"""
rebalance_live.py
=================
Rebalancement trimestriel automatique du panier live (nav_latest.json).

Détecte si aujourd'hui est le premier jour ouvré d'un trimestre ETFDividende
(janvier / avril / juillet / octobre) et applique les nouveaux poids.

Méthode identique au backtest :
  - Poids cible     : capitalisation totale Sika (nb_titres × prix)
  - Contrainte ADV  : grands titres (>=3%) plafonnés à ADV × 40j / AUM
                      petits titres (< 3%) plafonnés à ADV × 20j / AUM
  - Excès redistribué proportionnellement aux non-plafonnés
  - Titres sans ADV mesurable ou poids < 0.1% : exclus

Sorties :
  - data/nav_latest.json     mis à jour (nouveau basket + coûts de tx appliqués)
  - data/dashboard_data.json mis à jour (w_history + rebal_dates)
  - data/rebal_detail.json   mis à jour (nouvelle entrée de rebalancement)
  - stdout                   ordres d'achat / vente

Usage :
  python scripts/rebalance_live.py              # auto-détecte + dry-run si c'est le jour J
  python scripts/rebalance_live.py --dry-run    # calcule les ordres sans rien écrire (défaut en CI)
  python scripts/rebalance_live.py --apply      # applique vraiment le rebalancement
  python scripts/rebalance_live.py --force      # force même si ce n'est pas le jour J
  python scripts/rebalance_live.py --date 2026-07-01  # simule à une date précise

Sécurité :
  Sans --apply, le script ne modifie AUCUN fichier.
  Le workflow quotidien tourne toujours en dry-run (prévisualisation).
  Pour appliquer, déclencher manuellement le workflow "Appliquer rebalancement"
  depuis GitHub Actions → onglet Actions → "Appliquer rebalancement trimestriel".
"""
import sys, os, json, argparse, calendar
from datetime import date as date_cls
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, 'data')

NL_PATH  = os.path.join(DATA, 'nav_latest.json')
SH_PATH  = os.path.join(DATA, 'sika_history.json')
SOC_PATH = os.path.join(DATA, 'sika_societe.json')
BCH_PATH = os.path.join(DATA, 'brvm_composition_history.json')
DD_PATH  = os.path.join(DATA, 'dashboard_data.json')
RD_PATH  = os.path.join(DATA, 'rebal_detail.json')

# ── Paramètres ────────────────────────────────────────────────────────────────
MAX_EXEC_LARGE   = 40      # jours de bourse pour grands titres (>= 3% ETFDividende) — ≈2 mois, fini avant le T+1
MAX_EXEC_SMALL   = 20      # jours de bourse pour petits titres (< 3% ETFDividende) — ≈1 mois
LARGE_THRESHOLD  = 0.03
PARTICIPATION_RATE = 0.15  # max 15% de l'ADV quotidien (screen + OTC petits blocs)
MIN_ADV_MFCFA    = 0.5
MIN_WEIGHT       = 0.001
FORCE_TOP_N      = 5       # top 5 titres ETFDividende tenus à leur poids exact (OTC)
CASH_BUFFER      = 0.01   # poche de liquidité : 1% du NAV en cash


def spread_one_way(adv_mfcfa):
    """Spread bid-ask one-way selon la liquidité du titre."""
    if adv_mfcfa >= 100: return 0.0025
    if adv_mfcfa >=  30: return 0.0040
    if adv_mfcfa >=  10: return 0.0080
    if adv_mfcfa >=   5: return 0.0125
    return 0.0175

# ── Détection date de rebalancement ──────────────────────────────────────────
REBAL_MONTHS = {1, 4, 7, 10}   # trimestres ETFDividende

def is_rebal_day(date_str, tolerance_days = 3):
    """
    Retourne True si date_str est le 1er jour ouvré d'un mois de rebalancement,
    avec une tolérance de ±tolerance_days jours (au cas où le script tourne en retard).
    """
    dt = pd.Timestamp(date_str)
    if dt.month not in REBAL_MONTHS:
        return False
    # Premier jour du mois, cherche le 1er jour ouvré
    first = pd.Timestamp(dt.year, dt.month, 1)
    first_bday = first + pd.offsets.BDay(0)
    delta = abs((dt - first_bday).days)
    return delta <= tolerance_days

