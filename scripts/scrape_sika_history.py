"""
scrape_sika_history.py — Historique complet BRVM depuis Sika Finance
=====================================================================
Scrape l'API /api/general/GetHistos par chunks de 90j depuis 2005.

Usage:
  python scrape_sika_history.py              # mise à jour (nouvelles données seulement)
  python scrape_sika_history.py --full       # re-scrape tout depuis 2005
  python scrape_sika_history.py --ticker SNTS  # un seul ticker
  python scrape_sika_history.py --since 2024-01-01  # depuis une date précise
"""
import sys, io, os, json, time, argparse, warnings
from datetime import date, timedelta
warnings.filterwarnings('ignore')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests

from base import BaseScript


class SikaHistoryScraper(BaseScript):

    def __init__(self):
        super().__init__()
        self.api_url    = 'https://www.sikafinance.com/api/general/GetHistos'
        self.start_date = date(2005, 1, 1)
        self.out_file   = os.path.join(self.data_dir, 'sika_history.json')
        self.headers    = {
            'User-Agent':       'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type':     'application/json;charset=UTF-8',
            'Accept':           'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin':           'https://www.sikafinance.com',
            'Referer':          'https://www.sikafinance.com/marches/historiques/',
        }
        self.country_map = {
            'ABJC': 'ci', 'BICB': 'bj', 'BICC': 'ci', 'BNBC': 'ci',
            'BOAB': 'bj', 'BOABF': 'bf', 'BOAC': 'ci', 'BOAM': 'ml',
            'BOAN': 'ne', 'BOAS': 'sn', 'CABC': 'ci', 'CBIBF': 'bf',
            'CFAC': 'ci', 'CIEC': 'ci', 'ECOC': 'ci', 'ETIT': 'tg',
            'FTSC': 'ci', 'LNBB': 'bj', 'NEIC': 'ci', 'NSBC': 'ci',
            'NTLC': 'ci', 'ONTBF': 'bf', 'ORAC': 'ci', 'ORGT': 'tg',
            'PALC': 'ci', 'PRSC': 'ci', 'SAFC': 'ci', 'SCRC': 'ci',
            'SDCC': 'ci', 'SDSC': 'ci', 'SEMC': 'ci', 'SGBC': 'ci',
            'SHEC': 'ci', 'SIBC': 'ci', 'SICC': 'ci', 'SIVC': 'ci',
            'SLBC': 'ci', 'SMBC': 'ci', 'SNTS': 'sn', 'SOGC': 'ci',
            'SPHC': 'ci', 'STAC': 'ci', 'STBC': 'ci', 'TTLC': 'ci',
            'TTLS': 'sn', 'UNLC': 'ci', 'UNXC': 'ci',
        }

    def _fetch_chunk(self, ticker_full, d_from, d_to,
                     retries: int = 3):
        """Appel API pour un chunk de max 90j. Retourne une liste de dicts."""
        payload = {
            'ticker':  ticker_full,
            'datedeb': d_from.strftime('%d/%m/%Y'),
            'datefin': d_to.strftime('%d/%m/%Y'),
            'xperiod': 0,
        }
        for attempt in range(retries):
            try:
                r = requests.post(self.api_url, headers=self.headers, json=payload,
                                  verify=False, timeout=20)
                if r.status_code != 200:
                    time.sleep(2)
                    continue
                resp = r.json()
                err  = resp.get('error', '')
                if err == 'toolong':
                    return []
                if err in ('baddt', 'nodata'):
                    return []
                lst = resp.get('lst', [])
                return lst if isinstance(lst, list) else []
            except Exception:
                time.sleep(2)
        return []

    def _chunks(self, start, end, days = 88):
        """Génère des tuples (debut, fin) par tranches de `days` jours."""
        cur = start
        while cur <= end:
            yield cur, min(cur + timedelta(days=days), end)
            cur += timedelta(days=days + 1)

    def scrape_ticker(self, ticker, since = None,
                      delay: float = 0.4):
        """
        Scrape tout l'historique d'un ticker depuis `since` (ou self.start_date).
        Retourne un dict {date_iso: {close, volume, open, high, low}}.
        """
        pays = self.country_map.get(ticker)
        if pays is None:
            print(f"  {ticker}: pays inconnu, ignoré")
            return {}

        ticker_full = f'{ticker}.{pays}'
        start = since or self.start_date
        today = date.today()
        result: dict = {}

        for d_from, d_to in self._chunks(start, today):
            rows = self._fetch_chunk(ticker_full, d_from, d_to)
            for row in rows:
                raw_date = row.get('Date', '')
                parts = raw_date.split('/')
                if len(parts) != 3:
                    continue
                date_iso = f'{parts[2]}-{parts[1]}-{parts[0]}'
                result[date_iso] = {
                    'close':  row.get('Close',  0),
                    'volume': row.get('Volume', 0),
                    'open':   row.get('Open',   0),
                    'high':   row.get('High',   0),
                    'low':    row.get('Low',    0),
                }
            time.sleep(delay)

        return result

    def load_existing(self):
        if os.path.exists(self.out_file):
            with open(self.out_file, encoding='utf-8') as f:
                try:
                    return json.load(f)
                except Exception:
                    return {}
        return {}

    def save(self, data):
        with open(self.out_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

    def run(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--full',   action='store_true', help='Re-scrape tout depuis 2005')
        parser.add_argument('--ticker', type=str, default=None, help='Un seul ticker')
        parser.add_argument('--since',  type=str, default=None, help='Depuis date YYYY-MM-DD')
        args = parser.parse_args()

        history = self.load_existing()
        tickers = [args.ticker] if args.ticker else list(self.country_map.keys())

        for tk in tickers:
            if args.full:
                since = self.start_date
            elif args.since:
                since = date.fromisoformat(args.since)
            else:
                existing = history.get(tk, {})
                if existing:
                    last_date = max(existing.keys())
                    since = date.fromisoformat(last_date) - timedelta(days=5)
                else:
                    since = self.start_date

            print(f"  {tk:<8}  depuis {since}...", end=' ', flush=True)
            new_data = self.scrape_ticker(tk, since=since)

            if new_data:
                if tk not in history:
                    history[tk] = {}
                history[tk].update(new_data)
                print(f"{len(new_data)} entrées  "
                      f"(total: {len(history[tk])}  "
                      f"de {min(history[tk])} à {max(history[tk])})")
            else:
                print("aucune donnée")

        self.save(history)
        print(f"\nSauvegardé → {self.out_file}")
        print(f"Tickers: {len(history)}  "
              f"Total entrées: {sum(len(v) for v in history.values())}")


if __name__ == '__main__':
    SikaHistoryScraper().run()
