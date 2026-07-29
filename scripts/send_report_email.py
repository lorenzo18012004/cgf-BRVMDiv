"""
send_report_email.py — Envoi du rapport journalier PDF
=======================================================
- En local  : utilise Outlook COM (pas de mot de passe nécessaire)
- Cloud     : utilise Gmail SMTP via variables d'env GMAIL_USER + GMAIL_APP_PASSWORD

Usage : python send_report_email.py [--date YYYY-MM-DD]
"""
import os, sys, argparse, datetime, smtplib, json
from email.mime.multipart import MIMEMultipart
from email.mime.base      import MIMEBase
from email.mime.text      import MIMEText
from email                import encoders

from base import BaseScript


class ReportEmailSender(BaseScript):
    def __init__(self):
        super().__init__()
        self.RECIPIENTS = ["l.philippe@cgfgestion.com", "philippee.pro@gmail.com"]

    def _send_gmail(self, pdf_path, date_str, gmail_user, gmail_pass):
        recipients_str = ", ".join(self.RECIPIENTS)
        msg = MIMEMultipart()
        msg['From']    = gmail_user
        msg['To']      = recipients_str
        msg['Subject'] = f"CGF ETFDividende ETF — Rapport journalier {date_str}"

        body = (
            f"Bonjour,\n\n"
            f"Veuillez trouver ci-joint le rapport journalier du fonds CGF ETFDividende ETF "
            f"pour la séance du {date_str}.\n\n"
            f"Cordialement,\n"
            f"CGF Bourse — Système automatique"
        )
        msg.attach(MIMEText(body, 'plain'))

        with open(pdf_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(pdf_path)}"')
        msg.attach(part)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, self.RECIPIENTS, msg.as_string())

        print(f"[OK] Email envoyé via Gmail à {recipients_str}")
        return True

    def _send_outlook(self, pdf_path, date_str):
        import win32com.client
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail    = outlook.CreateItem(0)
        mail.To      = "; ".join(self.RECIPIENTS)
        mail.Subject = f"CGF ETFDividende ETF — Rapport journalier {date_str}"
        mail.Body    = (
            f"Bonjour,\n\n"
            f"Veuillez trouver ci-joint le rapport journalier du fonds CGF ETFDividende ETF "
            f"pour la séance du {date_str}.\n\n"
            f"Cordialement,\n"
            f"CGF Bourse — Système automatique"
        )
        mail.Attachments.Add(pdf_path)
        mail.Send()
        print(f"[OK] Email envoyé via Outlook à {'; '.join(self.RECIPIENTS)}")
        return True

    def _load_secrets(self):
        path = os.path.join(self.root_dir, "secrets.json")
        if os.path.exists(path):
            try:
                return json.load(open(path, encoding="utf-8"))
            except Exception:
                pass
        return {}

    def send(self, date_str = None):
        if date_str is None:
            date_str = datetime.date.today().strftime("%Y-%m-%d")

        year_month = date_str[:7]   # "2026-07"
        year       = date_str[:4]   # "2026"
        pdf_path = os.path.join(self.data_dir, "pdfs", "journalier", year, year_month,
                                f"rapport_journalier_{date_str}.pdf")
        if not os.path.exists(pdf_path):
            print(f"[ERREUR] PDF introuvable : {pdf_path}")
            return False

        try:
            secrets    = self._load_secrets()
            gmail_user = os.environ.get('GMAIL_USER') or secrets.get('smtp_user')
            gmail_pass = os.environ.get('GMAIL_APP_PASSWORD') or secrets.get('smtp_password')
            if gmail_user and gmail_pass and gmail_pass != "REMPLACER_PAR_APP_PASSWORD":
                return self._send_gmail(pdf_path, date_str, gmail_user, gmail_pass)
            else:
                return self._send_outlook(pdf_path, date_str)
        except Exception as e:
            print(f"[ERREUR] Envoi email échoué : {e}")
            return False

    def run(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--date", default=None)
        args = parser.parse_args()
        ok = self.send(args.date)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    ReportEmailSender().run()