def next_rebal_date(from_date):
    dt = pd.Timestamp(from_date)
    for months_ahead in range(1, 5):
        candidate_month = ((dt.month - 1 + months_ahead) % 12) + 1
        candidate_year  = dt.year + ((dt.month - 1 + months_ahead) // 12)
        if candidate_month in REBAL_MONTHS:
            first = pd.Timestamp(candidate_year, candidate_month, 1)
            return (first + pd.offsets.BDay(0)).strftime('%Y-%m-%d')
    return ''

# ── Helpers Sika ─────────────────────────────────────────────────────────────
def last_price(sh, ticker, as_of_date):
    hist = sh.get(ticker, {})
    past = sorted(d for d in hist if d <= as_of_date)
    if past:
        p = hist[past[-1]]
        close = p.get('close') if isinstance(p, dict) else p
        if close and float(close) > 0:
            return float(close)
    return None

def _prev_quarter_range(as_of_date):
    """Retourne (start, end) du trimestre calendaire précédent (format YYYY-MM-DD)."""
    d = date_cls.fromisoformat(as_of_date)
    q = (d.month - 1) // 3   # trimestre courant : 0=Q1, 1=Q2, 2=Q3, 3=Q4
    if q == 0:
        start = date_cls(d.year - 1, 10, 1)
        end   = date_cls(d.year - 1, 12, 31)
    else:
        sm = (q - 1) * 3 + 1
        em = q * 3
        start = date_cls(d.year, sm, 1)
        end   = date_cls(d.year, em, calendar.monthrange(d.year, em)[1])
    return start.isoformat(), end.isoformat()

def compute_adv(sh, ticker, as_of_date):
    q_start, q_end = _prev_quarter_range(as_of_date)
    hist  = sh.get(ticker, {})
    dates = [d for d in hist if q_start <= d <= q_end]
    vals  = [(hist[d].get('volume') or 0) * (hist[d].get('close') or 0) / 1e6
             for d in dates]
    return float(sum(vals) / len(dates)) if dates else 0.0

def compute_stale(sh, ticker, as_of_date):
    q_start, q_end = _prev_quarter_range(as_of_date)
    hist  = sh.get(ticker, {})
    dates = [d for d in hist if q_start <= d <= q_end]
    if not dates:
        return 1.0
    return sum(1 for d in dates if (hist[d].get('volume') or 0) == 0) / len(dates)

# ── Calcul des poids total cap Sika ──────────────────────────────────────────
def get_total_cap_weights(tickers, rebal_date, sh, soc):
    market_cap = {}
    missing = []
    for tk in tickers:
        nb   = soc.get(tk, {}).get('nb_titres')
        prix = last_price(sh, tk, rebal_date)
        if nb and prix:
            market_cap[tk] = nb * prix
        else:
            missing.append(tk)
    if missing and market_cap:
        avg = sum(market_cap.values()) / len(market_cap)
        for tk in missing:
            market_cap[tk] = avg
    total = sum(market_cap.values())
    if total <= 0:
        return {tk: 1 / len(tickers) for tk in tickers}
    return {tk: market_cap[tk] / total for tk in tickers}

# ── Stratégie : top-5 OTC (plein poids indice) + CAP ADV pour les autres ──────
def build_adv_capped_weights(w_etfdividende, rebal_date, aum_mfcfa, sh, old_basket=None):
    """
    Top FORCE_TOP_N par poids indice → OTC (tient le plein poids indice, bloc négocié).
    Autres titres → si le delta dépasse la capacité screen (15% ADV × 40j/20j) → CAP
                    (poids réduit à ce qu'on peut acheter/vendre sur screen).
    Exclusion uniquement si ADV < MIN_ADV_MFCFA ou poids résiduel < MIN_WEIGHT.
    Retourne (final_weights, exclu_info, otc_set).
    """
    if old_basket is None:
        old_basket = {}

    total_etfdividende = sum(w_etfdividende.values()) or 1.0
    w_norm = {tk: v / total_etfdividende for tk, v in w_etfdividende.items()}
    adv    = {tk: compute_adv(sh, tk, rebal_date) for tk in w_norm}

    exclu_info = {tk: f'ADV {adv[tk]:.1f} MFCFA < {MIN_ADV_MFCFA}'
                  for tk in w_norm if adv[tk] < MIN_ADV_MFCFA}
    eligible = [tk for tk in w_norm if adv[tk] >= MIN_ADV_MFCFA]

    if not eligible:
        return {}, exclu_info, set()

    total_elig = sum(w_norm[tk] for tk in eligible) or 1.0
    w_target   = {tk: w_norm[tk] / total_elig for tk in eligible}

    # Top FORCE_TOP_N par poids indice → OTC (bloc négocié, poids indice exact)
    sorted_by_w = sorted(eligible, key=lambda tk: -w_target[tk])
    otc_set = set(sorted_by_w[:FORCE_TOP_N])

    # Poids initiaux = poids indice pour tous
    weights = {tk: w_target[tk] for tk in eligible}

    # Redistribution itérative : excédent des capés → non-capés non-top5 uniquement
    for _ in range(30):
        capped_w  = {}
        uncapped  = []
        for tk in eligible:
            if tk in otc_set:
                continue
            w_cur     = old_basket.get(tk, 0.0)
            delta     = weights[tk] - w_cur
            max_d     = MAX_EXEC_LARGE if w_norm[tk] >= LARGE_THRESHOLD else MAX_EXEC_SMALL
            max_delta = PARTICIPATION_RATE * adv[tk] * max_d / aum_mfcfa
            if abs(delta) > max_delta + 1e-6:
                capped_w[tk] = max(0.0, w_cur + (max_delta if delta > 0 else -max_delta))
            else:
                uncapped.append(tk)

        if not capped_w:
            break  # Plus aucun cap → convergé

        # Fixer les capés, redistribuer le reste aux non-capés proportionnellement
        total_top5    = sum(w_target[tk] for tk in otc_set if tk in weights)
        total_capped  = sum(capped_w[tk]  for tk in capped_w)
        avail         = 1.0 - total_top5 - total_capped

        for tk in capped_w:
            weights[tk] = capped_w[tk]

        uncapped_tgt = sum(w_target[tk] for tk in uncapped) or 1.0
        for tk in uncapped:
            weights[tk] = max(0.0, avail * w_target[tk] / uncapped_tgt)

        # Top-5 restent exactement à leur poids indice
        for tk in otc_set:
            if tk in weights:
                weights[tk] = w_target[tk]

    # Exclure les poids résiduels trop faibles (non-top5 uniquement)
    for _ in range(5):
        tiny = [tk for tk in eligible if tk not in otc_set
                and 0 < weights.get(tk, 0) < MIN_WEIGHT]
        if not tiny:
            break
        for tk in tiny:
            exclu_info[tk] = f'Poids < {MIN_WEIGHT*100:.1f}%'
            eligible.remove(tk)
        if not eligible:
            break
        # Recalcul après exclusion
        total_keep = sum(weights[tk] for tk in eligible) or 1.0
        weights = {tk: weights[tk] / total_keep for tk in eligible}
        for tk in otc_set:
            if tk in weights:
                weights[tk] = w_target[tk]

    final = {tk: round(weights[tk], 6) for tk in eligible if weights.get(tk, 0) > 0}
    # Normalisation finale : top-5 exacts, le reste ajusté
    top5_total = sum(final[tk] for tk in otc_set if tk in final)
    rest_total = sum(final[tk] for tk in final if tk not in otc_set)
    if rest_total > 0:
        scale = (1.0 - top5_total) / rest_total
        final = {tk: (round(v, 6) if tk in otc_set else round(v * scale, 6))
                 for tk, v in final.items()}

    return final, exclu_info, otc_set


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply',    action='store_true',
                        help='Applique vraiment le rebalancement (modifie les fichiers)')
    parser.add_argument('--force',    action='store_true',
                        help='Ignore la vérification de date')
    parser.add_argument('--dry-run',  action='store_true', dest='dry_run',
                        help='Calcule les ordres sans rien écrire (comportement par défaut)')
    parser.add_argument('--date',     default=None,
                        help='Date du rebalancement (YYYY-MM-DD), défaut = aujourd\'hui')
    args = parser.parse_args()

    # Sans --apply, on est toujours en dry-run
    dry_run = not args.apply

    today = args.date or pd.Timestamp.now().strftime('%Y-%m-%d')

    # ── Vérification date ──────────────────────────────────────────────────────
    if not args.force and not is_rebal_day(today):
        print(f"[SKIP] {today} n'est pas une date de rebalancement ETFDividende.")
        print(f"       Prochain rebal estimé : {next_rebal_date(today)}")
        print("       Pour simuler : --force   Pour appliquer : --force --apply")
        sys.exit(0)

    mode = "DRY-RUN (prévisualisation)" if dry_run else "APPLICATION RÉELLE"
    print(f"=== REBALANCEMENT ETFDividende ETF — {today} [{mode}] ===")
    print()

    # ── Chargement ────────────────────────────────────────────────────────────
    sh  = json.load(open(SH_PATH,  encoding='utf-8'))
    soc = json.load(open(SOC_PATH, encoding='utf-8'))
    nl  = json.load(open(NL_PATH,  encoding='utf-8'))
    dd  = json.load(open(DD_PATH,  encoding='utf-8'))
    rd  = json.load(open(RD_PATH,  encoding='utf-8'))
    bch = json.load(open(BCH_PATH, encoding='utf-8'))

    aum_mfcfa = float(nl.get('aum_mfcfa', 5000))
    last_rebal = nl.get('last_rebal_date', '2026-04-01')

    # Vérifier qu'on ne rebalance pas deux fois la même date (sauf dry-run)
    if today <= last_rebal and not args.force and not dry_run:
        print(f"[SKIP] Dernier rebal : {last_rebal} — déjà à jour.")
        sys.exit(0)

    # ── Composition ETFDividende ────────────────────────────────────────────────────
    # Prendre la dernière composition connue avant ou égale à today
    comp_entries = [c for c in bch if c.get('rebal_date') and
                    len(c.get('composition', [])) >= 25 and
                    c['rebal_date'] <= today]

    if comp_entries:
        latest_comp = max(comp_entries, key=lambda c: c['rebal_date'])
        tickers = [t.upper() for t in latest_comp['composition']]
        index_entries = {t.upper() for t in latest_comp.get('entries', [])}
        index_exits   = {t.upper() for t in latest_comp.get('exits', [])}
        print(f"[1/5] Composition : {len(tickers)} titres (PDF du {latest_comp['rebal_date']})")
    else:
        # Fallback : composition du dernier rebal en portefeuille
        tickers = [item['ticker'] for item in nl.get('basket', [])]
        index_entries = set()
        index_exits   = set()
        print(f"[1/5] Composition : {len(tickers)} titres (basket actuel — pas de PDF récent)")

    # ── Poids total cap Sika ──────────────────────────────────────────────────
    print("[2/5] Calcul des poids total cap Sika…")
    w_etfdividende = get_total_cap_weights(tickers, today, sh, soc)

    # ── Stratégie hybride OTC + ADV-cap ──────────────────────────────────────
    print(f"[3/5] Poids cibles indice + détection OTC par delta d'ordre…")
    old_basket_w = {item['ticker']: item['poids_pct'] / 100 for item in nl.get('basket', [])}
    new_basket_w, exclu_info, forced_tks = build_adv_capped_weights(w_etfdividende, today, aum_mfcfa, sh, old_basket_w)

    print(f"   Panier final : {len(new_basket_w)} titres | {len(exclu_info)} exclus | {len(forced_tks)} OTC requis")
    for tk, raison in sorted(exclu_info.items()):
        print(f"   EXCLU {tk} : {raison}")

    # ── Ordres d'achat / vente ────────────────────────────────────────────────
    print()
    print("[4/5] Ordres de rebalancement…")
    old_basket = {item['ticker']: item['poids_pct'] / 100
                  for item in nl.get('basket', [])}

    all_tickers = sorted(set(old_basket) | set(new_basket_w))
    orders = []
    turnover = 0.0

    for tk in all_tickers:
        w_old = old_basket.get(tk, 0.0)
        w_new = new_basket_w.get(tk, 0.0)
        delta = w_new - w_old
        if abs(delta) < 0.0001:
            continue
        montant_mfcfa = abs(delta) * aum_mfcfa
        sens  = 'ACHETER' if delta > 0 else 'VENDRE'
        adv      = compute_adv(sh, tk, today)
        w_b30    = w_etfdividende.get(tk, 0.0)
        days_raw = (montant_mfcfa / adv / PARTICIPATION_RATE) if adv > 0 else 999.0
        max_days = MAX_EXEC_LARGE if w_b30 >= LARGE_THRESHOLD else MAX_EXEC_SMALL
        is_full_exit = (w_new == 0.0)  # sortant : liquider à 0%, pas de cap
        days_exec = days_raw if is_full_exit else min(days_raw, max_days)
        orders.append({
            'ticker':       tk,
            'sens':         sens,
            'delta_pct':    round(delta * 100, 2),
            'montant_mfcfa':round(montant_mfcfa, 1),
            'w_old_pct':    round(w_old * 100, 2),
            'w_new_pct':    round(w_new * 100, 2),
            'w_etfdividende_pct': round(w_b30 * 100, 2),
            'adv_mfcfa':    round(adv, 1),
            'days_exec':    round(days_exec, 1),
            'days_exec_raw':round(days_raw, 1),  # valeur brute conservée pour info
            'otc':          tk in forced_tks and days_raw > max_days,
            'capped':       tk not in forced_tks and w_new < w_b30 - 1e-4,
        })
        turnover += abs(delta)

    turnover /= 2   # one-way turnover
    # Coût variable : spread selon ADV de chaque titre
    cost_pct = sum(
        abs(new_basket_w.get(tk, 0) - old_basket.get(tk, 0)) *
        spread_one_way(compute_adv(sh, tk, today))
        for tk in all_tickers
    )
    cash_mfcfa = aum_mfcfa * CASH_BUFFER
    print(f"   Poche de liquidité : {CASH_BUFFER*100:.0f}% = {cash_mfcfa:.0f} MFCFA en cash")
    print(f"   AUM investi (panier) : {(1-CASH_BUFFER)*100:.0f}% = {aum_mfcfa*(1-CASH_BUFFER):.0f} MFCFA")
    print(f"   Turnover one-way : {turnover*100:.1f}%")
    print(f"   Coût de transaction (spread variable) : {cost_pct*100:.3f}% de l'AUM")
    print()
    HDR = f"   {'Ticker':<8} {'Sens':<8} {'Delta':>7} {'Montant':>11} {'Ancien':>7} {'Nouveau':>7} {'Indice':>7} {'ADV':>7} {'Jours':>6}  Flags"
    SEP = f"   {'-'*87}"

    def _print_order(o):
        flags = []
        if o['otc']:    flags.append('OTC')
        if o['capped']: flags.append('CAP')
        print(f"   {o['ticker']:<8} {o['sens']:<8} {o['delta_pct']:>+6.2f}%"
              f" {o['montant_mfcfa']:>9.1f} M"
              f" {o['w_old_pct']:>6.2f}%"
              f" {o['w_new_pct']:>6.2f}%"
              f" {o['w_etfdividende_pct']:>6.2f}%"
              f" {o['adv_mfcfa']:>6.1f} M"
              f" {o['days_exec']:>5.1f}j"
              f"  {' '.join(flags)}")

    # Classer par rapport à l'indice officiel (entries/exits du PDF BRVM)
    entrants  = [o for o in orders if o['ticker'] in index_entries and o['w_new_pct'] > 0]
    sortants  = [o for o in orders if o['ticker'] in index_exits or o['w_new_pct'] == 0]
    ajusts    = [o for o in orders if o['ticker'] not in index_entries and o['ticker'] not in index_exits and o['w_new_pct'] > 0]

    # Ajouter le champ section pour le dashboard
    for o in entrants: o['section'] = 'Entrant'
    for o in ajusts:   o['section'] = 'Ajustement'
    for o in sortants: o['section'] = 'Sortant'

    if entrants:
        print(f"\n   ── Entrants dans l'indice ({len(entrants)}) ──────────────────────────────────")
        print(HDR); print(SEP)
        for o in sorted(entrants, key=lambda x: -x['delta_pct']):
            _print_order(o)

    if ajusts:
        print(f"\n   ── Ajustements du panier ({len(ajusts)}) ──────────────────────────────────")
        print(HDR); print(SEP)
        for o in sorted(ajusts, key=lambda x: -abs(x['delta_pct'])):
            _print_order(o)

    if sortants:
        print(f"\n   ── Sortants de l'indice à liquider ({len(sortants)}) ───────────────────────")
        print(HDR); print(SEP)
        for o in sorted(sortants, key=lambda x: x['delta_pct']):
            _print_order(o)

    # ── Calcul NAV après coûts ────────────────────────────────────────────────
    nav_before = float(nl.get('nav_indice', 0))
    nav_after  = nav_before * (1 - cost_pct)

    # ── Résumé dry-run ────────────────────────────────────────────────────────
    if dry_run:
        print()
        print("=" * 70)
        print("  [DRY-RUN] AUCUN FICHIER MODIFIÉ")
        print(f"  Panier projeté   : {len(new_basket_w)} titres  |  {len(exclu_info)} exclus")
        print(f"  Turnover one-way : {turnover*100:.1f}%")
        print(f"  Coût transaction : {cost_pct*100:.3f}%")
        print(f"  NAV projetée     : {nav_before:.4f} → {nav_after:.4f}")

        # Titres plafonnés (w_etf < w_etfdividende)
        capped_list = [(tk, w_etfdividende[tk]*100, new_basket_w[tk]*100)
                       for tk in new_basket_w if tk not in forced_tks
                       and new_basket_w[tk] < w_etfdividende.get(tk, 0) - 1e-4]
        if capped_list:
            print(f"\n  Titres plafonnés par ADV ({len(capped_list)}) :")
            for tk, w_idx, w_etf in sorted(capped_list, key=lambda x: -(x[1]-x[2])):
                print(f"    {tk:<8} indice {w_idx:.2f}% → ETF {w_etf:.2f}%  (écart {w_idx-w_etf:+.2f}%)")

        if exclu_info:
            print(f"\n  Exclus ({len(exclu_info)}) :")
            for tk, raison in exclu_info.items():
                print(f"    {tk:<8} {w_etfdividende.get(tk,0)*100:.2f}% — {raison}")

        otc_orders = [o['ticker'] for o in orders if o['otc']]
        if otc_orders:
            print(f"\n  Ordres nécessitant OTC ({len(otc_orders)}) : {', '.join(otc_orders)}")
        print()
        print("  Pour appliquer : Dashboard → onglet REBALANCER → Étape 2")
        print("=" * 70)
        # Bloc JSON parsé par le dashboard pour affichage coloré
        import json as _json
        print("### JSON_ORDERS ###")
        print(_json.dumps(orders, ensure_ascii=False))
        return

    # ── Application réelle : écriture des fichiers ────────────────────────────
    print()
    print("[5/5] Application du rebalancement…")

    new_basket = []
    for tk, w in sorted(new_basket_w.items(), key=lambda x: -x[1]):
        prix  = last_price(sh, tk, today)
        stale = compute_stale(sh, tk, today) > 0.5
        adv   = compute_adv(sh, tk, today)
        new_basket.append({
            'ticker':       tk,
            'poids_pct':    round(w * 100, 4),
            'pv_mfcfa':     round(w * aum_mfcfa * (1 - CASH_BUFFER) * (1 - cost_pct), 1),
            'dernier_prix': prix,
            'prix_stale':   stale,
            'adv_mfcfa':    round(adv, 1),
            'w_etfdividende':     round(w_etfdividende.get(tk, 0), 6),
            'force_otc':    tk in forced_tks,
        })

    nl['basket']           = new_basket
    nl['n_basket']         = len(new_basket)
    nl['last_rebal_date']  = today
    nl['nav_indice']       = round(nav_after, 4)
    nl['aum_mfcfa']        = round(nav_after / nav_before * aum_mfcfa, 1) if nav_before > 0 else aum_mfcfa
    nl['cash_buffer_pct']  = CASH_BUFFER * 100

    json.dump(nl, open(NL_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f"   nav_latest.json    : {len(new_basket)} titres | NAV {nav_before:.4f} → {nav_after:.4f}")

    dd.setdefault('w_history', {})[today] = new_basket_w
    json.dump(dd, open(DD_PATH, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f"   dashboard_data.json: w_history[{today}] ajouté")

    from datetime import datetime as _dt
    new_rebal_entry = {
        'date':       today,
        'date_label': _dt.strptime(today, '%Y-%m-%d').strftime('%d %b. %Y'),
        'skipped':    False,
        'basket_n': len(new_basket),
        'excl_n':   len(exclu_info),
        'coverage': round(sum(w_etfdividende.get(tk, 0) for tk in new_basket_w), 4),
        'excl_w':   round(sum(w_etfdividende.get(tk, 0) for tk in exclu_info), 4),
        'turnover': round(turnover, 4),
        'cost_tx':  round(cost_pct, 6),
        'cost_bps': round(cost_pct * 10000, 2),
        'cost_pct': round(cost_pct * 100, 4),
        'basket': [
            {
                'ticker':       tk,
                'w_etf':        round(w, 6),
                'w_etfdividende':     round(w_etfdividende.get(tk, 0), 6),
                'adv_mfcfa':    round(compute_adv(sh, tk, today), 1),
                'stale_ratio':  round(compute_stale(sh, tk, today), 3),
                'force':        tk in forced_tks,
                'force_otc':    tk in forced_tks,
                'trade_mfcfa':  round(
                    next((o['montant_mfcfa'] * (1 if o['sens'] == 'ACHETER' else -1)
                          for o in orders if o['ticker'] == tk), 0.0), 1),
                'days_exec':    round(
                    next((o['days_exec'] for o in orders if o['ticker'] == tk), 0.0), 1),
                'delta':        round(
                    next((o['delta_pct'] / 100 for o in orders if o['ticker'] == tk), 0.0), 6),
            }
            for tk, w in new_basket_w.items()
        ],
        'excluded': [
            {
                'ticker':      tk,
                'w_etfdividende':    round(w_etfdividende.get(tk, 0), 6),
                'raison':      raison,
                'adv_mfcfa':   round(compute_adv(sh, tk, today), 1),
                'stale_ratio': round(compute_stale(sh, tk, today), 3),
            }
            for tk, raison in exclu_info.items()
        ],
        'orders': orders,
    }

    rebals = [r for r in rd.get('rebalancings', []) if r.get('date') != today]
    rebals.append(new_rebal_entry)
    rebals.sort(key=lambda r: r['date'])
    rd['rebalancings'] = rebals
    json.dump(rd, open(RD_PATH, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f"   rebal_detail.json  : entrée {today} ajoutée")

    # Marquer rebal_pending.json comme appliqué
    from datetime import datetime as _dt2, timezone as _tz
    PENDING_PATH = os.path.join(DATA, 'rebal_pending.json')
    if os.path.exists(PENDING_PATH):
        pending = _json.load(open(PENDING_PATH, encoding='utf-8'))
        pending['status']     = 'applied'
        pending['applied_at'] = _dt2.now(_tz.utc).strftime('%Y-%m-%d %H:%M UTC')
        _json.dump(pending, open(PENDING_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f"   rebal_pending.json : marqué 'applied'")

    print()
    print("=== REBALANCEMENT APPLIQUÉ ===")
    print(f"   Panier : {len(new_basket)} titres")
    print(f"   Turnover one-way : {turnover*100:.1f}%")
    print(f"   Coût de transaction : {cost_pct*100:.3f}%")
    print(f"   NAV après coûts : {nav_after:.4f}")


if __name__ == '__main__':
    main()
