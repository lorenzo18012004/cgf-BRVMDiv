"""
track_inav_failure.py — Suivi des échecs consécutifs du calcul iNAV
====================================================================
Appelé depuis le workflow intraday.yml après chaque tentative de calcul.

Usage :
    python scripts/track_inav_failure.py success   # réinitialise le compteur
    python scripts/track_inav_failure.py failure   # incrémente et alerte si >= 3
"""
import json, os, sys, smtplib, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

BASE       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COUNTER    = os.path.join(BASE, "data", "intraday_failure_count.json")
RECIPIENTS = ["l.philippe@cgfgestion.com", "philippee.pro@gmail.com"]
MAX_FAILS  = 3


def _send_alert(n: int, gmail_user: str, gmail_pass: str):
    ts  = datetime.datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "[ALERTE] iNAV ETF Dividende — 3 échecs consécutifs"
    msg["From"]    = gmail_user
    msg["To"]      = ", ".join(RECIPIENTS)
    body = f"""<html><body style="font-family:Arial,sans-serif;color:#1e293b;max-width:600px">
<h2 style="color:#dc2626">&#9888; iNAV ETF Dividende — Panne détectée</h2>
<p>Le calcul de l'iNAV a échoué <b>{n} fois de suite</b>.<br>
Dernier échec : <b>{ts}</b></p>
<p>Vérifier le workflow GitHub Actions.</p>
<p style="color:#64748b;font-size:12px">Alerte automatique — CGF Bourse Système</p>
</body></html>"""
    msg.attach(MIMEText(body, "html", "utf-8"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.ehlo(); s.starttls()
            s.login(gmail_user, gmail_pass)
            s.sendmail(gmail_user, RECIPIENTS, msg.as_string())
        print(f"[ALERTE] Email envoyé — {n} échecs consécutifs")
    except Exception as e:
        print(f"[ERREUR] Email non envoyé : {e}")


def main():
    outcome = sys.argv[1] if len(sys.argv) > 1 else "success"

    data = json.load(open(COUNTER)) if os.path.exists(COUNTER) else {"count": 0}

    if outcome == "success":
        data["count"] = 0
    else:
        data["count"] = data.get("count", 0) + 1
        print(f"[iNAV] Échec #{data['count']}")
        if data["count"] >= MAX_FAILS:
            gmail_user = os.environ.get("GMAIL_USER", "")
            gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "")
            if gmail_user and gmail_pass:
                _send_alert(data["count"], gmail_user, gmail_pass)
            else:
                print(f"[ALERTE] {data['count']} échecs consécutifs — credentials Gmail absents")
            data["count"] = 0

    with open(COUNTER, "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    main()
