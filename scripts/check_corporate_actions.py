"""
check_corporate_actions.py — Détection des actions corporatives BRVM
=====================================================================
Tourne à 9h00 UTC (avant ouverture marché) via GitHub Actions.

Détecte :
1. Anomalies de prix vs clôture de la veille (dividendes, splits non annoncés)
2. Événements connus dans dividend_calendar.json (rappel proactif)
3. Provisionnement comptable automatique à l'ex-date (Dividend_Receivable /
   Distribution_Payable) selon la méthode Dividend Settlement Gap.

Envoie un email d'alerte si quelque chose est détecté.
"""
import os, sys, smtplib, json
from datetime import date, timedelta, datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from base import BaseScript


class CorporateActionsChecker(BaseScript):
    def __init__(self):
        super().__init__()
        self.THRESHOLD_DIV   = 0.04
        self.THRESHOLD_SPLIT = 0.10
        self.CALENDAR_DAYS   = 5
        self.RECIPIENTS      = ["l.philippe@cgfgestion.com", "philippee.pro@gmail.com"]
        self.SIKA_HIST    = os.path.join(self.data_dir, "sika_history.json")
        self.NAV_LATEST   = os.path.join(self.data_dir, "nav_latest.json")
        self.DIV_CALENDAR = os.path.join(self.data_dir, "dividend_calendar.json")

    def _get_prev_close(self, sika_hist, ticker, today_str):
        hist = sika_hist.get(ticker, {})
        dates = sorted(d for d in hist if d < today_str)
        if not dates:
            return None
        return hist[dates[-1]].get("close")

    def _get_etf_weights(self, nav_latest):
        basket = (nav_latest or {}).get("basket", [])
        return {it["ticker"]: it["poids_pct"] for it in basket}

    def _scrape_live_prices(self):
        try:
            sys.path.insert(0, self.scripts_dir)
            from scrape_sika import _fetch_html, scrape_prices, SIKA_URL
            html = _fetch_html(SIKA_URL)
            prices = scrape_prices(html)
            return {tk: float(prices[tk]) for tk in prices.index}
        except Exception as e:
            print(f"[ERREUR] Scraping live : {e}")
            return {}

    def _check_calendar(self, today_str):
        cal = self.load_json_path(self.DIV_CALENDAR) or {}
        events = cal.get("events", [])
        today  = date.fromisoformat(today_str)
        upcoming = []
        for ev in events:
            try:
                ex = date.fromisoformat(ev["ex_date"])
                delta = (ex - today).days
                if 0 <= delta <= self.CALENDAR_DAYS:
                    ev["_days_away"] = delta
                    upcoming.append(ev)
            except Exception:
                pass
        return sorted(upcoming, key=lambda x: x["_days_away"])

    def _send_alert(self, subject, body_html, gmail_user, gmail_pass):
        msg = MIMEMultipart("alternative")
        msg["From"]    = gmail_user
        msg["To"]      = ", ".join(self.RECIPIENTS)
        msg["Subject"] = subject
        msg.attach(MIMEText(body_html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
            srv.login(gmail_user, gmail_pass)
            srv.sendmail(gmail_user, self.RECIPIENTS, msg.as_string())
        print(f"[OK] Alerte envoyée à {', '.join(self.RECIPIENTS)}")

    # ── Dividend Settlement Gap ───────────────────────────────────────────── #

    def _provision_dividends(self, today_str, nav_latest):
        """
        À l'ex-date : inscrit Dividend_Receivable (actif) et Distribution_Payable
        (passif) pour un montant identique, neutralisant l'impact cash sur la NAV
        tout en la faisant baisser en synchronisation avec l'indice Price Return.
        """
        ACCT_PATH = os.path.join(self.data_dir, "dividend_accounting.json")
        DIV_PATH  = os.path.join(self.data_dir, "sika_dividendes.json")
        LOG_PATH  = os.path.join(self.data_dir, "dividend_log.json")

        if not os.path.exists(DIV_PATH):
            return []

        sika_div   = json.load(open(DIV_PATH, encoding="utf-8"))
        basket     = nav_latest.get("basket", [])
        aum_mfcfa  = float(nav_latest.get("aum_mfcfa") or 0)
        n_parts    = int(nav_latest.get("n_parts") or 50000)

        # Construire index basket : ticker → {poids_pct, dernier_prix}
        basket_idx = {b["ticker"]: b for b in basket}

        # Événements ex-date = aujourd'hui dans sika_dividendes
        today_events = [
            d for d in sika_div.get("dividendes", [])
            if d.get("date_detach") == today_str and d.get("ticker")
        ]

        if not today_events:
            return []

        # Charger le grand livre comptable
        if os.path.exists(ACCT_PATH):
            acct = json.load(open(ACCT_PATH, encoding="utf-8"))
        else:
            acct = {
                "updated_at": today_str,
                "dividend_receivable_fcfa": 0.0,
                "distribution_payable_fcfa": 0.0,
                "poche_distribution_fcfa": 0.0,
                "evenements": [],
            }

        # Lire date de distribution depuis dividend_log.json
        distrib_date = "N/A"
        if os.path.exists(LOG_PATH):
            try:
                distrib_date = json.load(open(LOG_PATH, encoding="utf-8")).get(
                    "distribution_date", "N/A"
                )
            except Exception:
                pass

        provisioned = []
        existing_ids = {e["id"] for e in acct.get("evenements", [])}

        for ev in today_events:
            ticker  = ev["ticker"]
            ev_id   = f"{ticker}_{today_str}"
            if ev_id in existing_ids:
                continue  # déjà provisionné

            montant_par_action = float(ev.get("montant") or 0)
            if montant_par_action <= 0:
                continue

            b = basket_idx.get(ticker)
            if not b:
                print(f"  [DIV] {ticker} ex-div aujourd'hui mais absent du panier ETF — ignoré.")
                continue

            poids_pct    = float(b.get("poids_pct") or 0) / 100.0
            dernier_prix = float(b.get("dernier_prix") or 0)
            if dernier_prix <= 0 or aum_mfcfa <= 0:
                continue

            # Nombre de titres détenus (estimation à partir des poids)
            nb_titres        = poids_pct * aum_mfcfa * 1_000_000 / dernier_prix
            montant_total    = nb_titres * montant_par_action
            montant_par_part = montant_total / n_parts if n_parts > 0 else 0.0

            entry = {
                "id":                    ev_id,
                "ticker":                ticker,
                "nom":                   ev.get("nom_sika", ticker),
                "ex_date":               today_str,
                "montant_par_action_fcfa": round(montant_par_action, 2),
                "nb_titres_etf":         round(nb_titres, 0),
                "montant_total_fcfa":    round(montant_total, 0),
                "montant_par_part_fcfa": round(montant_par_part, 4),
                "payment_date":          None,
                "distribution_date":     distrib_date,
                "status":                "accrued",
                "journal": [
                    {
                        "date":    today_str,
                        "type":    "ACCRUAL",
                        "debit":   "Dividend_Receivable",
                        "credit":  "Distribution_Payable",
                        "montant_fcfa": round(montant_total, 0),
                        "note":    f"Provisionnement ex-date {ticker} — {montant_par_action:.2f} FCFA/action",
                    }
                ],
            }

            acct["evenements"].append(entry)
            acct["dividend_receivable_fcfa"]  = round(
                acct.get("dividend_receivable_fcfa", 0) + montant_total, 0)
            acct["distribution_payable_fcfa"] = round(
                acct.get("distribution_payable_fcfa", 0) + montant_total, 0)

            provisioned.append(entry)
            print(f"  [DIV] ACCRUAL {ticker} : {montant_total:,.0f} FCFA "
                  f"({montant_par_part:.4f} FCFA/part)")

        if provisioned:
            acct["updated_at"] = datetime.now(timezone.utc).isoformat()
            json.dump(acct, open(ACCT_PATH, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)
            print(f"  [DIV] {len(provisioned)} événement(s) provisionné(s) → dividend_accounting.json")

        return provisioned

    def record_payment_received(self, ticker, ex_date, payment_date=None):
        """
        À appeler manuellement (ou via dashboard) quand le cash est physiquement
        reçu : solde Dividend_Receivable et route vers Poche Distribution.
        """
        ACCT_PATH = os.path.join(self.data_dir, "dividend_accounting.json")
        if not os.path.exists(ACCT_PATH):
            print("[WARN] dividend_accounting.json introuvable.")
            return

        acct    = json.load(open(ACCT_PATH, encoding="utf-8"))
        ev_id   = f"{ticker}_{ex_date}"
        payment_date = payment_date or date.today().isoformat()

        for ev in acct.get("evenements", []):
            if ev["id"] == ev_id and ev["status"] == "accrued":
                montant = ev["montant_total_fcfa"]
                ev["payment_date"] = payment_date
                ev["status"]       = "received"
                ev["journal"].append({
                    "date":         payment_date,
                    "type":         "PAYMENT",
                    "debit":        "Tresorerie_Depositaire_Poche_Distribution",
                    "credit":       "Dividend_Receivable",
                    "montant_fcfa": montant,
                    "note":         f"Encaissement dividende {ticker} — routé Poche Distribution (sans transit NAV)",
                })
                acct["dividend_receivable_fcfa"]  = round(
                    acct.get("dividend_receivable_fcfa", 0) - montant, 0)
                acct["poche_distribution_fcfa"]   = round(
                    acct.get("poche_distribution_fcfa", 0) + montant, 0)
                acct["updated_at"] = datetime.now(timezone.utc).isoformat()
                json.dump(acct, open(ACCT_PATH, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
                print(f"[DIV] PAYMENT {ticker} : {montant:,.0f} FCFA → Poche Distribution")
                return

        print(f"[WARN] Événement {ev_id} introuvable ou déjà traité.")

    def _auto_record_payments(self, today_str):
        """
        Vérifie chaque jour si un dividende provisionné doit être encaissé.
        Se déclenche quand date_paiement == today dans sika_dividendes.json.
        """
        DIV_PATH  = os.path.join(self.data_dir, "sika_dividendes.json")
        ACCT_PATH = os.path.join(self.data_dir, "dividend_accounting.json")

        if not os.path.exists(DIV_PATH) or not os.path.exists(ACCT_PATH):
            return []

        sika_div = json.load(open(DIV_PATH, encoding="utf-8"))
        acct     = json.load(open(ACCT_PATH, encoding="utf-8"))

        # Événements dont date_paiement = aujourd'hui et statut = accrued
        accrued_ids = {
            ev["id"]: ev
            for ev in acct.get("evenements", [])
            if ev.get("status") == "accrued"
        }

        recorded = []
        for d in sika_div.get("dividendes", []):
            if d.get("date_paiement") != today_str:
                continue
            ticker   = d.get("ticker")
            ex_date  = d.get("date_detach")
            if not ticker or not ex_date:
                continue
            ev_id = f"{ticker}_{ex_date}"
            if ev_id not in accrued_ids:
                continue

            # Enregistrer le paiement
            ev      = accrued_ids[ev_id]
            montant = ev["montant_total_fcfa"]
            ev["payment_date"] = today_str
            ev["status"]       = "received"
            ev["journal"].append({
                "date":         today_str,
                "type":         "PAYMENT",
                "debit":        "Tresorerie_Depositaire_Poche_Distribution",
                "credit":       "Dividend_Receivable",
                "montant_fcfa": montant,
                "note":         f"Encaissement automatique {ticker} — Poche Distribution",
            })
            acct["dividend_receivable_fcfa"] = round(
                acct.get("dividend_receivable_fcfa", 0) - montant, 0)
            acct["poche_distribution_fcfa"]  = round(
                acct.get("poche_distribution_fcfa", 0) + montant, 0)
            recorded.append(ticker)
            print(f"  [DIV] AUTO-PAYMENT {ticker} : {montant:,.0f} FCFA → Poche Distribution")

        if recorded:
            acct["updated_at"] = datetime.now(timezone.utc).isoformat()
            json.dump(acct, open(ACCT_PATH, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)

        return recorded

    def record_distribution(self, distribution_date=None):
        """
        À la date de distribution : solde Distribution_Payable et vide la Poche.
        """
        ACCT_PATH = os.path.join(self.data_dir, "dividend_accounting.json")
        if not os.path.exists(ACCT_PATH):
            return

        acct   = json.load(open(ACCT_PATH, encoding="utf-8"))
        distrib_date = distribution_date or date.today().isoformat()
        total  = 0.0

        for ev in acct.get("evenements", []):
            if ev["status"] == "received":
                montant = ev["montant_total_fcfa"]
                ev["status"] = "distributed"
                ev["journal"].append({
                    "date":         distrib_date,
                    "type":         "DISTRIBUTION",
                    "debit":        "Distribution_Payable",
                    "credit":       "Tresorerie_Depositaire_Poche_Distribution",
                    "montant_fcfa": montant,
                    "note":         f"Distribution aux porteurs — {ev['ticker']}",
                })
                total += montant

        acct["distribution_payable_fcfa"] = round(
            max(0, acct.get("distribution_payable_fcfa", 0) - total), 0)
        acct["poche_distribution_fcfa"]   = round(
            max(0, acct.get("poche_distribution_fcfa", 0) - total), 0)
        acct["updated_at"] = datetime.now(timezone.utc).isoformat()
        json.dump(acct, open(ACCT_PATH, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print(f"[DIV] DISTRIBUTION : {total:,.0f} FCFA distribués aux porteurs.")

    # ── Point d'entrée ────────────────────────────────────────────────────── #

    def run(self):
        today_str  = date.today().isoformat()
        sika_hist  = self.load_json_path(self.SIKA_HIST) or {}
        nav_latest = self.load_json_path(self.NAV_LATEST) or {}
        etf_weights = self._get_etf_weights(nav_latest)

        # Provisionnement comptable dividendes à l'ex-date (DSG)
        provisioned = self._provision_dividends(today_str, nav_latest)
        # Encaissement automatique si date_paiement = aujourd'hui
        self._auto_record_payments(today_str)

        live_prices = self._scrape_live_prices()
        anomalies = []

        all_tickers = set(etf_weights.keys()) | set(sika_hist.keys())
        for tk in sorted(all_tickers):
            prev_close = self._get_prev_close(sika_hist, tk, today_str)
            live       = live_prices.get(tk)
            if not prev_close or not live or prev_close <= 0:
                continue
            chg = (live - prev_close) / prev_close

            severity = None
            if abs(chg) >= self.THRESHOLD_SPLIT:
                severity = "CRITIQUE"
            elif chg <= -self.THRESHOLD_DIV:
                severity = "ATTENTION"

            if severity:
                w_etf = etf_weights.get(tk, 0)
                impact_inav = round(w_etf / 100 * chg * 100, 3)
                anomalies.append({
                    "ticker":      tk,
                    "prev_close":  prev_close,
                    "live":        live,
                    "chg_pct":     round(chg * 100, 2),
                    "w_etf_pct":   round(w_etf, 2),
                    "impact_inav": impact_inav,
                    "severity":    severity,
                })

        anomalies.sort(key=lambda x: abs(x["chg_pct"]), reverse=True)

        calendar_alerts = self._check_calendar(today_str)

        if not anomalies and not calendar_alerts:
            print(f"[{today_str}] Aucune action corporative détectée.")
            return

        secrets    = self.load_json_path(os.path.join(self.root_dir, "secrets.json")) or {}
        gmail_user = os.environ.get("GMAIL_USER") or secrets.get("smtp_user")
        gmail_pass = os.environ.get("GMAIL_APP_PASSWORD") or secrets.get("smtp_password")
        if not gmail_user or not gmail_pass:
            print("[WARN] Pas de credentials Gmail — affichage console uniquement.")
            for a in anomalies:
                print(f"  [{a['severity']}] {a['ticker']} : {a['chg_pct']:+.2f}% "
                      f"(prev={a['prev_close']} → live={a['live']}) "
                      f"poids ETF={a['w_etf_pct']}% impact iNAV={a['impact_inav']:+.3f}%")
            for ev in calendar_alerts:
                print(f"  [CALENDRIER J+{ev['_days_away']}] {ev['ticker']} — {ev['type']} "
                      f"ex-date {ev['ex_date']}")
            return

        rows_anomalies = ""
        for a in anomalies:
            color  = "#c0392b" if a["severity"] == "CRITIQUE" else "#e67e22"
            bg     = "#fdf2f2" if a["severity"] == "CRITIQUE" else "#fef9f0"
            rows_anomalies += f"""
        <tr style="background:{bg}">
          <td style="padding:8px 12px;font-weight:700;color:{color}">{a['severity']}</td>
          <td style="padding:8px 12px;font-weight:700">{a['ticker']}</td>
          <td style="padding:8px 12px">{a['prev_close']:,.0f} FCFA</td>
          <td style="padding:8px 12px">{a['live']:,.0f} FCFA</td>
          <td style="padding:8px 12px;font-weight:700;color:{color}">{a['chg_pct']:+.2f}%</td>
          <td style="padding:8px 12px">{a['w_etf_pct']:.2f}%</td>
          <td style="padding:8px 12px;font-weight:700;color:{color}">{a['impact_inav']:+.3f}%</td>
        </tr>"""

        rows_calendar = ""
        for ev in calendar_alerts:
            j = ev["_days_away"]
            label = "AUJOURD'HUI" if j == 0 else f"J+{j}"
            detail = ""
            if ev.get("amount_fcfa"):
                detail = f"Dividende : {ev['amount_fcfa']} FCFA/action"
            elif ev.get("split_ratio"):
                detail = f"Split {ev['split_ratio']}-pour-1"
            elif ev.get("note"):
                detail = ev["note"]
            rows_calendar += f"""
        <tr>
          <td style="padding:8px 12px;font-weight:700;color:#2980b9">{label}</td>
          <td style="padding:8px 12px;font-weight:700">{ev['ticker']}</td>
          <td style="padding:8px 12px">{ev['type'].upper()}</td>
          <td style="padding:8px 12px">{ev['ex_date']}</td>
          <td style="padding:8px 12px">{detail}</td>
        </tr>"""

        section_anomalies = ""
        if anomalies:
            section_anomalies = f"""
        <h3 style="color:#c0392b;margin-top:24px">⚠ Anomalies de prix détectées</h3>
        <p style="color:#666;font-size:13px">
          Prix au scraping de 9h00 UTC vs clôture officielle de la veille.<br>
          Vérifier si un dividende ou un split a été détaché ce matin.
        </p>
        <table style="border-collapse:collapse;width:100%;font-size:13px">
          <thead>
            <tr style="background:#f3f4f6;color:#374151">
              <th style="padding:8px 12px;text-align:left">Niveau</th>
              <th style="padding:8px 12px;text-align:left">Ticker</th>
              <th style="padding:8px 12px;text-align:left">Clôture J-1</th>
              <th style="padding:8px 12px;text-align:left">Prix 9h00</th>
              <th style="padding:8px 12px;text-align:left">Variation</th>
              <th style="padding:8px 12px;text-align:left">Poids ETF</th>
              <th style="padding:8px 12px;text-align:left">Impact iNAV</th>
            </tr>
          </thead>
          <tbody>{rows_anomalies}</tbody>
        </table>"""

        section_calendar = ""
        if calendar_alerts:
            section_calendar = f"""
        <h3 style="color:#2980b9;margin-top:24px">📅 Événements du calendrier</h3>
        <table style="border-collapse:collapse;width:100%;font-size:13px">
          <thead>
            <tr style="background:#f3f4f6;color:#374151">
              <th style="padding:8px 12px;text-align:left">Échéance</th>
              <th style="padding:8px 12px;text-align:left">Ticker</th>
              <th style="padding:8px 12px;text-align:left">Type</th>
              <th style="padding:8px 12px;text-align:left">Ex-date</th>
              <th style="padding:8px 12px;text-align:left">Détail</th>
            </tr>
          </thead>
          <tbody>{rows_calendar}</tbody>
        </table>"""

        body_html = f"""
    <html><body style="font-family:Inter,sans-serif;color:#0c1a2e;max-width:800px;margin:0 auto;padding:24px">
      <h2 style="color:#0c1a2e;border-bottom:2px solid #b8973f;padding-bottom:8px">
        CGF BRVMC ETF — Alerte Actions Corporatives {today_str}
      </h2>
      {section_anomalies}
      {section_calendar}
      <p style="margin-top:24px;font-size:12px;color:#9ca3af">
        Message automatique généré à 9h00 UTC — CGF Bourse Système
      </p>
    </body></html>"""

        subject = f"[ALERTE] CGF ETF — Actions corporatives {today_str}"
        if anomalies:
            n_crit = sum(1 for a in anomalies if a["severity"] == "CRITIQUE")
            subject = f"[{'CRITIQUE' if n_crit else 'ATTENTION'}] CGF ETF — {len(anomalies)} anomalie(s) de prix {today_str}"

        self._send_alert(subject, body_html, gmail_user, gmail_pass)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-payment", nargs=2, metavar=("TICKER", "EX_DATE"),
                        help="Enregistrer la réception du cash dividende pour TICKER à EX_DATE")
    parser.add_argument("--distribute", action="store_true",
                        help="Enregistrer la distribution aux porteurs")
    args = parser.parse_args()

    checker = CorporateActionsChecker()
    if args.record_payment:
        checker.record_payment_received(args.record_payment[0], args.record_payment[1])
    elif args.distribute:
        checker.record_distribution()
    else:
        checker.run()
