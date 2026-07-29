"""
apply_rebalancing.py — Application d'un rebalancement après validation manuelle
================================================================================
Lit rebal_pending.json (généré par propose_rebalancing.py) et l'ajoute
à rebal_detail.json. Déclenché UNIQUEMENT via workflow_dispatch sur GitHub.

Usage :
    python apply_rebalancing.py
"""

import os, sys
from datetime import datetime, timezone

from base import BaseScript


class RebalancingApplier(BaseScript):

    def run(self):
        pending = self.load_json("rebal_pending.json", {})

        if not pending:
            print("[ERREUR] rebal_pending.json vide ou absent.")
            return False

        status = pending.get("status")
        if status == "applied":
            print(f"[INFO] Ce rebalancement a déjà été appliqué le "
                  f"{pending.get('applied_at', '?')}.")
            return False
        if status != "pending":
            print(f"[ERREUR] Statut inattendu dans rebal_pending.json : {status!r}")
            return False

        rebal_date   = pending["proposed_rebal_date"]
        new_basket   = pending["new_basket"]       # liste complète avec adv_mfcfa, days_exec…
        excluded     = pending.get("excluded", [])
        entries      = pending.get("entries", [])
        exits        = pending.get("exits",   [])
        turnover     = pending.get("turnover_pct", 0.0)
        excess_cnt   = pending.get("excess_days_cnt", {})

        print(f"[OK] Application du rebalancement {rebal_date}...")
        print(f"  Entrants : {entries or 'aucun'}")
        print(f"  Sortants : {exits or 'aucun'}")
        print(f"  Panier ETF : {len(new_basket)} titres")
        print(f"  Exclus ({len(excluded)}) :")
        for e in excluded:
            print(f"    {e['ticker']:8s} ({e.get('w_etfdividende',0)*100:.2f}%) — {e.get('raison','?')}")
        print(f"  Turnover estimé : {turnover}%")

        rd = self.load_json("rebal_detail.json", {"rebalancings": []})

        existing_dates = [r["date"] for r in rd.get("rebalancings", [])]
        if rebal_date in existing_dates:
            print(f"[WARN] Rebalancement {rebal_date} déjà présent dans rebal_detail.json.")
            pending["status"]     = "applied"
            pending["applied_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            self.save_json("rebal_pending.json", pending)
            return False

        excl_w   = round(sum(e.get("w_etfdividende", 0) for e in excluded), 4)
        coverage = round(sum(b.get("w_etfdividende", 0) for b in new_basket), 4)

        new_entry = {
            "date":            rebal_date,
            "date_label":      rebal_date,
            "skipped":         False,
            "basket_n":        len(new_basket),
            "excl_n":          len(excluded),
            "excl_w":          excl_w,
            "coverage":        coverage,
            "turnover":        round(turnover / 100, 4),
            "entries":         entries,
            "exits":           exits,
            "excess_days_cnt": excess_cnt,
            "basket":          new_basket,
            "excluded":        excluded,
            "applied_at":      datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "source":          "auto_proposal",
        }

        rd["rebalancings"].append(new_entry)
        self.save_json("rebal_detail.json", rd)

        pending["status"]     = "applied"
        pending["applied_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        self.save_json("rebal_pending.json", pending)

        print(f"[OK] Rebalancement {rebal_date} ajouté à rebal_detail.json.")
        print("[OK] rebal_pending.json marqué comme appliqué.")
        return True


if __name__ == "__main__":
    RebalancingApplier().run()
