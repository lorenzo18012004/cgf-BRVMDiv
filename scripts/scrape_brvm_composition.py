"""
scrape_brvm_composition.py — Mise à jour automatique de la composition ETFDividende
=============================================================================
Scrape la composition officielle du ETFDividende depuis sikafinance.com.
Compare avec brvm_composition_latest.json — met à jour uniquement si changement.
Alimente propose_rebalancing.py qui détecte ensuite les entrées/sorties.

Usage :
    python scrape_brvm_composition.py
    python scrape_brvm_composition.py --force   # forcer la mise à jour
"""

import os, sys, json, re, argparse, warnings
from datetime import datetime, date, timezone

warnings.filterwarnings("ignore")
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

from base import BaseScript


class BRVMCompositionScraper(BaseScript):

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    # Page Sika listant les composantes du ETFDividende
    SIKA_ETFDividende_URL = "https://www.sikafinance.com/marches/aaz"
    # Page BRVM officielle (fallback)
    BRVM_INDEX_URL  = "https://www.brvm.org/fr/cours-indices/0/index/BRVM-30"

    def __init__(self):
        super().__init__()
        self.out_file  = os.path.join(self.data_dir, "brvm_composition_latest.json")
        self.hist_file = os.path.join(self.data_dir, "brvm_composition_history.json")

    # ------------------------------------------------------------------ #

    def _fetch(self, url):
        r = requests.get(url, headers=self.HEADERS, timeout=25, verify=False)
        r.raise_for_status()
        return r.text

    def _parse_sika(self, html):
        """Extrait les tickers ETFDividende depuis la page Sika (tableau des cotations)."""
        soup = BeautifulSoup(html, "html.parser")
        tickers = []
        for row in soup.select("table tr"):
            cells = row.find_all("td")
            if not cells:
                continue
            # Cherche une colonne "indice" ou "index" contenant ETFDividende
            row_text = row.get_text(" ").upper()
            if "ETFDividende" in row_text or "BRVM 30" in row_text:
                # Récupère le ticker (1ère cellule généralement)
                tk_cell = cells[0].get_text(strip=True)
                if re.match(r"^[A-Z]{3,5}$", tk_cell):
                    tickers.append(tk_cell)
        return sorted(set(tickers))

    def _parse_brvm(self, html):
        """Extrait les tickers depuis la page officielle BRVM."""
        soup = BeautifulSoup(html, "html.parser")
        tickers = []
        for cell in soup.find_all(["td", "span", "div"]):
            txt = cell.get_text(strip=True)
            if re.match(r"^[A-Z]{3,5}$", txt):
                tickers.append(txt)
        return sorted(set(tickers))

    def _scrape_tickers(self):
        """Tente Sika en premier, puis BRVM officiel en fallback."""
        for url, parser in [
            (self.SIKA_ETFDividende_URL, self._parse_sika),
            (self.BRVM_INDEX_URL,  self._parse_brvm),
        ]:
            try:
                html    = self._fetch(url)
                tickers = parser(html)
                if len(tickers) >= 20:          # santé minimale : au moins 20 tickers
                    print(f"  Source : {url}")
                    return tickers
                print(f"  [WARN] {url} → seulement {len(tickers)} tickers, fallback...")
            except Exception as e:
                print(f"  [WARN] {url} → {e}")
        return []

    # ------------------------------------------------------------------ #

    def run(self, force = False):
        today = date.today().isoformat()

        # Composition actuelle
        current = self.load_json("brvm_composition_latest.json", {})
        current_tickers = set(current.get("composition", []))
        current_rebal   = current.get("rebal_date", "")

        print("[INFO] Scraping composition ETFDividende...")
        new_tickers = self._scrape_tickers()

        if not new_tickers:
            print("[ERREUR] Impossible de récupérer la composition ETFDividende.")
            return False

        new_set = set(new_tickers)
        print(f"  {len(new_tickers)} tickers trouvés : {sorted(new_tickers)}")

        # Comparer avec la composition actuelle
        if not force and new_set == current_tickers:
            print(f"[INFO] Composition inchangée vs {current_rebal}. Rien à faire.")
            return False

        entries = sorted(new_set - current_tickers)
        exits   = sorted(current_tickers - new_set)

        if not force and not entries and not exits:
            print("[INFO] Aucun changement de composition détecté.")
            return False

        print(f"[OK] Changement détecté !")
        if entries: print(f"  Entrants : {entries}")
        if exits:   print(f"  Sortants : {exits}")

        # Mise à jour brvm_composition_latest.json
        new_comp = {
            "rebal_date":  today,
            "scrape_ts":   datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "n_tickers":   len(new_tickers),
            "composition": sorted(new_tickers),
            "entries":     entries,
            "exits":       exits,
        }
        self.save_json("brvm_composition_latest.json", new_comp)
        print(f"[OK] brvm_composition_latest.json mis à jour ({today}).")

        # Ajout dans l'historique
        hist = self.load_json("brvm_composition_history.json", [])
        if not isinstance(hist, list):
            hist = []
        hist.append({
            "scrape_date": today,
            "scrape_time": datetime.now(timezone.utc).strftime("%H:%M UTC"),
            "n_stocks_total": len(new_tickers),
            "etfdividende":   sorted(new_tickers),
            "entries":  entries,
            "exits":    exits,
        })
        self.save_json("brvm_composition_history.json", hist)
        print("[OK] brvm_composition_history.json mis à jour.")

        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper composition ETFDividende")
    parser.add_argument("--force", action="store_true",
                        help="Forcer la mise à jour même si composition inchangée")
    args = parser.parse_args()
    BRVMCompositionScraper().run(force=args.force)
