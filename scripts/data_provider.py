"""
data_provider.py — Interface de données BRVM
============================================
Découple la couche métier (calc_nav, rebalance, iNAV) de la source de données.

POUR IT :
    Pour connecter une source alternative (Bloomberg, API BRVM officielle, OMS, etc.) :
      1. Copier data_provider_template.py → data_provider_<nom>.py
      2. Implémenter les 4 méthodes abstraites
      3. Définir  DATA_PROVIDER=<nom>  dans les secrets GitHub Actions

    Exemple : DATA_PROVIDER=bloomberg → charge BloombergProvider depuis data_provider_bloomberg.py

CONTRAT JSON (formats attendus dans data/)
------------------------------------------
sika_history.json — prix de clôture historiques :
    {
      "SNTS": {
        "2024-01-02": {"close": 15000.0, "volume": 1234, "open": 14900.0, "high": 15100.0, "low": 14800.0},
        "2024-01-03": { ... }
      },
      ...
    }

sika_societe.json — données sociétés (capitalisation) :
    {
      "SNTS": {"nb_titres": 50000000.0, "flottant_pct": 25.0, "valorisation_mfcfa": 1500000.0},
      ...
    }
"""

import os
import importlib
from abc import ABC, abstractmethod

import pandas as pd


class BRVMDataProvider(ABC):
    """
    Interface que toute source de données BRVM doit implémenter.

    La couche métier (iNAV, NAV, rebalancement) ne connaît que cette interface —
    elle ne sait pas si les données viennent de Sika Finance, Bloomberg, ou autre.
    """

    @abstractmethod
    def get_live_prices(self) -> pd.Series:
        """
        Cours du jour de tous les titres BRVM (temps réel ou fin de séance).
        Retourne une Series pandas { ticker: float }.
        Doit couvrir au minimum les 30 titres du BRVM30 courant.
        """

    @abstractmethod
    def get_brvm30_index(self) -> "float | None":
        """
        Valeur courante de l'indice BRVM30 (ex: 285.42).
        Retourne None si la valeur n'est pas disponible.
        """

    def get_brvmc_index(self) -> "float | None":
        """Valeur courante de l'indice BRVM Composite. Retourne None si indisponible."""
        return None

    @abstractmethod
    def update_price_history(self, tickers: "list | None" = None) -> dict:
        """
        Télécharge les cours de clôture récents et met à jour data/sika_history.json.
        Appelé quotidiennement par GitHub Actions (workflow scrape_history).

        Paramètres :
            tickers : liste de tickers à mettre à jour (None = tous les tickers BRVM)

        Retourne :
            dict { ticker: nombre_de_nouvelles_entrées_ajoutées }

        La méthode DOIT écrire (ou compléter) data/sika_history.json
        au format décrit en en-tête de ce fichier.
        """

    @abstractmethod
    def update_societe(self, tickers: "list | None" = None) -> dict:
        """
        Met à jour data/sika_societe.json (nb de titres, flottant, capitalisation).
        Appelé lors des rebalancements trimestriels.

        Retourne :
            dict { ticker: nb_titres }

        La méthode DOIT écrire (ou compléter) data/sika_societe.json
        au format décrit en en-tête de ce fichier.
        """


# ─────────────────────────────────────────────────────────────────────────────
# Implémentation par défaut : Sika Finance
# ─────────────────────────────────────────────────────────────────────────────

class SikaProvider(BRVMDataProvider):
    """
    Implémentation via sikafinance.com (source actuelle).
    Le cache HTML évite deux requêtes HTTP pour le même snapshot intraday.
    """

    def __init__(self):
        self._html_cache = None

    def _get_html(self) -> str:
        if self._html_cache is None:
            from scrape_sika import _fetch_html, SIKA_URL
            self._html_cache = _fetch_html(SIKA_URL)
        return self._html_cache

    def get_live_prices(self) -> pd.Series:
        from scrape_sika import scrape_prices
        return scrape_prices(self._get_html())

    def get_brvm30_index(self) -> "float | None":
        from scrape_sika import scrape_brvm30_index
        return scrape_brvm30_index(self._get_html())

    def get_brvmc_index(self) -> "float | None":
        from scrape_sika import scrape_brvmc_index
        return scrape_brvmc_index(self._get_html())

    def update_price_history(self, tickers: "list | None" = None) -> dict:
        from scrape_sika_history import SikaHistoryScraper
        SikaHistoryScraper().run()
        return {}

    def update_societe(self, tickers: "list | None" = None) -> dict:
        # Les données sociétés sont scrappées via scrape_brvm_composition.py
        # et stockées directement dans sika_societe.json
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────────────────

def get_provider() -> BRVMDataProvider:
    """
    Retourne le provider actif selon la variable d'environnement DATA_PROVIDER.
    Par défaut : SikaProvider.

    Pour brancher un nouveau provider :
      1. Créer scripts/data_provider_<nom>.py  (voir data_provider_template.py)
      2. Définir  DATA_PROVIDER=<nom>  dans GitHub Actions → Settings → Secrets
    """
    name = os.environ.get("DATA_PROVIDER", "sika").lower()

    if name == "sika":
        return SikaProvider()

    # Chargement dynamique d'un provider externe
    try:
        mod      = importlib.import_module(f"data_provider_{name}")
        cls_name = name.capitalize() + "Provider"
        cls      = getattr(mod, cls_name)
        return cls()
    except ImportError:
        raise ValueError(
            f"[data_provider] Module 'data_provider_{name}.py' introuvable dans scripts/. "
            f"Créer ce fichier à partir de data_provider_template.py."
        )
    except AttributeError:
        raise ValueError(
            f"[data_provider] Classe '{name.capitalize()}Provider' absente de data_provider_{name}.py."
        )
