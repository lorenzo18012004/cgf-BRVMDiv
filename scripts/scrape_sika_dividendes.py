"""
scrape_sika_dividendes.py — Scrape les dividendes BRVM depuis Sika Finance
===========================================================================
Source : https://www.sikafinance.com/marches/dividendes
Produit : sika_dividendes.json

Format de sortie :
{
  "annee": 2026,
  "scraped_at": "2026-06-11T18:00:00",
  "dividendes": [
    {
      "nom_sika":    "ORANGE CI",
      "ticker":      "ORAC",
      "date_detach": "2026-06-05",   // null si "A préciser"
      "montant":     800.0,
      "rendement":   5.06
    },
    ...
  ],
  "historique": {
    "ORAC": {"2022": 650.0, "2023": 700.0, "2024": 750.0, "2025": null},
    ...
  }
}

Usage :
    python scrape_sika_dividendes.py
"""

import sys, io, os, json, re, warnings, argparse
from datetime import datetime
warnings.filterwarnings('ignore')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

from base import BaseScript


class SikaDividendesScraper(BaseScript):

    def __init__(self):
        super().__init__()
        self.sika_url  = 'https://www.sikafinance.com/marches/dividendes'
        self.out_file  = os.path.join(self.data_dir, 'sika_dividendes.json')
        self.hist_file = os.path.join(self.data_dir, 'dividend_history.json')
        self.headers   = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            ),
            'Accept-Language': 'fr-FR,fr;q=0.9',
        }
        self.nom_to_ticker = {
            "ORANGE CI":                        "ORAC",
            "ONATEL BF":                        "ONTBF",
            "CORIS BANK INTERNATIONAL BF":      "CBIBF",
            "PALMCI":                           "PALC",
            "CIE CI":                           "CIEC",
            "SMB CI":                           "SMBC",
            "NEI CEDA CI":                      "NEIC",
            "SOCIETE IVOIRIENNE DE BANQUE CI":  "SIBC",
            "SGBCI":                            "SGBC",
            "ETI TG":                           "ETIT",
            "SODECI":                           "SDSC",
            "SAPH CI":                          "SHEC",
            "SERVAIR ABIDJAN CI":               "SAFC",
            "TRACTAFRIC MOTORS CI":             "TTLC",
            "TOTAL CI":                         "TOTC",
            "TOTAL SENEGAL":                    "TOSG",
            "VIVO ENERGY CI":                   "VIVC",
            "LOTERIE NATIONALE DU BENIN":       "LNBB",
            "NESTLE CI":                        "NLCI",
            "SNTS CI":                          "SNTS",
            "SOCIETE GENERALE CI":              "SGBC",
            "BANK OF AFRICA CI":                "BOAC",
            "BANK OF AFRICA BENIN":             "BOAB",
            "BANK OF AFRICA BURKINA":           "BOABF",
            "BANK OF AFRICA NIGER":             "BOAN",
            "BANK OF AFRICA MALI":              "BOAM",
            "ECOBANK CI":                       "ECOC",
            "ECOBANK TRANSNATIONAL":            "ETIT",
            "SOLIBRA":                          "SLBC",
            "SICABLE CI":                       "SCRC",
            "SIFCA CI":                         "SIVC",
            "BICICI":                           "BICC",
            "CFAO MOTORS CI":                   "CFAC",
            "SIB CI":                           "SIBC",
            "BERNABE CI":                       "BNBC",
            "SAFCA CI":                         "SAFC",
            "SETAO CI":                         "STAC",
            "SOGB CI":                          "SOGC",
            "SITAB CI":                         "SDSC",
            "FILTISAC":                         "FTSC",
            "PRECIA":                           "PRSC",
            "AFRICA GLOBAL LOGIST":             "ABJC",
            "AFRICAINE LOGISTIQUE":             "ABJC",
            "ORGT":                             "ORGT",
        }

    def _norm(self, name):
        """Normalise un nom pour la comparaison."""
        return re.sub(r'\s+', ' ', name.strip().upper())

    def _to_ticker(self, name):
        n = self._norm(name)
        if n in self.nom_to_ticker:
            return self.nom_to_ticker[n]
        for k, v in self.nom_to_ticker.items():
            if n.startswith(k[:6]) or k.startswith(n[:6]):
                return v
        return None

    def _parse_date(self, txt):
        txt = txt.strip()
        m = re.match(r'(\d{2})/(\d{2})/(\d{4})', txt)
        if m:
            return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        return None

    def _parse_float(self, txt):
        txt = txt.strip().replace(',', '.').replace('\xa0', '').replace(' ', '')
        txt = re.sub(r'[^\d.]', '', txt)
        try:
            return float(txt)
        except ValueError:
            return None

    def scrape(self, year = None):
        if year is None:
            year = datetime.now().year

        print(f"Scraping dividendes Sika Finance {year}...")
        r = requests.get(self.sika_url, headers=self.headers, verify=False, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        tables = soup.find_all('table')

        dividendes = []
        if tables:
            for row in tables[0].find_all('tr')[1:]:
                cells = [td.get_text(strip=True).replace('\xa0', ' ') for td in row.find_all('td')]
                if len(cells) < 3:
                    continue
                date_str = cells[0]
                nom      = cells[1].strip()
                montant  = self._parse_float(cells[2]) if len(cells) > 2 else None
                rend     = self._parse_float(cells[3]) if len(cells) > 3 else None
                if not nom or montant is None:
                    continue
                dividendes.append({
                    "nom_sika":    nom,
                    "ticker":      self._to_ticker(nom),
                    "date_detach": self._parse_date(date_str),
                    "montant":     montant,
                    "rendement":   rend,
                })

        historique: dict[str, dict] = {}
        if len(tables) > 1:
            year_cols = []
            headers   = [th.get_text(strip=True) for th in tables[1].find_all('th')]
            for h in headers:
                m = re.search(r'(\d{4})', h)
                if m and 'Div' in h:
                    year_cols.append(m.group(1))

            for row in tables[1].find_all('tr')[1:]:
                cells = [td.get_text(strip=True).replace('\xa0', ' ') for td in row.find_all('td')]
                if not cells:
                    continue
                nom    = cells[0].strip()
                ticker = self._to_ticker(nom)
                if not ticker:
                    continue
                entry = {}
                for i, yr in enumerate(year_cols):
                    idx = 1 + i * 2
                    if idx < len(cells):
                        v = self._parse_float(cells[idx])
                        entry[yr] = v
                if entry:
                    historique[ticker] = entry

        result = {
            "annee":      year,
            "scraped_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            "dividendes": dividendes,
            "historique": historique,
        }

        n_ok = sum(1 for d in dividendes if d["ticker"])
        n_ko = sum(1 for d in dividendes if not d["ticker"])
        print(f"  {len(dividendes)} dividendes scraped : {n_ok} tickers reconnus, {n_ko} inconnus")
        if n_ko:
            unknowns = [d["nom_sika"] for d in dividendes if not d["ticker"]]
            print(f"  Inconnus : {unknowns}")

        with open(self.out_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  → {self.out_file}")

        self._update_dividend_history(historique, dividendes, year)

        return result

    def _update_dividend_history(self, historique, dividendes, year):
        """Merge les données historiques + dividendes confirmés de l'année dans dividend_history.json."""
        if os.path.exists(self.hist_file):
            with open(self.hist_file, 'r', encoding='utf-8') as f:
                db = json.load(f)
            history = db.get('history', {})
            meta    = {k: v for k, v in db.items() if k != 'history'}
        else:
            history = {}
            meta    = {}

        for ticker, years_data in historique.items():
            if ticker not in history:
                history[ticker] = {}
            for yr, montant in years_data.items():
                if montant is not None:
                    history[ticker][yr] = montant
                elif yr not in history[ticker]:
                    history[ticker][yr] = None

        yr_str = str(year)
        for div in dividendes:
            ticker  = div.get('ticker')
            montant = div.get('montant')
            if ticker and montant is not None:
                if ticker not in history:
                    history[ticker] = {}
                history[ticker][yr_str] = montant

        history_sorted = {
            t: dict(sorted(yrs.items()))
            for t, yrs in sorted(history.items())
        }

        out = {
            "updated_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            "source":     "sikafinance.com/marches/dividendes",
            "n_tickers":  len(history_sorted),
            "history":    history_sorted,
        }

        with open(self.hist_file, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

        n_years = max((len(v) for v in history_sorted.values()), default=0)
        print(f"  → {self.hist_file}  ({len(history_sorted)} tickers, jusqu'à {n_years} années/ticker)")

    def run(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--year', type=int, default=None)
        args = parser.parse_args()
        self.scrape(year=args.year)


if __name__ == '__main__':
    SikaDividendesScraper().run()
