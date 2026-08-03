"""
calc_nav_cloud.py — NAV quotidienne ETF CGF BRVMHalal (GitHub Actions)
"""
import sys, os, warnings
warnings.filterwarnings("ignore")

from datetime import datetime, timezone

from base import BaseScript


class NavCalculatorCloud(BaseScript):

    def __init__(self):
        super().__init__()
        self.NAV_PATH    = os.path.join(self.data_dir, "nav_latest.json")
        self.SIKA_PATH   = os.path.join(self.data_dir, "sika_history.json")
        self.LAUNCH_PATH = os.path.join(self.data_dir, "launch_state.json")

    def run(self):
        os.chdir(self.data_dir)

        now_utc   = datetime.now(timezone.utc)
        today_str = now_utc.strftime("%Y-%m-%d")

        nl = self.load_json_path(self.NAV_PATH, default=None)
        if nl is None:
            print("[ERREUR] nav_latest.json introuvable")
            sys.exit(1)

        last_date = nl.get("calc_date") or nl.get("date", "")
        if last_date >= today_str:
            print(f"[OK] nav_latest.json deja a jour ({last_date}) -- rien a faire.")
            return

        print(f"nav_latest.json pas encore mis a jour pour {today_str} -- calcul via sika...")

        sika = self.load_json_path(self.SIKA_PATH, default=None)
        if sika is None:
            print("[ERREUR] sika_history.json introuvable")
            sys.exit(1)

        latest_prices = {}
        for ticker, hist in sika.items():
            if hist:
                last_d = max(hist.keys())
                v      = hist[last_d]
                close  = v.get("close") if isinstance(v, dict) else v
                if close:
                    latest_prices[ticker] = float(close)

        basket = nl.get("basket", [])
        if not basket:
            print("[ERREUR] basket vide dans nav_latest.json")
            sys.exit(1)

        nav_base = float(nl.get("nav_indice") or nl.get("nav_index") or 0)
        if nav_base == 0:
            print("[ERREUR] nav_indice manquant dans nav_latest.json")
            sys.exit(1)
        vl_base  = float(nl.get("vl_par_part_fcfa") or nl.get("par_fcfa", 100000))
        n_parts  = int(nl.get("n_parts", 25000))

        MGMT_FEE_ANN = 0.006
        fee_daily    = (1.0 - MGMT_FEE_ANN) ** (1.0 / 252.0)

        portfolio_new = {}
        n_live        = 0
        for item in basket:
            tk  = item["ticker"]
            v   = item["poids_pct"] / 100.0
            p0  = item.get("dernier_prix")
            p1  = latest_prices.get(tk)
            if p0 and p0 > 0 and p1 and p1 > 0:
                portfolio_new[tk] = v * (p1 / p0)
                n_live += 1
            else:
                portfolio_new[tk] = v

        v_total   = sum(portfolio_new.values()) or 1.0
        total_ret = v_total - 1.0

        nav_new       = nav_base * v_total * fee_daily
        nav_base_idx  = float(nl.get("nav_indice_reference") or nav_base)
        nav_index_new = nav_base_idx * v_total  # sans fee ni cash drag

        for item in basket:
            tk = item["ticker"]
            if tk in portfolio_new:
                item["poids_pct"] = round(portfolio_new[tk] / v_total * 100, 4)

        ls = self.load_json_path(self.LAUNCH_PATH, default=None)
        if ls is not None:
            nav_anchor = ls.get("nav_index_at_launch")
            n_parts    = int(ls.get("n_parts", n_parts))
            par_ls     = float(ls.get("par_fcfa", 100_000))
            if not nav_anchor:
                nav_anchor = nav_new
                ls["nav_index_at_launch"] = round(float(nav_new), 6)
                self.save_json_path(self.LAUNCH_PATH, ls)
                print(f"[LANCEMENT] nav_index_at_launch fixé à {nav_anchor:.6f}")
            vl_new   = par_ls * (nav_new / float(nav_anchor))
            perf_lct = (nav_new / float(nav_anchor) - 1) * 100
        else:
            vl_new   = vl_base * (1.0 + total_ret)
            perf_lct = total_ret * 100

        aum = vl_new * n_parts / 1_000_000
        chg = total_ret * 100

        live_series = nl.get("nav_live_series") or []
        from datetime import date as _date
        live_series = [r for r in live_series if _date.fromisoformat(r[0]).weekday() < 5]
        existing_dates = {row[0] for row in live_series}
        if today_str not in existing_dates and now_utc.weekday() < 5:
            live_series.append([today_str, round(vl_new, 0)])
            live_series.sort(key=lambda x: x[0])

        nl.update({
            "calc_date":           today_str,
            "launched":            True,
            "nav_indice":          round(nav_new, 4),
            "nav_indice_reference": round(nav_index_new, 4),
            "vl_par_part_fcfa":    round(vl_new, 0),
            "aum_mfcfa":           round(aum, 1),
            "perf_since_launch":   round(perf_lct, 4),
            "change_day_pct":      round(chg, 4),
            "source":              "cloud_fallback_sika",
            "n_live_prices":       n_live,
            "nav_live_series":     live_series,
        })

        for item in nl["basket"]:
            tk = item["ticker"]
            if tk in latest_prices:
                item["dernier_prix"]    = latest_prices[tk]
                item["last_price_date"] = today_str
            item["pv_mfcfa"]   = round((item["poids_pct"] / 100) * aum, 1)
            item["prix_stale"] = item.get("last_price_date", "") < today_str
            item.setdefault("w_brvm30",   round(item["poids_pct"] / 100, 6))
            item.setdefault("adv_mfcfa",  None)
            item.setdefault("force_otc",  False)

        self.save_json_path(self.NAV_PATH, nl)

        print(f"[OK] nav_latest.json mis a jour ({today_str})")
        print(f"     NAV indice   : {nav_new:.4f}")
        print(f"     VL par part  : {vl_new:,.0f} FCFA")
        print(f"     Perf lct     : {perf_lct:+.3f}%")
        print(f"     Variation J  : {chg:+.3f}%")
        print(f"     Cours utilises: {n_live} tickers")


if __name__ == "__main__":
    NavCalculatorCloud().run()
