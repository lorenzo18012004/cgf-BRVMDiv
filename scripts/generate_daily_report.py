"""
generate_daily_report.py — Bulletin quotidien de VL CGF ETFDividende ETF
Usage : python generate_daily_report.py [--date YYYY-MM-DD] [--force]
"""
import os, re, warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether,
)
from base import BaseScript

JOURS_FR = ['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche']
MOIS_FR  = ['janvier','février','mars','avril','mai','juin',
            'juillet','août','septembre','octobre','novembre','décembre']

def _date_fr(s):
    t = pd.Timestamp(s)
    return f"{JOURS_FR[t.weekday()]} {t.day} {MOIS_FR[t.month-1]} {t.year}"

def _dfr(s):
    t = pd.Timestamp(s)
    return f"{t.day:02d}/{t.month:02d}/{t.year}"

# ── palette ─────────────────────────────────────────────────────────
BLACK  = colors.HexColor("#111111")
DKGRAY = colors.HexColor("#444444")
GRAY   = colors.HexColor("#777777")
LGRAY  = colors.HexColor("#f2f2f2")
BORDER = colors.HexColor("#111111")
WHITE  = colors.white
NAVY   = colors.HexColor("#1a3557")
GOLD   = colors.HexColor("#b8922f")
GREEN  = colors.HexColor("#166534")
RED    = colors.HexColor("#991b1b")

# ── couleurs pour graphiques d'allocation ────────────────────────────
SECTOR_COLORS = {
    'Finance':    '#1a3557',
    'Télécoms':   '#b8922f',
    'Énergie':    '#2d6a4f',
    'Agriculture':'#7c4a03',
    'Industries': '#5a5a8a',
}
COUNTRY_COLORS = {
    "Côte d'Ivoire": '#1a3557',
    'Sénégal':       '#b8922f',
    'Burkina Faso':  '#2d6a4f',
    'Bénin':         '#8b0000',
    'Togo':          '#5a5a8a',
    'Mali':          '#7c4a03',
    'Niger':         '#888888',
}

# ── métadonnées fondamentales des 30 titres ETFDividende ──────────────────
# (secteur, pays, nom complet)
TICKER_META = {
    # Télécommunications
    'SNTS':  ('Télécoms',      'Sénégal',        'Sonatel'),
    'ORAC':  ('Télécoms',      "Côte d'Ivoire",  'Orange CI'),
    'ONTBF': ('Télécoms',      'Burkina Faso',   'ONATEL BF'),
    # Finance — banques
    'SGBC':  ('Finance',       "Côte d'Ivoire",  'Société Générale CI'),
    'ECOC':  ('Finance',       "Côte d'Ivoire",  'Ecobank CI'),
    'SIBC':  ('Finance',       "Côte d'Ivoire",  'SIB CI'),
    'STBC':  ('Finance',       "Côte d'Ivoire",  'Stanbic CI'),
    'BOAC':  ('Finance',       "Côte d'Ivoire",  'BOA CI'),
    'CFAC':  ('Finance',       "Côte d'Ivoire",  'CORIS Bank CI'),
    'ETIT':  ('Finance',       'Togo',           'ETI (Ecobank Transnational)'),
    'ORGT':  ('Finance',       'Togo',           'Oragroup Togo'),
    'CBIBF': ('Finance',       'Burkina Faso',   'Coris Bank BF'),
    'BOABF': ('Finance',       'Burkina Faso',   'BOA Burkina Faso'),
    'BICB':  ('Finance',       'Burkina Faso',   'BICI Burkina Faso'),
    'BOAB':  ('Finance',       'Bénin',          'BOA Bénin'),
    'BOAS':  ('Finance',       'Sénégal',        'BOA Sénégal'),
    'BOAM':  ('Finance',       'Mali',           'BOA Mali'),
    'BOAN':  ('Finance',       'Niger',          'BOA Niger'),
    'SDSC':  ('Finance',       'Sénégal',        'Société Générale SN'),
    'NSBC':  ('Finance',       "Côte d'Ivoire",  'NSIA Banque CI'),
    'SIVC':  ('Finance',       "Côte d'Ivoire",  'Erium'),
    'SAFC':  ('Finance',       "Côte d'Ivoire",  'SAFCA CI'),
    # Énergie / Services publics
    'CIEC':  ('Énergie',       "Côte d'Ivoire",  'CIE'),
    'TTLC':  ('Énergie',       "Côte d'Ivoire",  'TotalEnergies CI'),
    'SHEC':  ('Énergie',       "Côte d'Ivoire",  'Shell CI'),
    # Agriculture / Agro-industrie
    'SPHC':  ('Agriculture',   "Côte d'Ivoire",  'SAPH'),
    'SCRC':  ('Agriculture',   "Côte d'Ivoire",  'Sucrivoire'),
    'SOGC':  ('Agriculture',   "Côte d'Ivoire",  'SOGB CI'),
    # Industries & Distribution
    'UNXC':  ('Industries',    "Côte d'Ivoire",  'UNIWAX CI'),
    'STAC':  ('Industries',    "Côte d'Ivoire",  'SETAO CI'),
    'FTSC':  ('Industries',    "Côte d'Ivoire",  'Filtisac CI'),
    'NEIC':  ('Industries',    "Côte d'Ivoire",  'NEI CEDA CI'),
    'SEMC':  ('Industries',    "Côte d'Ivoire",  'Crown Siem CI'),
}


