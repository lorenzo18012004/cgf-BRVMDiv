"""
propose_rebalancing.py — Détection automatique de nouveau rebalancement ETFDividende
==============================================================================
Appelé mensuellement par GitHub Actions.
Compare brvm_composition_latest.json avec le dernier rebal dans rebal_detail.json.
Si une nouvelle composition existe → génère rebal_pending.json + envoie un email.

Utilise exactement le même moteur que rebalance_live.py (fonctions importées) :
  - Poids cible       : capitalisation totale Sika (nb_titres × prix)
  - Top FORCE_TOP_N   : OTC (poids exact indice, pas de contrainte ADV)
  - Autres            : ADV-cap sur le DELTA depuis la position courante
  - Exclusion         : si ADV < MIN_ADV_MFCFA ou poids résiduel < MIN_WEIGHT

Usage :
    python propose_rebalancing.py           # vérification normale
    python propose_rebalancing.py --force   # forcer même si déjà proposé
"""

import os, sys, json, smtplib, argparse
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base import BaseScript
from rebalance_live import (
    build_adv_capped_weights,
    compute_adv,
    compute_stale,
    get_total_cap_weights,
    FORCE_TOP_N,
    MIN_ADV_MFCFA,
    MIN_WEIGHT,
)


class RebalancingProposer(BaseScript):

    def __init__(self):
        super().__init__()
        self.recipients = ["l.philippe@cgfgestion.com", "philippee.pro@gmail.com"]

    # ── Turnover ──────────────────────────────────────────────────────────────── #

    def _compute_turnover(self, old_basket_w, new_weights):
        all_tickers = set(old_basket_w) | set(new_weights)
        tv = sum(abs(new_weights.get(tk, 0.0) - old_basket_w.get(tk, 0.0)) for tk in all_tickers)
        return round(tv / 2 * 100, 1)

    # ── Email ─────────────────────────────────────────────────────────────────── #

    def _send_email(self, proposal):
        gmail_user = os.environ.get("GMAIL_USER")
        gmail_pass = os.environ.get("GMAIL_APP_PASSWORD")
        if not gmail_user:
            secrets = self.load_json_path(os.path.join(self.root_dir, "secrets.json")) or {}
            gmail_user = secrets.get("smtp_user")
            gmail_pass = secrets.get("smtp_pass")
        if not gmail_user:
            print("[WARN] Pas de credentials email — notification ignorée.")
            return

        entries  = proposal.get("entries", [])
        exits    = proposal.get("exits", [])
        capped   = proposal.get("capped_tickers", [])
        excluded = proposal.get("excluded", {})
        rd       = proposal.get("proposed_rebal_date", "?")
        turnover = proposal.get("turnover_pct", "?")
        n_basket = len(proposal.get("new_basket", []))

        excl_lines = "\n".join(
            f"    {tk:8s} — {raison}" for tk, raison in excluded.items()
        ) or "    aucun"

        cap_lines = "\n".join(
            f"    {tk}" for tk in capped
        ) or "    aucun"

        body = (
            f"Bonjour,\n\n"
            f"Un nouveau rebalancement du ETFDividende ETF est proposé pour le {rd}.\n\n"
            f"CHANGEMENTS DE COMPOSITION :\n"
            f"  → Entrants ({len(entries)}) : {', '.join(entries) or 'aucun'}\n"
            f"  → Sortants ({len(exits)})   : {', '.join(exits) or 'aucun'}\n\n"
            f"STRATÉGIE ADV-CAP :\n"
            f"  → Panier ETF : {n_basket} titres\n"
            f"  → Top {FORCE_TOP_N} OTC (poids exact indice, pas de contrainte ADV)\n"
            f"  → Titres plafonnés sur le delta d'ordre ({len(capped)}) :\n{cap_lines}\n"
            f"  → Exclus (ADV < {MIN_ADV_MFCFA} MFCFA ou poids < {MIN_WEIGHT*100:.1f}%) ({len(excluded)}) :\n{excl_lines}\n\n"
            f"Turnover estimé : {turnover}%\n\n"
            f"PROCHAINE ÉTAPE :\n"
            f"GitHub → Actions → 'Appliquer Rebalancement' → Run workflow\n\n"
            f"Cordialement,\nCGF Bourse — Système automatique"
        )

        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        msg = MIMEMultipart()
        msg["From"]    = gmail_user
        msg["To"]      = ", ".join(self.recipients)
        msg["Subject"] = f"[CGF ETFDividende ETF] Rebalancement proposé — {rd}"
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, self.recipients, msg.as_string())
        print(f"[OK] Email envoyé à {', '.join(self.recipients)}")

    # ── Point d'entrée ────────────────────────────────────────────────────────── #

    def run(self, force=False):
        # Dernier rebal appliqué
        rd_data    = self.load_json("rebal_detail.json", {"rebalancings": []})
        rebals     = [r for r in rd_data.get("rebalancings", []) if not r.get("skipped") and r.get("basket")]
        last       = rebals[-1] if rebals else {}
        last_date  = last.get("date", "")
        old_basket = last.get("basket", [])

        # Position courante mark-to-market depuis nav_latest.json (mise à jour quotidienne)
        # Fallback sur rebal_detail si nav_latest n'a pas de basket
        nav_latest_pre = self.load_json("nav_latest.json", {})
        nav_basket = nav_latest_pre.get("basket", [])
        if nav_basket:
            old_basket_w = {b["ticker"]: b.get("poids_pct", 0.0) / 100 for b in nav_basket}
        else:
            old_basket_w = {b["ticker"]: b.get("w_etf", 0.0) for b in old_basket}

        # Nouvelle composition
        new_comp       = self.load_json("brvm_composition_latest.json", {})
        new_rebal_date = new_comp.get("rebal_date")

        if not new_rebal_date:
            print("[INFO] Pas de composition ETFDividende disponible — rien à faire.")
            return

        if not force and last_date and new_rebal_date <= last_date:
            print(f"[INFO] Composition {new_rebal_date} déjà appliquée (dernier rebal : {last_date}).")
            return

        pending = self.load_json("rebal_pending.json", {})
        if (not force
                and pending.get("status") == "pending"
                and pending.get("proposed_rebal_date") == new_rebal_date):
            print(f"[INFO] Proposition pour {new_rebal_date} déjà en attente.")
            return

        print(f"[INFO] Nouvelle composition ETFDividende détectée ({new_rebal_date}).")

        sika        = self.load_json("sika_history.json", {})
        soc         = self.load_json("sika_societe.json", {})
        new_tickers = new_comp.get("composition", [])
        entries     = new_comp.get("entries", [])
        exits       = new_comp.get("exits", [])

        nav_latest = nav_latest_pre
        aum_mfcfa  = float(nav_latest.get("aum_mfcfa") or 5000.0)

        # Poids capitalisation totale Sika (même fonction que rebalance_live.py)
        w_etfdividende = get_total_cap_weights(new_tickers, new_rebal_date, sika, soc)

        # ADV-cap avec position courante — même moteur que rebalance_live.py
        basket_weights, exclu_info, forced_tks = build_adv_capped_weights(
            w_etfdividende, new_rebal_date, aum_mfcfa, sika, old_basket=old_basket_w
        )

        # Titres plafonnés : dans le panier mais w_etf < w_etfdividende
        capped_tickers = sorted(
            tk for tk in basket_weights
            if tk not in forced_tks and basket_weights[tk] < w_etfdividende.get(tk, 0) - 1e-6
        )

        turnover = self._compute_turnover(old_basket_w, basket_weights)

        basket_detail = [
            {
                "ticker":      tk,
                "w_etf":       round(w, 6),
                "w_etfdividende":    round(w_etfdividende.get(tk, 0), 6),
                "force_otc":   tk in forced_tks,
                "capped":      tk in capped_tickers,
                "adv_mfcfa":   round(compute_adv(sika, tk, new_rebal_date), 1),
                "stale_ratio": round(compute_stale(sika, tk, new_rebal_date), 3),
            }
            for tk, w in sorted(basket_weights.items(), key=lambda x: -x[1])
        ]

        proposal = {
            "status":              "pending",
            "proposed_at":         datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "proposed_rebal_date": new_rebal_date,
            "last_rebal_date":     last_date,
            "entries":             entries,
            "exits":               exits,
            "turnover_pct":        turnover,
            "aum_mfcfa":           aum_mfcfa,
            "new_basket":          basket_detail,
            "capped_tickers":      capped_tickers,
            "excluded":            exclu_info,
            "current_basket":      [{"ticker": tk, "w_etf": w} for tk, w in old_basket_w.items()],
        }

        self.save_json("rebal_pending.json", proposal)

        sorted_by_brvm = sorted(w_etfdividende, key=lambda x: -w_etfdividende[x])
        print(f"[OK] Proposition sauvegardée dans rebal_pending.json")
        print(f"  Entrants : {entries}")
        print(f"  Sortants : {exits}")
        print(f"  Top {FORCE_TOP_N} OTC : {', '.join(sorted_by_brvm[:FORCE_TOP_N])}")
        print(f"  Panier ETF : {len(basket_detail)} titres")
        if capped_tickers:
            print(f"  Plafonnés ADV ({len(capped_tickers)}) : {', '.join(capped_tickers)}")
        if exclu_info:
            print(f"  Exclus ({len(exclu_info)}) :")
            for tk, raison in exclu_info.items():
                print(f"    {tk:8s} ({w_etfdividende.get(tk,0)*100:.2f}%) — {raison}")
        print(f"  Turnover estimé : {turnover}%")

        try:
            self._send_email(proposal)
        except Exception as e:
            print(f"[WARN] Email non envoyé : {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Forcer même si déjà proposé")
    args = parser.parse_args()
    RebalancingProposer().run(force=args.force)
