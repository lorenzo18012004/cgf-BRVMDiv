"""
scrape_intraday_cloud.py — iNAV ETF CGF BRVMHalal (GitHub Actions)
"""
import sys, os, json, argparse, warnings
warnings.filterwarnings("ignore")

from datetime import datetime, time as dtime, timezone

from base import BaseScript


class IntradayScraperCloud(BaseScript):
    def __init__(self):
        super().__init__()
        self.MARKET_OPEN   = dtime(9,  0)
        self.MARKET_CLOSE  = dtime(15, 30)
        self.INTRADAY_FILE = os.path.join(self.data_dir, "intraday_nav.json")
        self.HIST_FILE     = os.path.join(self.data_dir, "nav_intraday_history.json")

    def _is_market_open(self):
        now = datetime.now(timezone.utc)
        if now.weekday() >= 5:
            return False
        t = now.time().replace(tzinfo=None)
        return self.MARKET_OPEN <= t <= self.MARKET_CLOSE

    def run(self, force=False):
        os.chdir(self.data_dir)
        sys.path.insert(0, self.scripts_dir)

        now_utc   = datetime.now(timezone.utc)
        today_str = now_utc.strftime("%Y-%m-%d")

        if not force and not self._is_market_open():
            print(f"[{now_utc.strftime('%H:%M')} UTC] Hors heures de marche BRVM -- rien a faire.")
            return None

        try:
            from data_provider import get_provider
            _dp         = get_provider()
            live_prices = _dp.get_live_prices()
        except Exception as e:
            print(f"[ERREUR] Récupération données marché : {e}")
            return None

        try:
            nav_path    = os.path.join(self.data_dir, "nav_latest.json")
            launch_path = os.path.join(self.data_dir, "launch_state.json")
            with open(nav_path, encoding="utf-8") as _f:
                _nl = json.load(_f)
            _ls      = json.load(open(launch_path, encoding="utf-8")) if os.path.exists(launch_path) else {}
            _basket  = _nl.get("basket", [])
            _nav_base = _nl["nav_indice"]
            _vl_base  = _nl.get("vl_par_part_fcfa", _nl.get("par_fcfa", 100000))

            _total_ret = 0.0
            _n_live    = 0
            _prices_now = {}
            _ticker_contribs = {}
            for _item in _basket:
                _tk  = _item["ticker"]
                _w   = _item["poids_pct"] / 100.0
                _w_pct = _item["poids_pct"]
                _p0  = _item.get("dernier_prix")
                _p1  = float(live_prices[_tk]) if _tk in live_prices.index else None
                if _p1:
                    _prices_now[_tk] = round(_p1, 0)
                if _p0 and _p0 > 0 and _p1 and _p1 > 0:
                    _ret = (_p1 / _p0 - 1)
                    _total_ret += _w * _ret
                    _n_live += 1
                    _ticker_contribs[_tk] = {
                        "w_pct":           round(_w_pct, 4),
                        "w_brvm30_pct":    round(_w_pct, 4),
                        "prix_prev":       _p0,
                        "prix_now":        _p1,
                        "ret_pct":         round(_ret * 100, 3),
                        "contrib_pct":     round(_w * _ret * 100, 4),
                        "gap_contrib_pct": 0.0,
                    }

            _nav_live   = _nav_base * (1.0 + _total_ret)
            _nav_anchor = float(_ls["nav_index_at_launch"]) if _ls and _ls.get("nav_index_at_launch") else None
            if _nav_anchor:
                _vl_live = float(_ls["par_fcfa"]) * (_nav_live / _nav_anchor)
                _n_parts = _ls.get("n_parts", _nl.get("n_parts", 25000))
            else:
                _nav_anchor = _nav_live
                _par        = float((_ls or {}).get("par_fcfa", _vl_base))
                _vl_live    = _par
                _n_parts    = _nl.get("n_parts", 25000)
                if _ls:
                    _ls["nav_index_at_launch"] = round(_nav_anchor, 6)
                    with open(os.path.join(self.data_dir, "launch_state.json"), "w", encoding="utf-8") as _fw:
                        json.dump(_ls, _fw, ensure_ascii=False, indent=2)
                    print(f"[LANCEMENT] nav_index_at_launch fixé à {_nav_anchor:.6f}")

            nav_result = {
                "nav_indice":       round(_nav_live, 4),
                "vl_par_part_fcfa": round(_vl_live, 0),
                "change_1d_pct":    round((_nav_live / _nav_base - 1) * 100, 4),
                "aum_mfcfa":        round(_vl_live * _n_parts / 1_000_000, 1),
                "n_live_prices":    _n_live,
            }
        except Exception as e:
            print(f"[ERREUR] Calcul VL : {e}")
            return None

        if os.path.exists(self.INTRADAY_FILE):
            with open(self.INTRADAY_FILE, encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"date": None, "snapshots": []}

        if data.get("date") != today_str:
            data = {"date": today_str, "snapshots": [], "open_nav": nav_result["nav_indice"]}

        open_nav   = data.get("open_nav", nav_result["nav_indice"])
        change_day = (nav_result["nav_indice"] / open_nav - 1) * 100

        vl_live     = nav_result.get("vl_par_part_fcfa", 0)
        perf_launch = None
        if os.path.exists(launch_path):
            with open(launch_path, encoding="utf-8") as f:
                ls = json.load(f)
            nav_anchor  = float(ls.get("nav_index_at_launch") or nav_result["nav_indice"])
            par_fcfa    = float(ls.get("par_fcfa", 100_000))
            vl_live     = round(par_fcfa * (nav_result["nav_indice"] / nav_anchor), 0)
            perf_launch = round((nav_result["nav_indice"] / nav_anchor - 1) * 100, 4)

        snapshot = {
            "time":                 now_utc.strftime("%H:%M"),
            "nav_indice":           nav_result["nav_indice"],
            "halal_official":       nav_result["nav_indice"],
            "vl_par_part":          nav_result["vl_par_part_fcfa"],
            "vl_live_fcfa":         vl_live,
            "perf_since_launch":    perf_launch,
            "change_1d_pct":        nav_result["change_1d_pct"],
            "change_day_pct":       round(change_day, 4),
            "aum_mfcfa":            nav_result["aum_mfcfa"],
            "n_prices":             nav_result["n_live_prices"],
            "prices_by_ticker":     _prices_now,
            "ticker_contributions": _ticker_contribs,
        }

        existing_times = {s["time"] for s in data["snapshots"]}
        if snapshot["time"] not in existing_times:
            data["snapshots"].append(snapshot)

        with open(self.INTRADAY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        try:
            hist = json.load(open(self.HIST_FILE, encoding="utf-8")) if os.path.exists(self.HIST_FILE) else {}
            if today_str not in hist:
                hist[today_str] = []
            if snapshot["time"] not in {p["time"] for p in hist[today_str]}:
                hist[today_str].append({
                    "time":              snapshot["time"],
                    "vl":                round(vl_live, 0),
                    "nav_indice":        snapshot["nav_indice"],
                    "perf_since_launch": snapshot["perf_since_launch"],
                    "change_1d_pct":     snapshot["change_1d_pct"],
                    "change_day_pct":    snapshot["change_day_pct"],
                    "aum_mfcfa":         snapshot["aum_mfcfa"],
                    "n_prices":          snapshot["n_prices"],
                })
            with open(self.HIST_FILE, "w", encoding="utf-8") as f:
                json.dump(hist, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[WARN] Historique : {e}")

        launch_str = f" | Dlancement {perf_launch:+.3f}%" if perf_launch is not None else ""
        print(f"[{snapshot['time']} UTC] iNAV {nav_result['nav_indice']:.4f} | VL {vl_live:,.0f} FCFA | Djour {change_day:+.3f}%{launch_str}")
        return snapshot


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="iNAV CGF BRVMHalal ETF -- cloud")
    parser.add_argument("--force", action="store_true", help="Forcer meme hors heures de marche")
    args = parser.parse_args()
    result = IntradayScraperCloud().run(force=args.force)
    if result is None and not args.force:
        print("Utilisez --force pour tester hors heures de marche.")