class ReportGenerator(BaseScript):

    def __init__(self):
        super().__init__()
        self.PAGE_W, self.PAGE_H = A4
        self.M = 1.8 * cm
        self.LOGO = os.path.join(self.root_dir, '1780762763961.jpg')

    def _pdfs_dir(self, report_date):
        t = pd.Timestamp(report_date)
        return os.path.join(self.data_dir, 'pdfs', 'journalier',
                            str(t.year), t.strftime('%Y-%m'))

    def _load(self, f):
        p = os.path.join(self.data_dir, f)
        if not os.path.exists(p): return None
        import json; return json.load(open(p, encoding='utf-8'))

    def _get_live_prices(self, nl):
        """
        Cours du jour via le provider actif (data_provider.py).
        Retourne {ticker: {'dernier': float, 'variation': float|None}}.
        La variation est calculée depuis dernier_prix dans nav_latest.json.
        """
        import sys
        sys.path.insert(0, self.scripts_dir)
        try:
            from data_provider import get_provider
            series = get_provider().get_live_prices()
            live = {tk: float(p) for tk, p in series.items()}
        except Exception:
            live = {}

        p0_map = {item["ticker"]: item.get("dernier_prix") for item in nl.get("basket", [])}
        out = {}
        for tk, p1 in live.items():
            p0 = p0_map.get(tk)
            variation = round((p1 / p0 - 1) * 100, 2) if p0 and p0 > 0 else None
            out[tk] = {"dernier": p1, "variation": variation}
        return out

    # ── styles ──────────────────────────────────────────────────────
    def S(self):
        return {
            'h_name': ParagraphStyle('hn', fontName='Helvetica-Bold', fontSize=11,
                      textColor=BLACK, alignment=TA_RIGHT, leading=14),
            'h_sub':  ParagraphStyle('hs', fontName='Helvetica', fontSize=7.5,
                      textColor=DKGRAY, alignment=TA_RIGHT, leading=10),
            'clbl':   ParagraphStyle('cl', fontName='Helvetica', fontSize=6.5,
                      textColor=GRAY, leading=9, spaceBefore=0),
            'clbl_r': ParagraphStyle('clr', fontName='Helvetica', fontSize=6.5,
                      textColor=GRAY, leading=9, alignment=TA_RIGHT),
            'clbl_b': ParagraphStyle('clb', fontName='Helvetica-Bold', fontSize=7,
                      textColor=BLACK, leading=10, spaceBefore=0),
            'cval':   ParagraphStyle('cv', fontName='Helvetica-Bold', fontSize=34,
                      textColor=BLACK, leading=40),
            'mval':   ParagraphStyle('mv', fontName='Helvetica-Bold', fontSize=22,
                      textColor=BLACK, leading=26),
            'sval':   ParagraphStyle('sv', fontName='Helvetica-Bold', fontSize=13,
                      textColor=BLACK, leading=16),
            'csub':   ParagraphStyle('cs', fontName='Helvetica', fontSize=6.5,
                      textColor=GRAY, leading=8.5),
            'body':   ParagraphStyle('b', fontName='Helvetica', fontSize=8,
                      textColor=DKGRAY, leading=11),
            'note':   ParagraphStyle('n', fontName='Helvetica-Oblique', fontSize=6.5,
                      textColor=GRAY, leading=8.5),
            'th':     ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=7.5,
                      textColor=WHITE, alignment=TA_CENTER, leading=10),
            'td':     ParagraphStyle('td', fontName='Helvetica', fontSize=7.5,
                      textColor=BLACK, alignment=TA_CENTER, leading=10),
            'td_pos': ParagraphStyle('tdp', fontName='Helvetica-Bold', fontSize=7.5,
                      textColor=GREEN, alignment=TA_CENTER, leading=10),
            'td_neg': ParagraphStyle('tdn', fontName='Helvetica', fontSize=7.5,
                      textColor=RED, alignment=TA_CENTER, leading=10),
            # tableau détail allocation
            'al_lbl': ParagraphStyle('all', fontName='Helvetica-Bold', fontSize=7.5,
                      textColor=BLACK, leading=10),
            'al_pct': ParagraphStyle('alp', fontName='Helvetica-Bold', fontSize=7.5,
                      textColor=BLACK, alignment=TA_RIGHT, leading=10),
            'al_sub': ParagraphStyle('als', fontName='Helvetica', fontSize=6.5,
                      textColor=GRAY, leading=8),
        }

    @staticmethod
    def _pct(v, dec=2):
        if v is None: return '—'
        return f'{"+" if v>0 else ""}{v:.{dec}f}%'

    def _card_cell(self, lbl, val, sub='', val_size='big'):
        s = self.S()
        vst = s['cval'] if val_size == 'big' else (s['mval'] if val_size == 'med' else s['sval'])
        lines = [Paragraph(lbl, s['clbl']),
                 Spacer(1, 7),
                 Paragraph(str(val), vst)]
        if sub:
            lines += [Spacer(1, 4), Paragraph(sub, s['csub'])]
        return lines

    # ── courbe TE glissante ──────────────────────────────────────────
    def _chart_te_rolling(self, ec, ic, cw_pt, te_target=1.0):
        """TE annualisée calculée de façon incrémentale depuis le lancement."""
        dates = sorted(set(ec.index) & set(ic.index))
        te_pts = {}
        for i, d in enumerate(dates):
            if i < 1: continue
            re_ = ec.loc[:d].pct_change().dropna()
            ri_ = ic.loc[:d].pct_change().dropna()
            cm_ = re_.index.intersection(ri_.index)
            if len(cm_) < 1: continue
            diff = re_.loc[cm_] - ri_.loc[cm_]
            if len(diff) >= 2:
                te_pts[d] = float(diff.std() * np.sqrt(252) * 100)
            else:
                te_pts[d] = float(abs(diff.iloc[0]) * np.sqrt(252) * 100)
        if not te_pts:
            return None
        fig, ax = plt.subplots(figsize=(cw_pt/72, 2.6))
        fig.patch.set_facecolor('white'); ax.set_facecolor('white')
        xs = list(range(len(te_pts)))
        ys = list(te_pts.values())
        ax.plot(xs, ys, color='#1a3557', lw=2.0, marker='o', ms=5)
        ax.axhline(te_target, color='#b8922f', ls='--', lw=1.5,
                   label=f'Plancher cible ≤ {te_target:.1f}%')
        # Zone rouge au-dessus du plancher
        ax.fill_between(xs, ys, te_target,
                        where=[y > te_target for y in ys],
                        color='#991b1b', alpha=0.12)
        ax.fill_between(xs, ys, te_target,
                        where=[y <= te_target for y in ys],
                        color='#166534', alpha=0.10)
        vmin = max(0, min(ys) * 0.6)
        vmax = max(max(ys), te_target) * 1.4
        ax.set_ylim(vmin, vmax)
        labels = [d.strftime('%d/%m') for d in te_pts.keys()]
        ax.set_xticks(xs); ax.set_xticklabels(labels, fontsize=9)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'{v:.2f}%'))
        ax.legend(fontsize=8, framealpha=0, loc='upper right')
        ax.tick_params(colors='#777777', labelsize=8)
        for sp in ax.spines.values(): sp.set_color('#cccccc'); sp.set_linewidth(0.5)
        ax.grid(axis='y', color='#eeeeee', lw=0.5)
        plt.tight_layout(pad=0.4)
        buf = BytesIO(); plt.savefig(buf, format='png', dpi=160, bbox_inches='tight')
        plt.close(); buf.seek(0); return buf

    # ── courbe MDD glissant ──────────────────────────────────────────
    def _chart_mdd_rolling(self, ec, par, cw_pt):
        """Max Drawdown glissant calculé depuis le lancement."""
        if len(ec) < 2:
            return None
        vls     = ec.sort_index()
        cum_max = vls.cummax()
        dd      = (vls - cum_max) / cum_max * 100   # valeurs négatives ou nulles
        fig, ax = plt.subplots(figsize=(cw_pt/72, 2.6))
        fig.patch.set_facecolor('white'); ax.set_facecolor('white')
        xs = list(range(len(dd)))
        ax.fill_between(xs, dd.values, 0, color='#991b1b', alpha=0.18)
        ax.plot(xs, dd.values, color='#991b1b', lw=2.0, marker='o', ms=5)
        ax.axhline(0, color='#444444', lw=0.7)
        vmin = min(dd.values) * 1.4 if min(dd.values) < 0 else -0.1
        ax.set_ylim(vmin, 0.05)
        # Annotation du MDD max
        mdd_val = float(dd.min())
        mdd_idx = int(dd.values.tolist().index(mdd_val))
        if mdd_val < -0.001:
            ax.annotate(f'{mdd_val:.2f}%', xy=(mdd_idx, mdd_val),
                        xytext=(0, -14), textcoords='offset points',
                        fontsize=8.5, color='#991b1b', ha='center', fontweight='bold')
        labels = [d.strftime('%d/%m') for d in dd.index]
        ax.set_xticks(xs); ax.set_xticklabels(labels, fontsize=9)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'{v:.2f}%'))
        ax.tick_params(colors='#777777', labelsize=8)
        for sp in ax.spines.values(): sp.set_color('#cccccc'); sp.set_linewidth(0.5)
        ax.grid(axis='y', color='#eeeeee', lw=0.5)
        plt.tight_layout(pad=0.4)
        buf = BytesIO(); plt.savefig(buf, format='png', dpi=160, bbox_inches='tight')
        plt.close(); buf.seek(0); return buf

    # ── graphiques de performance ────────────────────────────────────
    def _chart_intraday(self, snaps, par, cw_pt):
        fig, ax = plt.subplots(figsize=(cw_pt/72, 2.5))
        fig.patch.set_facecolor('white'); ax.set_facecolor('white')
        times = [s['time'] for s in snaps]
        vls   = [float(s.get('vl_live_fcfa') or s.get('vl_fcfa') or s.get('vl') or 0) for s in snaps]
        xs = list(range(len(times)))
        ax.plot(xs, vls, color='#1a3557', lw=1.8)
        ax.fill_between(xs, vls, min(vls)*0.9994, alpha=0.04, color='#1a3557')
        ax.axhline(par, color='#888888', ls='--', lw=0.8, alpha=0.7)
        vm, vM = min(vls), max(vls)
        ax.annotate(f'{vm:,.0f}', xy=(vls.index(vm), vm), xytext=(0,-13),
                    textcoords='offset points', fontsize=7.5, color='#444444', ha='center')
        ax.annotate(f'{vM:,.0f}', xy=(vls.index(vM), vM), xytext=(0,6),
                    textcoords='offset points', fontsize=7.5, color='#111111', ha='center', fontweight='bold')
        step = max(1, len(times)//8)
        ax.set_xticks(xs[::step]); ax.set_xticklabels(times[::step], fontsize=8)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f'{x:,.0f}'))
        ax.tick_params(colors='#777777', labelsize=8)
        for sp in ax.spines.values(): sp.set_color('#cccccc'); sp.set_linewidth(0.5)
        ax.grid(axis='y', color='#eeeeee', lw=0.5)
        plt.tight_layout(pad=0.3)
        buf = BytesIO(); plt.savefig(buf, format='png', dpi=160, bbox_inches='tight'); plt.close(); buf.seek(0); return buf

    def _chart_intraday_vs_brvm(self, snaps, cw_pt):
        """iNAV vs ETFDividende normalisés base 100 à l'ouverture — comparaison intraday."""
        times = [s['time'] for s in snaps]
        vls   = [float(s.get('vl_live_fcfa') or s.get('vl_fcfa') or s.get('vl') or 0) for s in snaps]
        brvms = [float(s['etfdividende_official']) for s in snaps if s.get('etfdividende_official')]
        if not vls or not brvms or len(brvms) != len(times):
            return None
        base_vl = vls[0] or 1.0
        base_br = brvms[0] or 1.0
        vls_b  = [v / base_vl * 100 for v in vls]
        brvms_b = [b / base_br * 100 for b in brvms]
        xs = list(range(len(times)))

        fig, ax = plt.subplots(figsize=(cw_pt/72, 2.0))
        fig.patch.set_facecolor('white'); ax.set_facecolor('white')
        ax.plot(xs, vls_b,  color='#1a3557', lw=1.8, label='iNAV ETF')
        ax.plot(xs, brvms_b, color='#b8922f', lw=1.5, ls='--', label='ETFDividende')
        ax.axhline(100, color='#cccccc', ls=':', lw=0.8)
        all_v = vls_b + brvms_b
        amp = max(max(all_v) - min(all_v), 0.1)
        ax.set_ylim(min(all_v) - amp * 0.3, max(all_v) + amp * 0.3)
        step = max(1, len(times)//8)
        ax.set_xticks(xs[::step]); ax.set_xticklabels(times[::step], fontsize=8)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f'{x:.2f}'))
        ax.set_ylabel('Base 100', fontsize=7.5, color='#777777')
        ax.legend(fontsize=8, framealpha=0, loc='upper left')
        ax.tick_params(colors='#777777', labelsize=8)
        for sp in ax.spines.values(): sp.set_color('#cccccc'); sp.set_linewidth(0.5)
        ax.grid(axis='y', color='#eeeeee', lw=0.5)
        plt.tight_layout(pad=0.3)
        buf = BytesIO(); plt.savefig(buf, format='png', dpi=160, bbox_inches='tight'); plt.close(); buf.seek(0); return buf

    def _chart_base100(self, ih, launch_date, brvm_h, brvm_al, par, cw_pt, date_max=None):
        fig, ax = plt.subplots(figsize=(cw_pt/72, 3.4))
        fig.patch.set_facecolor('white'); ax.set_facecolor('white')
        lt = pd.Timestamp(launch_date)
        ep, bp = {lt: 100.0}, {}
        if brvm_al: bp[lt] = 100.0
        for d, pts in sorted(ih.items()):
            if date_max and d > date_max: continue
            if not pts or pd.Timestamp(d) < lt: continue
            lp = pts[-1]
            vl = lp.get('vl_fcfa') or lp.get('vl')
            bv = lp.get('etfdividende_official') or brvm_h.get(d)
            if vl: ep[pd.Timestamp(d)] = float(vl)/par*100
            if bv and brvm_al: bp[pd.Timestamp(d)] = float(bv)/brvm_al*100
        es = pd.Series(ep).sort_index(); bs = pd.Series(bp).sort_index()
        xs = list(range(len(es)))
        ax.plot(xs, es.values, color='#1a3557', lw=2.2, marker='o', ms=5, label='CGF ETFDividende ETF')
        if not bs.empty:
            bv_aligned = bs.reindex(es.index)
            ax.plot(xs, bv_aligned.values, color='#b8922f', lw=1.8,
                    ls='--', marker='s', ms=4, label='ETFDividende')
        ax.axhline(100, color='#cccccc', ls=':', lw=0.8)
        # y-axis : padding de ±15% de l'amplitude pour éviter l'aplatissement
        all_vals = list(es.values)
        if not bs.empty: all_vals += [v for v in bs.reindex(es.index).values if not np.isnan(v)]
        v_min, v_max = min(all_vals), max(all_vals)
        amp = max(v_max - v_min, 0.5)
        ax.set_ylim(v_min - amp * 0.35, v_max + amp * 0.35)
        labels = [d.strftime('%d/%m') for d in es.index]
        ax.set_xticks(xs); ax.set_xticklabels(labels, fontsize=9)
        ax.set_ylabel('Base 100', fontsize=7.5, color='#777777')
        ax.tick_params(colors='#777777', labelsize=8)
        ax.legend(fontsize=8.5, framealpha=0, loc='upper left')
        for sp in ax.spines.values(): sp.set_color('#cccccc'); sp.set_linewidth(0.5)
        ax.grid(axis='y', color='#eeeeee', lw=0.5)
        plt.tight_layout(pad=0.3)
        buf = BytesIO(); plt.savefig(buf, format='png', dpi=160, bbox_inches='tight'); plt.close(); buf.seek(0); return buf

    # ── graphiques d'allocation ──────────────────────────────────────
    def _chart_hbar(self, labels, values, fig_w_pt, fig_h_in=2.6, bar_colors=None):
        """Barres horizontales colorées — labels à droite avec %."""
        n = len(labels)
        if bar_colors is None:
            bar_colors = ['#1a3557','#b8922f','#2d6a4f','#8b0000','#5a5a8a','#7c4a03','#888888']
        clrs = [bar_colors[i % len(bar_colors)] for i in range(n)]
        fig, ax = plt.subplots(figsize=(fig_w_pt/72, fig_h_in))
        fig.patch.set_facecolor('white'); ax.set_facecolor('white')
        ys = list(range(n-1, -1, -1))  # inversé : plus grand en haut
        bars = ax.barh(ys, values, height=0.55, color=clrs, edgecolor='white', linewidth=0.4)
        ax.set_yticks(ys)
        ax.set_yticklabels(labels, fontsize=9, color='#111111')
        ax.set_xlim(0, max(values)*1.22)
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + max(values)*0.02, bar.get_y() + bar.get_height()/2,
                    f'{val:.1f}%', va='center', ha='left', fontsize=9,
                    fontweight='bold', color='#111111')
        ax.xaxis.set_visible(False)
        for sp in ['top','right','bottom']: ax.spines[sp].set_visible(False)
        ax.spines['left'].set_color('#cccccc'); ax.spines['left'].set_linewidth(0.5)
        ax.tick_params(left=False, colors='#333333')
        plt.tight_layout(pad=0.5)
        buf = BytesIO(); plt.savefig(buf, format='png', dpi=160, bbox_inches='tight'); plt.close(); buf.seek(0); return buf

    def _chart_top10(self, basket, fig_w_pt):
        """Barres horizontales top 10 titres — dégradé navy vers bleu clair."""
        top = sorted(basket, key=lambda r: r['poids_pct'], reverse=True)[:10]
        labels = [r['ticker'].upper() for r in top]
        values = [r['poids_pct'] for r in top]
        n = len(labels)
        # Dégradé de navy foncé vers bleu-gris clair
        import matplotlib.cm as cm
        cmap = cm.get_cmap('Blues_r')
        clrs = [cmap(0.15 + 0.55 * i / (n-1)) for i in range(n)]
        fig, ax = plt.subplots(figsize=(fig_w_pt/72, 2.6))
        fig.patch.set_facecolor('white'); ax.set_facecolor('white')
        ys = list(range(n-1, -1, -1))
        bars = ax.barh(ys, values, height=0.55, color=clrs, edgecolor='white', linewidth=0)
        ax.set_yticks(ys)
        ax.set_yticklabels(labels, fontsize=8.5, color='#111111', fontweight='bold')
        ax.set_xlim(0, max(values)*1.32)
        for bar, val, r in zip(bars, values, top):
            meta = TICKER_META.get(r['ticker'].upper(), ('', '', r['ticker']))
            nom  = meta[2] if meta[2] != r['ticker'] else ''
            lbl  = f'{val:.1f}%  {nom}' if nom else f'{val:.1f}%'
            ax.text(bar.get_width() + max(values)*0.015, bar.get_y() + bar.get_height()/2,
                    lbl, va='center', ha='left', fontsize=8, color='#333333')
        ax.xaxis.set_visible(False)
        for sp in ['top','right','bottom']: ax.spines[sp].set_visible(False)
        ax.spines['left'].set_color('#cccccc'); ax.spines['left'].set_linewidth(0.5)
        ax.tick_params(left=False)
        plt.tight_layout(pad=0.5)
        buf = BytesIO(); plt.savefig(buf, format='png', dpi=160, bbox_inches='tight'); plt.close(); buf.seek(0); return buf

    def _basket_for_date(self, basket_latest, snap):
        """Recalcule poids réels depuis les prix du snapshot de la date cible."""
        tc = snap.get('ticker_contributions', {})
        if not tc:
            return basket_latest
        # Déduire les quantités depuis nav_latest (pv_mfcfa / dernier_prix)
        qty_map = {}
        for r in basket_latest:
            tk  = r['ticker'].upper()
            pv  = r.get('pv_mfcfa', 0)
            px  = r.get('dernier_prix')
            if pv and px:
                qty_map[tk] = pv * 1e6 / px
        # Recalculer la valeur de marché avec les prix du snapshot
        pvs = {}
        for tk, qty in qty_map.items():
            info = tc.get(tk, {})
            prix = info.get('prix_now')
            if prix:
                pvs[tk] = qty * float(prix)
        total = sum(pvs.values())
        if total == 0:
            return basket_latest
        result = []
        for r in basket_latest:
            tk = r['ticker'].upper()
            if tk in pvs:
                info = tc.get(tk, {})
                result.append({
                    **r,
                    'poids_pct': round(pvs[tk] / total * 100, 4),
                    'pv_mfcfa':  round(pvs[tk] / 1e6, 2),
                    'dernier_prix': info.get('prix_now', r.get('dernier_prix')),
                })
        return result if result else basket_latest

    def _alloc_dicts(self, basket):
        """Agrège poids par secteur et par pays."""
        sec, pays = {}, {}
        for r in basket:
            meta = TICKER_META.get(r['ticker'].upper())
            if not meta: continue
            s_, p_, _ = meta
            sec[s_]   = sec.get(s_, 0) + r['poids_pct']
            pays[p_]  = pays.get(p_, 0) + r['poids_pct']
        sec_sorted  = sorted(sec.items(),  key=lambda x: x[1], reverse=True)
        pays_sorted = sorted(pays.items(), key=lambda x: x[1], reverse=True)
        return sec_sorted, pays_sorted

    # ── construction de cartes ──────────────────────────────────────
    def _cards_row(self, cells_content, col_widths, pad=14):
        t = Table([cells_content], colWidths=col_widths)
        n = len(cells_content)
        ts = [
            ('BOX',           (0,0),(-1,-1), 0.6, BORDER),
            ('LINEBEFORE',    (1,0),(n-1,0), 0.4, BORDER),
            ('BACKGROUND',    (0,0),(-1,-1), WHITE),
            ('VALIGN',        (0,0),(-1,-1), 'TOP'),
            ('TOPPADDING',    (0,0),(-1,-1), pad),
            ('BOTTOMPADDING', (0,0),(-1,-1), pad),
            ('LEFTPADDING',   (0,0),(-1,-1), 14),
            ('RIGHTPADDING',  (0,0),(-1,-1), 14),
        ]
        t.setStyle(TableStyle(ts))
        return t

    def _wrap_card(self, content_list, cw):
        """Enveloppe une liste de flowables dans une carte pleine largeur."""
        t = Table([[content_list]], colWidths=[cw])
        t.setStyle(TableStyle([
            ('BOX',           (0,0),(-1,-1), 0.6, BORDER),
            ('BACKGROUND',    (0,0),(-1,-1), WHITE),
            ('TOPPADDING',    (0,0),(-1,-1), 14),
            ('BOTTOMPADDING', (0,0),(-1,-1), 10),
            ('LEFTPADDING',   (0,0),(-1,-1), 14),
            ('RIGHTPADDING',  (0,0),(-1,-1), 14),
        ]))
        return t

    # ── en-tête ──────────────────────────────────────────────────────
    def _header(self, cw, etf_name, date_str):
        s = self.S()
        logo = Image(self.LOGO, width=3.6*cm, height=1.0*cm, kind='proportional') \
               if os.path.exists(self.LOGO) else Paragraph('CGF', s['h_name'])
        right = [Paragraph(etf_name, s['h_name']), Spacer(1,2),
                 Paragraph(f'Bulletin de valeur liquidative  ·  {date_str}', s['h_sub'])]
        hdr = Table([[logo, right]], colWidths=[4*cm, cw-4*cm])
        hdr.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), colors.HexColor('#f7f7f7')),
            ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0),(-1,-1), 6),
            ('BOTTOMPADDING', (0,0),(-1,-1), 6),
            ('LEFTPADDING',   (0,0),(0,0),   0),
            ('RIGHTPADDING',  (1,0),(1,0),   0),
        ]))
        return [hdr, Spacer(1, 16)]

    # ── génération principale ───────────────────────────────────────
    def generate(self, report_date=None, force=False):
        if report_date is None:
            report_date = datetime.now().strftime('%Y-%m-%d')
        pdfs_dir = self._pdfs_dir(report_date)
        os.makedirs(pdfs_dir, exist_ok=True)
        pdf_path = os.path.join(pdfs_dir, f'rapport_journalier_{report_date}.pdf')
        if os.path.exists(pdf_path) and not force:
            print(f"Existant : {pdf_path}"); return pdf_path

        print("Chargement...")
        nl     = self._load('nav_latest.json')          or {}
        intra  = self._load('intraday_nav.json')         or {}
        ih     = self._load('nav_intraday_history.json') or {}
        launch = self._load('launch_state.json')         or {}

        par         = float(launch.get('par_fcfa', 100000))
        launch_date = launch.get('launch_date', report_date)
        n_parts     = int(launch.get('n_parts', 0))
        etf_name    = nl.get('etf_name', 'CGF ETFDividende ETF')

        snaps = ih.get(report_date) or intra.get('snapshots', [])
        last  = snaps[-1] if snaps else {}

        # VL officielle : nav_latest.json (calc_nav_cloud, prix clôture Sika) si dispo pour ce jour
        # Fallback : dernier snapshot intraday (peut être en cours de séance)
        nl_is_final = nl.get('calc_date') == report_date and nl.get('vl_par_part_fcfa')
        vl     = float(nl['vl_par_part_fcfa']) if nl_is_final else float(last.get('vl_live_fcfa') or last.get('vl_fcfa') or last.get('vl') or par)
        aum    = float(nl['aum_mfcfa']) if nl_is_final else float(last.get('aum_mfcfa') or nl.get('aum_mfcfa') or 0)
        perf_l = nl.get('perf_since_launch') if nl_is_final else last.get('perf_since_launch')
        var_j  = nl.get('change_day_pct') if nl_is_final else (last.get('change_1d_pct') or last.get('change_day_pct'))
        heure  = last.get('time','—')
        n_prix = int(last.get('n_prices') or nl.get('n_live_prices') or 0)

        brvm_h   = self._load('etfdividende_index_history.json') or {}
        brvm_al  = float(launch.get('etfdividende_index_at_launch') or brvm_h.get(launch_date) or 0) or None
        brvm_now = last.get('etfdividende_official')
        if not brvm_now and brvm_h:
            # Ne jamais utiliser une date postérieure au rapport
            past = {d: v for d, v in brvm_h.items() if d <= report_date}
            if past:
                brvm_now = past.get(report_date) or float(past[max(past.keys())])
        perf_idx = (float(brvm_now)/brvm_al - 1)*100 if brvm_now and brvm_al else None

        lt = pd.Timestamp(launch_date)
        ce, ci = {}, {}
        for d, pts in ih.items():
            # Exclure toute date postérieure au rapport
            if d > report_date:
                continue
            if pts and pd.Timestamp(d) >= lt:
                lp = pts[-1]
                v2 = lp.get('vl_fcfa') or lp.get('vl')
                bv = lp.get('etfdividende_official')
                if v2: ce[d] = float(v2)
                if bv: ci[d] = float(bv)
                elif d in brvm_h: ci[d] = float(brvm_h[d])

        te = td = None
        ec = pd.Series({pd.Timestamp(k): v for k,v in ce.items()}).sort_index()
        ic = pd.Series({pd.Timestamp(k): v for k,v in ci.items()}).sort_index()
        nd = len(ec)
        if len(ec) >= 2 and len(ic) >= 2:
            re_ = ec.pct_change().dropna(); ri_ = ic.pct_change().dropna()
            cm_ = re_.index.intersection(ri_.index)
            if len(cm_) >= 1:
                act = re_.loc[cm_] - ri_.loc[cm_]
                te  = float(act.std()*np.sqrt(252)*100) if len(cm_)>=2 else float(abs(act.iloc[0])*np.sqrt(252)*100)
            if brvm_al and not ec.empty and not ic.empty:
                td = (ec.iloc[-1]/par / (ic.iloc[-1]/brvm_al) - 1)*100

        last_r = nl.get('last_rebal_date')
        next_r_str = '—'; days_r = None
        if last_r:
            try:
                from dateutil.relativedelta import relativedelta
                lr = pd.Timestamp(last_r); nr = lr + relativedelta(months=12)
                while nr.weekday() >= 5: nr += pd.Timedelta(days=1)
                next_r_str = _dfr(nr)
                days_r = (nr - pd.Timestamp(report_date).normalize()).days
            except: pass

        print("Cours du jour..."); sika = self._get_live_prices(nl)
        # Basket avec poids recalculés aux prix du jour (pas les arrondis de nav_latest)
        basket = self._basket_for_date(nl.get('basket', []), last)

        print("PDF...")
        s  = self.S()
        cw = self.PAGE_W - 2*self.M


        def _bg(canvas, doc):
            canvas.saveState()
            canvas.setFillColor(colors.HexColor('#f7f7f7'))
            canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
            canvas.restoreState()

        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
            leftMargin=self.M, rightMargin=self.M,
            topMargin=0.8*cm, bottomMargin=0.8*cm,
            title=f'Bulletin VL — {etf_name} — {report_date}',
            author='CGF Gestion')

        story = []

        # ══ PAGE 1 : VL + perf + iNAV ════════════════════════════════
        story += self._header(cw, etf_name, _date_fr(report_date))

        vl_w = cw * 0.55; var_w = cw * 0.45
        story.append(self._cards_row([
            self._card_cell('VALEUR LIQUIDATIVE  ·  CLÔTURE OFFICIELLE',
                            f'{vl:,.0f}', 'FCFA PAR PART', val_size='big'),
            self._card_cell('VARIATION JOURNALIÈRE',
                            self._pct(var_j),
                            f'iNAV {heure} UTC  ·  {n_prix}/{len(basket)} cours', val_size='big'),
        ], [vl_w, var_w], pad=18))
        story.append(Spacer(1, 6))

        te_val  = f'{te:.2f}%'                          if te is not None else '—'
        td_bps  = f'{int(round(td*100)):+d} bps'        if td is not None else '—'
        story.append(self._cards_row([
            self._card_cell('ETF CGF ETFDividende', self._pct(perf_l),
                            f'depuis le {_dfr(launch_date)}', val_size='med'),
            self._card_cell('ETFDividende', self._pct(perf_idx),
                            'indice de cours', val_size='med'),
            self._card_cell('TRACKING ERROR', te_val,
                            f'annualisée  ·  {nd} séance(s)', val_size='med'),
            self._card_cell('ACTIF NET', f'{aum:,.1f} M',
                            f'FCFA  ·  {n_parts:,} parts', val_size='med'),
        ], [cw/4]*4, pad=14))
        story.append(Spacer(1, 6))

        if snaps:
            vls = [float(x.get('vl_live_fcfa') or x.get('vl_fcfa') or x.get('vl') or 0) for x in snaps]
            sub = f'{len(snaps)} valorisations  ·  min {min(vls):,.0f}  –  max {max(vls):,.0f} FCFA'
            buf     = self._chart_intraday(snaps, par, cw - 28)
            buf_vs  = self._chart_intraday_vs_brvm(snaps, cw - 28)
            ch_w = cw - 28
            card_items = [
                Paragraph('iNAV INTRADAY', s['clbl']),
                Spacer(1,3),
                Paragraph(sub, s['csub']),
                Spacer(1,8),
                Image(buf, width=ch_w, height=ch_w*2.5/7.22),
            ]
            if buf_vs:
                card_items += [
                    Spacer(1,10),
                    Paragraph('iNAV ETF vs ETFDividende  —  base 100 à l\'ouverture', s['csub']),
                    Spacer(1,6),
                    Image(buf_vs, width=ch_w, height=ch_w*2.0/7.22),
                ]
            story.append(self._wrap_card(card_items, cw))
        story.append(Spacer(1, 10))

        td_str  = f'TD {td_bps}  ·  ' if td is not None else ''
        reb_str = f'Prochain rebalancement le {next_r_str} ({days_r}j)' if days_r is not None else ''
        brv_str = f'  ·  ETFDividende {float(brvm_now):.2f}' if brvm_now else ''
        story.append(Paragraph(
            f'{n_parts:,} parts  ·  {aum:,.1f} M FCFA actif net  ·  {td_str}{reb_str}{brv_str}',
            s['body']))
        story.append(Spacer(1,6))
        # ══ PAGE 2 : Base100 + Composition ════════════════════════════
        story.append(PageBreak())
        story += self._header(cw, etf_name, _date_fr(report_date))

        buf2 = self._chart_base100(ih, launch_date, brvm_h, brvm_al, par, cw-28, date_max=report_date) if nd>=1 else None
        ch_w = cw - 28
        # figsize hauteur = 3.4 in → height en pt = 3.4 * 72 = 244.8
        story.append(self._wrap_card([
            Paragraph('PERFORMANCE RELATIVE', s['clbl']),
            Spacer(1,3),
            Paragraph(f'Base 100 au {_dfr(launch_date)}  ·  {nd} séance(s)', s['csub']),
            Spacer(1,8),
            Image(buf2, width=ch_w, height=3.4*72) if buf2 else Paragraph('—', s['body']),
        ], cw))
        story.append(Spacer(1,6))

        # ── Courbes TE glissant + MDD glissant (côte à côte) ──────────
        te_target = float(launch.get('te_target_pct', 2.5))
        hw = (cw - 6) / 2
        buf_te  = self._chart_te_rolling(ec, ic, hw - 28, te_target=te_target) if len(ec) >= 2 else None
        buf_mdd = self._chart_mdd_rolling(ec, par, hw - 28) if len(ec) >= 2 else None

        if buf_te or buf_mdd:
            cell_te = [
                Paragraph('TRACKING ERROR GLISSANTE', s['clbl']),
                Spacer(1,3),
                Paragraph(f'Annualisée  ·  plancher cible ≤ {te_target:.1f}%', s['csub']),
                Spacer(1,8),
                Image(buf_te, width=hw-28, height=2.6*72) if buf_te else Paragraph('Données insuffisantes (min. 2 séances)', s['csub']),
            ]
            cell_mdd = [
                Paragraph('MAXIMUM DRAWDOWN GLISSANT', s['clbl']),
                Spacer(1,3),
                Paragraph(f'Pire repli depuis le sommet historique  ·  depuis le lancement', s['csub']),
                Spacer(1,8),
                Image(buf_mdd, width=hw-28, height=2.6*72) if buf_mdd else Paragraph('Données insuffisantes (min. 2 séances)', s['csub']),
            ]
            t_risk = Table([[cell_te, cell_mdd]], colWidths=[hw, hw])
            t_risk.setStyle(TableStyle([
                ('BOX',           (0,0),(-1,-1), 0.6, BORDER),
                ('LINEBEFORE',    (1,0),(1,0),   0.4, BORDER),
                ('BACKGROUND',    (0,0),(-1,-1), WHITE),
                ('VALIGN',        (0,0),(-1,-1), 'TOP'),
                ('TOPPADDING',    (0,0),(-1,-1), 14),
                ('BOTTOMPADDING', (0,0),(-1,-1), 10),
                ('LEFTPADDING',   (0,0),(-1,-1), 14),
                ('RIGHTPADDING',  (0,0),(-1,-1), 14),
            ]))
            story.append(t_risk)
            story.append(Spacer(1,6))

        story.append(Paragraph(
            f'COMPOSITION DU PORTEFEUILLE  ·  {len(basket)} titres  ·  '
            f'NAV {report_date}  ·  AUM {aum:,.1f} M FCFA', s['clbl']))
        story.append(Spacer(1,5))

        cws_t = [cw*x for x in [0.10, 0.08, 0.12, 0.095, 0.12, 0.09, 0.395]]
        hrow  = [Paragraph(h, s['th']) for h in
                 ['Ticker','Poids','Clôture J-1','Var. J','Cours live','Qté','Valeur (M FCFA)']]
        rows  = [hrow]
        for r in basket:
            tk = r['ticker'].upper()
            sk = sika.get(tk, {})
            vj = sk.get('variation') if isinstance(sk, dict) else None
            co = sk.get('dernier')   if isinstance(sk, dict) else None
            _pv = r.get('pv_mfcfa', 0)
            _px = r.get('dernier_prix') or 0
            qt  = round(_pv * 1e6 / _px) if _pv and _px else (r.get('quantite') or r.get('qty') or '—')
            rows.append([
                Paragraph(tk, s['td']),
                Paragraph(f"{r['poids_pct']:.2f}%", s['td']),
                Paragraph(f"{int(r['dernier_prix']):,}" if r.get('dernier_prix') else '—', s['td']),
                Paragraph(f'{vj:+.2f}%' if vj is not None else '—',
                          s['td_pos'] if (vj or 0)>0 else (s['td_neg'] if (vj or 0)<0 else s['td'])),
                Paragraph(f"{int(co):,}" if co else '—', s['td']),
                Paragraph(f"{int(qt):,}" if isinstance(qt,(int,float)) else str(qt), s['td']),
                Paragraph(f"{r['pv_mfcfa']:.2f}", s['td']),
            ])
        sc = [
            ('BACKGROUND',    (0,0),(-1,0),  BLACK),
            ('LINEBELOW',     (0,0),(-1,0),  0.5, colors.HexColor('#555555')),
            ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
            ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0),(-1,-1), 1),
            ('BOTTOMPADDING', (0,0),(-1,-1), 1),
            ('LINEABOVE',     (0,1),(-1,-1), 0.2, colors.HexColor('#dddddd')),
            ('BOX',           (0,0),(-1,-1), 0.6, BORDER),
        ]
        for i in range(1, len(rows)):
            if i % 2 == 0: sc.append(('BACKGROUND', (0,i),(-1,i), LGRAY))
        pt = Table(rows, colWidths=cws_t, repeatRows=1)
        pt.setStyle(TableStyle(sc)); story.append(pt); story.append(Spacer(1,6))

        bv_ = [(r['ticker'].upper(), r['poids_pct'],
                sika.get(r['ticker'].upper(),{}).get('variation'))
               for r in basket
               if isinstance(sika.get(r['ticker'].upper(),{}),dict)
               and sika.get(r['ticker'].upper(),{}).get('variation') is not None]
        if bv_:
            top5 = sorted(bv_, key=lambda x:x[2], reverse=True)[:5]
            bot5 = sorted(bv_, key=lambda x:x[2])[:5]
            hw   = (cw - 6) / 2
            mk_h = lambda t: Paragraph(t, ParagraphStyle('mh', fontName='Helvetica-Bold',
                             fontSize=7.5, textColor=WHITE, alignment=TA_CENTER, leading=10))
            def mk_rows(data, bold):
                r = [[mk_h('Ticker'), mk_h('Poids'), mk_h('Variation')]]
                for tk, pds, vj in data:
                    st = s['td_pos'] if bold else s['td_neg']
                    r.append([Paragraph(tk,s['td']),Paragraph(f'{pds:.2f}%',s['td']),
                               Paragraph(f'{vj:+.2f}%',st)])
                return r
            t_top = Table(mk_rows(top5,True),  colWidths=[hw/3]*3)
            t_bot = Table(mk_rows(bot5,False), colWidths=[hw/3]*3)
            for t in (t_top,t_bot):
                t.setStyle(TableStyle([
                    ('BACKGROUND',(0,0),(-1,0),BLACK),('BOX',(0,0),(-1,-1),0.6,BORDER),
                    ('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                    ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
                    ('LINEABOVE',(0,1),(-1,-1),0.2,colors.HexColor('#dddddd')),
                ]))
            lh = Paragraph('TOP 5 HAUSSES', ParagraphStyle('lh',fontName='Helvetica-Bold',
                           fontSize=7,textColor=BLACK,leading=9,spaceAfter=4))
            lb = Paragraph('TOP 5 BAISSES', ParagraphStyle('lb',fontName='Helvetica-Bold',
                           fontSize=7,textColor=DKGRAY,leading=9,spaceAfter=4))
            movers = Table([[lh,lb],[t_top,t_bot]], colWidths=[hw,hw])
            movers.setStyle(TableStyle([
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
                ('LEFTPADDING',(0,0),(-1,-1),0),
                ('RIGHTPADDING',(0,0),(0,-1),6),('RIGHTPADDING',(1,0),(1,-1),0),
            ]))
            story.append(KeepTogether([
                Paragraph('TOP MOUVEMENTS DU JOUR', s['clbl']),
                Spacer(1,5), movers,
            ]))

        # ══ PAGE 3 : ALLOCATION SECTORIELLE, GÉOGRAPHIQUE, TOP 10 ══════
        story.append(PageBreak())
        story += self._header(cw, etf_name, _date_fr(report_date))

        sec_data, pays_data = self._alloc_dicts(basket)

        # ── Ligne 1 : carte Secteurs (gauche) + carte Pays (droite) ───
        ch_sec  = (cw - 6) * 0.52 - 28   # largeur utile image secteur
        ch_pays = (cw - 6) * 0.48 - 28   # largeur utile image pays
        n_sec   = len(sec_data); n_pays = len(pays_data)

        # Hauteur des graphiques proportionnelle au nombre de catégories
        h_sec  = max(1.8, n_sec  * 0.38)
        h_pays = max(1.8, n_pays * 0.38)
        h_both = max(h_sec, h_pays)       # même hauteur pour les 2 graphiques

        sec_clrs  = [SECTOR_COLORS.get(l, '#888888') for l,_ in sec_data]
        pays_clrs = [COUNTRY_COLORS.get(l, '#888888') for l,_ in pays_data]
        buf_sec  = self._chart_hbar([l for l,_ in sec_data],
                                    [v for _,v in sec_data], ch_sec,
                                    fig_h_in=h_both, bar_colors=sec_clrs)
        buf_pays = self._chart_hbar([l for l,_ in pays_data],
                                    [v for _,v in pays_data], ch_pays,
                                    fig_h_in=h_both, bar_colors=pays_clrs)

        def _alloc_detail_rows(data, s):
            """Tableau texte récap sous le graphique (secteur ou pays)."""
            rows_ = []
            for i, (lbl, val) in enumerate(data):
                bg = LGRAY if i%2==0 else WHITE
                rows_.append((lbl, val, bg))
            return rows_

        # Cellule gauche : Secteurs
        sec_rows = _alloc_detail_rows(sec_data, s)
        sec_tbl_data = [[Paragraph(lbl, s['al_lbl']), Paragraph(f'{val:.1f}%', s['al_pct'])]
                        for lbl, val, _ in sec_rows]
        sec_tbl = Table(sec_tbl_data, colWidths=[ch_sec*0.62, ch_sec*0.38])
        sec_sc  = [('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                   ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),
                   ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
                   ('LINEABOVE',(0,0),(-1,-1),0.2,colors.HexColor('#e0e0e0'))]
        for i,(lbl,val,bg) in enumerate(sec_rows):
            sec_sc.append(('BACKGROUND',(0,i),(-1,i),bg))
        sec_tbl.setStyle(TableStyle(sec_sc))

        cell_sec = [
            Paragraph('RÉPARTITION SECTORIELLE', s['clbl']),
            Spacer(1,4),
            Image(buf_sec, width=ch_sec, height=ch_sec*h_both/(ch_sec/72)),
            Spacer(1,8),
            sec_tbl,
        ]

        # Cellule droite : Pays
        pays_rows = _alloc_detail_rows(pays_data, s)
        pays_tbl_data = [[Paragraph(lbl, s['al_lbl']), Paragraph(f'{val:.1f}%', s['al_pct'])]
                         for lbl, val, _ in pays_rows]
        pays_tbl = Table(pays_tbl_data, colWidths=[ch_pays*0.65, ch_pays*0.35])
        pays_sc  = [('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                    ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),
                    ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
                    ('LINEABOVE',(0,0),(-1,-1),0.2,colors.HexColor('#e0e0e0'))]
        for i,(lbl,val,bg) in enumerate(pays_rows):
            pays_sc.append(('BACKGROUND',(0,i),(-1,i),bg))
        pays_tbl.setStyle(TableStyle(pays_sc))

        cell_pays = [
            Paragraph('RÉPARTITION GÉOGRAPHIQUE', s['clbl']),
            Spacer(1,4),
            Image(buf_pays, width=ch_pays, height=ch_pays*h_both/(ch_pays/72)),
            Spacer(1,8),
            pays_tbl,
        ]

        w_sec  = (cw - 6) * 0.52
        w_pays = (cw - 6) * 0.48
        t_alloc = Table([[cell_sec, cell_pays]], colWidths=[w_sec, w_pays])
        t_alloc.setStyle(TableStyle([
            ('BOX',           (0,0),(-1,-1), 0.6, BORDER),
            ('LINEBEFORE',    (1,0),(1,0),   0.4, BORDER),
            ('BACKGROUND',    (0,0),(-1,-1), WHITE),
            ('VALIGN',        (0,0),(-1,-1), 'TOP'),
            ('TOPPADDING',    (0,0),(-1,-1), 14),
            ('BOTTOMPADDING', (0,0),(-1,-1), 14),
            ('LEFTPADDING',   (0,0),(-1,-1), 14),
            ('RIGHTPADDING',  (0,0),(-1,-1), 14),
        ]))
        story.append(t_alloc)
        story.append(Spacer(1,6))

        # ── Carte : Top 10 titres ──────────────────────────────────────
        ch_t10 = cw - 28
        buf_t10 = self._chart_top10(basket, ch_t10)
        story.append(self._wrap_card([
            Paragraph('TOP 10 POSITIONS', s['clbl']),
            Spacer(1,3),
            Paragraph(f'Poids cumulé top 10 : '
                      f'{sum(r["poids_pct"] for r in sorted(basket, key=lambda x:x["poids_pct"],reverse=True)[:10]):.1f}%  ·  '
                      f'{len(basket)} titres au total', s['csub']),
            Spacer(1,8),
            Image(buf_t10, width=ch_t10, height=ch_t10*2.4/7.22),
        ], cw))
        story.append(Spacer(1,6))

        # ── Carte : Concentration ──────────────────────────────────────
        weights  = sorted([r['poids_pct'] for r in basket], reverse=True)
        top3_w   = sum(weights[:3])
        top5_w   = sum(weights[:5])
        sorted_b = sorted(basket, key=lambda x: x['poids_pct'], reverse=True)
        top3_lbl = '  ·  '.join(r['ticker'].upper() for r in sorted_b[:3])
        top5_lbl = '  ·  '.join(r['ticker'].upper() for r in sorted_b[:5])

        story.append(KeepTogether([
            self._cards_row([
                self._card_cell('CONCENTRATION TOP 3', f'{top3_w:.1f}%', top3_lbl, val_size='small'),
                self._card_cell('CONCENTRATION TOP 5', f'{top5_w:.1f}%', top5_lbl, val_size='small'),
            ], [cw/2, cw/2], pad=14),
            Spacer(1,10),
        ]))

        doc.build(story, onFirstPage=_bg, onLaterPages=_bg)
        print(f'PDF : {pdf_path}')
        return pdf_path

    def run(self):
        import argparse
        p = argparse.ArgumentParser()
        p.add_argument('--date', default=None)
        p.add_argument('--force', action='store_true')
        a = p.parse_args()
        self.generate(report_date=a.date, force=a.force)

if __name__ == '__main__':
    ReportGenerator().run()
