"""
send_alert.py -- Alertes email apres pipeline quotidien
=======================================================
Lit nav_latest.json, verifie les seuils definis dans alert_config.json,
envoie un email si un seuil est depasse.

Usage :
    python send_alert.py                  # verifie et envoie si besoin
    python send_alert.py --test           # envoie un email de test
    python send_alert.py --force          # envoie meme si aucun seuil depasse
"""
import sys, os, json, smtplib, argparse, warnings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

warnings.filterwarnings("ignore")

from base import BaseScript


class AlertSender(BaseScript):
    def __init__(self):
        super().__init__()
        self.CONFIG_PATH = os.path.join(self.data_dir, "alert_config.json")
        self.NAV_PATH    = os.path.join(self.data_dir, "nav_latest.json")

    def _load(self, path):
        if not os.path.exists(path):
            return {}
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _send_email(self, cfg, subject, body_html):
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = cfg["smtp_user"]
            msg["To"]      = ", ".join(cfg["recipients"])
            msg.attach(MIMEText(body_html, "html", "utf-8"))

            with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"]) as s:
                s.ehlo()
                s.starttls()
                s.login(cfg["smtp_user"], cfg["smtp_password"])
                s.sendmail(cfg["smtp_user"], cfg["recipients"], msg.as_string())
            return True
        except Exception as e:
            print(f"[ERREUR] Email non envoye : {e}")
            return False

    def check_and_alert(self, force = False, test = False):
        cfg = self._load(self.CONFIG_PATH)
        if not cfg:
            print("[WARN] alert_config.json introuvable -- alertes desactivees.")
            return []
        if os.environ.get("GMAIL_USER"):
            cfg["smtp_user"] = os.environ["GMAIL_USER"]
        if os.environ.get("GMAIL_APP_PASSWORD"):
            cfg["smtp_password"] = os.environ["GMAIL_APP_PASSWORD"]
        secrets_path = os.path.join(self.scripts_dir, "secrets.json")
        if os.path.exists(secrets_path):
            try:
                secrets = json.load(open(secrets_path, encoding="utf-8"))
                if secrets.get("smtp_password"):
                    cfg["smtp_password"] = secrets["smtp_password"]
                if secrets.get("smtp_user"):
                    cfg["smtp_user"] = secrets["smtp_user"]
            except Exception:
                pass
        if not cfg.get("enabled") and not force and not test:
            print("[INFO] Alertes desactivees (enabled: false dans alert_config.json).")
            return []
        if cfg.get("smtp_password") in (None, "", "REMPLACER_PAR_APP_PASSWORD"):
            print("[WARN] smtp_password non configure -- alertes email desactivees.")
            return []

        nl     = self._load(self.NAV_PATH)
        thr    = cfg.get("thresholds", {})
        alerts = []
        ts     = datetime.now().strftime("%d/%m/%Y %H:%M")

        if test:
            alerts.append(("TEST", "Ceci est un email de test du systeme d alerte CGF ETFDividende ETF."))
        else:
            change_1d = nl.get("change_1d_pct")
            age       = nl.get("data_age_biz_days", 0)
            te_live   = nl.get("tracking_error_live")
            td_live   = nl.get("tracking_diff_live")

            if change_1d is not None and abs(change_1d) >= thr.get("vl_change_1d_pct", 3.0):
                sign = "hausse" if change_1d > 0 else "baisse"
                alerts.append((f"VL variation extreme (+/- {thr.get('vl_change_1d_pct')}%)",
                                f"Variation du jour : <b>{change_1d:+.3f}%</b> ({sign})"))

            if age and age >= thr.get("data_age_biz_days", 2):
                alerts.append(("Donnees obsoletes",
                                f"Les donnees ont <b>{age} jours ouvrables</b> de retard."))

            if te_live and te_live >= thr.get("tracking_error_pct", 2.0):
                alerts.append(("Tracking Error elevee",
                                f"TE annualisee : <b>{te_live:.2f}%</b> (seuil : {thr.get('tracking_error_pct')}%)"))

            if td_live is not None and abs(td_live) >= thr.get("tracking_diff_pct", 0.5):
                alerts.append(("Tracking Difference",
                                f"TD : <b>{td_live:+.3f}%</b> (seuil : {thr.get('tracking_diff_pct')}%)"))

        if not alerts and not force:
            print(f"[OK] {ts} — Aucun seuil depasse, aucune alerte envoyee.")
            return []

        rows = "".join(
            f"<tr><td style='padding:8px 12px;font-weight:600;color:#dc2626'>{a[0]}</td>"
            f"<td style='padding:8px 12px'>{a[1]}</td></tr>"
            for a in alerts
        )
        calc_date = nl.get("calc_date", "—")
        nav_val   = nl.get("nav_indice", "—")
        vl_val    = nl.get("vl_par_part_fcfa", "—")

        body = f"""
<html><body style="font-family:Arial,sans-serif;color:#1e293b;max-width:600px">
<h2 style="color:#dc2626">⚠ Alerte CGF ETFDividende ETF — {ts}</h2>
<table style="border-collapse:collapse;width:100%;margin-bottom:16px">
  <tr style="background:#f1f5f9"><th style="padding:8px 12px;text-align:left">Alerte</th><th style="padding:8px 12px;text-align:left">Detail</th></tr>
  {rows}
</table>
<hr>
<p><b>NAV indice :</b> {nav_val} &nbsp;|&nbsp; <b>VL / part :</b> {f"{int(vl_val):,}" if isinstance(vl_val,(int,float)) else vl_val} FCFA &nbsp;|&nbsp; <b>Date :</b> {calc_date}</p>
<p style="color:#64748b;font-size:12px">Alerte automatique generee par le pipeline CGF ETFDividende ETF.</p>
</body></html>"""

        subject = f"[CGF ETFDividende ETF] {len(alerts)} alerte(s) — {ts}"
        ok = self._send_email(cfg, subject, body)
        if ok:
            print(f"[OK] Email envoye ({len(alerts)} alerte(s)) → {', '.join(cfg['recipients'])}")
        return alerts

    def run(self):
        parser = argparse.ArgumentParser(description="Alertes email CGF ETFDividende ETF")
        parser.add_argument("--test",  action="store_true", help="Envoyer un email de test")
        parser.add_argument("--force", action="store_true", help="Envoyer meme si pas d alerte")
        args = parser.parse_args()
        self.check_and_alert(force=args.force, test=args.test)


if __name__ == "__main__":
    AlertSender().run()
