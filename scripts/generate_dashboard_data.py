"""
Génère dashboard_data.json et backtest_metrics.json pour ETFDividende
à partir de validation_results.json et rebal_detail.json.
"""
import json, os, math
from datetime import datetime

BASE     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, "data")

MONTHS = {1:'Jan.',2:'Feb.',3:'Mar.',4:'Apr.',5:'May.',6:'Jun.',
          7:'Jul.',8:'Aug.',9:'Sep.',10:'Oct.',11:'Nov.',12:'Dec.'}

vr = json.load(open(os.path.join(DATA_DIR, "validation_results.json"), encoding="utf-8"))
rd = json.load(open(os.path.join(DATA_DIR, "rebal_detail.json"),       encoding="utf-8"))

# Assurer que chaque rebalancing a un date_label
for r in rd.get("rebalancings", []):
    if "date_label" not in r:
        d = datetime.fromisoformat(r["date"])
        r["date_label"] = f"{d.day:02d} {MONTHS[d.month]} {d.year}"
with open(os.path.join(DATA_DIR, "rebal_detail.json"), "w", encoding="utf-8") as _f:
    json.dump(rd, _f, ensure_ascii=False, indent=2)

# ── dashboard_data.json ───────────────────────────────────────────────────────
nav_etf   = vr.get("nav_etf_series",   [])
nav_bench = vr.get("nav_index_series", [])
m_etf     = vr.get("metrics_etf",      {})
m_idx     = vr.get("metrics_indice",   {})
td_ann    = vr.get("tracking_difference_ann_pct", 0) / 100
te_ann    = vr.get("tracking_error_ann_pct",       0) / 100

# rebal_history depuis rebal_detail
rebal_history = []
for r in rd.get("rebalancings", []):
    rebal_history.append({
        "date":     r["date"],
        "turnover": r.get("turnover", 0),
        "cost_bps": r.get("cost_bps", 0),
        "nav_after": None,
        "skipped":   r.get("skipped", False),
    })

# w_history : {date: {ticker: w_etf}}
w_history = {}
for r in rd.get("rebalancings", []):
    if r.get("skipped"):
        continue
    w_history[r["date"]] = {
        b["ticker"]: b.get("w_etf", 0) for b in r.get("basket", [])
    }

# Durée backtest en années
start = datetime.fromisoformat(vr.get("backtest_start", "2023-01-01"))
end   = datetime.fromisoformat(vr.get("backtest_end",   "2026-01-01"))
n_years = (end - start).days / 365.25

perf_etf   = m_etf.get("perf_total_pct", 0) / 100
perf_bench = m_idx.get("perf_total_pct", 0) / 100
td_total   = perf_etf - perf_bench

metrics = {
    "te":              te_ann,
    "td":              td_total,
    "td_gross":        td_total,
    "mgmt_fee_cumul":  -(1 - (1 - 0.006) ** n_years),
    "cost_tx_cumul":   vr.get("total_turnover_rebal", 0) * 0.001,
    "div_bench_factor": 1.0,
    "div_etf_factor":   1.0,
    "td_ann":           td_ann,
    "td_gross_ann":     td_ann,
    "te_gross":         te_ann,
}

dashboard_data = {
    "etf_name":      "CGF ETFDividende ETF",
    "nav_etf":       nav_etf,
    "nav_bench":     nav_bench,
    "nav_gross":     nav_etf,
    "metrics":       metrics,
    "rebal_history": rebal_history,
    "w_history":     w_history,
    "scalability":   [],
    "walk_forward":  [],
}

out_path = os.path.join(DATA_DIR, "dashboard_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(dashboard_data, f, ensure_ascii=False, indent=2)
print(f"[OK] dashboard_data.json -> {out_path}")

# ── backtest_metrics.json ─────────────────────────────────────────────────────
rebals = [r for r in rd.get("rebalancings", []) if not r.get("skipped")]
n_rebal    = len(rebals)
turnover_avg = vr.get("avg_turnover_per_rebal_pct", 0) / 100

# Nombre moyen de titres
n_titres_list = [len(r.get("basket", [])) for r in rebals]
n_titres_avg  = sum(n_titres_list) / len(n_titres_list) if n_titres_list else 0
n_titres_min  = min(n_titres_list) if n_titres_list else 0
n_titres_max  = max(n_titres_list) if n_titres_list else 0

# Performance annuelle — liste triée par année (le dashboard itère avec a.get("year"))
annual = []
for yr, p in vr.get("perf_by_year", {}).items():
    annual.append({
        "year":     int(yr),
        "etf":      p.get("etf_pct",    0) / 100,
        "bench":    p.get("indice_pct", 0) / 100,
        "td":       p.get("td_pct",     0) / 100,
        "td_gross": p.get("td_pct",     0) / 100,
        "te":       te_ann,
    })
annual.sort(key=lambda x: x["year"])

backtest_metrics = {
    "start_label":          vr.get("backtest_start", ""),
    "end_label":            vr.get("backtest_end",   ""),
    "n_years":              round(n_years, 2),
    "n_rebal":              n_rebal,
    "mgmt_fee_ann":         0.006,
    "te_full":              te_ann,
    "te_p1":                te_ann,
    "te_p2":                te_ann,
    "te_prog":              [[vr.get("backtest_start"), te_ann]],
    "td_full":              td_total,
    "td_full_ann":          td_ann,
    "mgmt_fee_cumul":       metrics["mgmt_fee_cumul"],
    "cost_tx_cumul":        metrics["cost_tx_cumul"],
    "basket_gap_cumul":     0.0,
    "td_structural_cumul":  metrics["mgmt_fee_cumul"] + metrics["cost_tx_cumul"],
    "td_structural_ann":    (metrics["mgmt_fee_cumul"] + metrics["cost_tx_cumul"]) / n_years,
    "cost_tx_ann":          metrics["cost_tx_cumul"] / n_years,
    "turnover_avg":         turnover_avg,
    "n_titres_avg":         round(n_titres_avg, 1),
    "n_titres_min":         n_titres_min,
    "n_titres_max":         n_titres_max,
    "annual":               annual,
    "td_gross":             td_total,
    "td_gross_ann":         td_ann,
    "selection_params":     {"cap_snts": 0.35, "min_dividende_w": 0.005},
    "td_prog":              [[vr.get("backtest_start"), td_ann]],
    "exec_days_by_rebal":   {},
    "te_t3":                te_ann,
    "td_t3":                td_ann,
    "td_ann_t3":            td_ann,
}

out_bm = os.path.join(DATA_DIR, "backtest_metrics.json")
with open(out_bm, "w", encoding="utf-8") as f:
    json.dump(backtest_metrics, f, ensure_ascii=False, indent=2)
print(f"[OK] backtest_metrics.json -> {out_bm}")
