"""
generate_periodic_reports.py — Rapports semestriel et annuel CGF ETFDividende ETF
Usage :
  python generate_periodic_reports.py --period semiannual --year 2026 --semester 1 [--force]
  python generate_periodic_reports.py --period annual     --year 2026               [--force]
"""
import os, warnings
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
    Image, HRFlowable, PageBreak, KeepTogether,
)
from base import BaseScript
from generate_daily_report import (
    TICKER_META, SECTOR_COLORS, COUNTRY_COLORS,
    BLACK, DKGRAY, GRAY, LGRAY, BORDER, WHITE, NAVY, GOLD, GREEN, RED,
    _dfr, MOIS_FR,
)

MOIS_CAPS = [m.capitalize() for m in MOIS_FR]


class PeriodicReportGenerator(BaseScript):

    def __init__(self):
        super().__init__()
        self.PAGE_W, self.PAGE_H = A4
        self.M = 1.8 * cm
        self.LOGO = os.path.join(self.root_dir, '1780762763961.jpg')

    def _load(self, f):
        p = os.path.join(self.data_dir, f)
        if not os.path.exists(p): return None
        import json; return json.load(open(p, encoding='utf-8'))

    # ── collecte des données sur une période ────────────────────────
    def _period_rows(self, date_from, date_to):
        """Liste de dicts {date, vl, etfdividende, aum} pour chaque séance entre date_from et date_to."""
        ih     = self._load('nav_intraday_history.json') or {}
        brvm_h = self._load('etfdividende_index_history.json') or {}
        launch = self._load('launch_state.json') or {}
        par    = float(launch.get('par_fcfa', 100000))
        rows   = []
        for d, snaps in sorted(ih.items()):
            if d < date_from or d > date_to or not snaps:
                continue
            lp  = snaps[-1]
            vl  = float(lp.get('vl_live_fcfa') or lp.get('vl_fcfa') or lp.get('vl') or par)
            bv  = float(lp.get('etfdividende_official') or brvm_h.get(d) or 0) or None
            aum = float(lp.get('aum_mfcfa') or 0)
            rows.append({'date': d, 'vl': vl, 'etfdividende': bv, 'aum': aum})
        return rows

    def _monthly_summary(self, rows):
        """Agrège les données par mois : {YYYY-MM: {vl_start, vl_end, bv_start, bv_end, perf_etf, perf_brvm}}"""
        by_month = {}
        for r in rows:
            ym = r['date'][:7]
            if ym not in by_month:
                by_month[ym] = []
            by_month[ym].append(r)
        summary = {}
        for ym, mrs in sorted(by_month.items()):
            vs, ve = mrs[0]['vl'],  mrs[-1]['vl']
            bs, be = mrs[0]['etfdividende'], mrs[-1]['etfdividende']
            summary[ym] = {
                'vl_start': vs, 'vl_end': ve,
                'bv_start': bs, 'bv_end': be,
                'perf_etf':  (ve / vs - 1) * 100 if vs else None,
                'perf_brvm': (be / bs - 1) * 100 if bs and be else None,
                'n_seances': len(mrs),
                'aum_end':   mrs[-1]['aum'],
            }
        return summary

    # ── styles ───────────────────────────────────────────────────────
    def S(self):
        return {
            'h_name': ParagraphStyle('hn', fontName='Helvetica-Bold', fontSize=11,
                      textColor=WHITE, alignment=TA_RIGHT, leading=14),
            'h_sub':  ParagraphStyle('hs', fontName='Helvetica', fontSize=7.5,
                      textColor=colors.HexColor('#bbbbbb'), alignment=TA_RIGHT, leading=10),
            'clbl':   ParagraphStyle('cl', fontName='Helvetica', fontSize=6.5,
                      textColor=GRAY, leading=9),
            'cval':   ParagraphStyle('cv', fontName='Helvetica-Bold', fontSize=28,
                      textColor=BLACK, leading=34),
            'mval':   ParagraphStyle('mv', fontName='Helvetica-Bold', fontSize=19,
                      textColor=BLACK, leading=23),
            'sval':   ParagraphStyle('sv', fontName='Helvetica-Bold', fontSize=12,
                      textColor=BLACK, leading=15),
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
            'al_lbl': ParagraphStyle('all', fontName='Helvetica-Bold', fontSize=7.5,
                      textColor=BLACK, leading=10),
            'al_pct': ParagraphStyle('alp', fontName='Helvetica-Bold', fontSize=7.5,
                      textColor=BLACK, alignment=TA_RIGHT, leading=10),
        }

    @staticmethod
    def _pct(v, dec=2):
        if v is None: return '—'
        return f'{"+" if v > 0 else ""}{v:.{dec}f}%'

    def _card_cell(self, lbl, val, sub='', val_size='big'):
        s = self.S()
        vst = {'big': s['cval'], 'med': s['mval'], 'small': s['sval']}[val_size]
        lines = [Paragraph(lbl, s['clbl']), Spacer(1, 7), Paragraph(str(val), vst)]
        if sub:
            lines += [Spacer(1, 4), Paragraph(sub, s['csub'])]
        return lines

    def _cards_row(self, cells, widths, pad=14):
        t = Table([cells], colWidths=widths)
        n = len(cells)
        t.setStyle(TableStyle([
            ('BOX',           (0,0),(-1,-1), 0.6, BORDER),
            ('LINEBEFORE',    (1,0),(n-1,0), 0.4, BORDER),
            ('BACKGROUND',    (0,0),(-1,-1), WHITE),
            ('VALIGN',        (0,0),(-1,-1), 'TOP'),
            ('TOPPADDING',    (0,0),(-1,-1), pad),
            ('BOTTOMPADDING', (0,0),(-1,-1), pad),
            ('LEFTPADDING',   (0,0),(-1,-1), 14),
            ('RIGHTPADDING',  (0,0),(-1,-1), 14),
        ]))
        return t

    def _wrap_card(self, content, cw):
        t = Table([[content]], colWidths=[cw])
        t.setStyle(TableStyle([
            ('BOX',           (0,0),(-1,-1), 0.6, BORDER),
            ('BACKGROUND',    (0,0),(-1,-1), WHITE),
            ('TOPPADDING',    (0,0),(-1,-1), 14),
            ('BOTTOMPADDING', (0,0),(-1,-1), 10),
            ('LEFTPADDING',   (0,0),(-1,-1), 14),
            ('RIGHTPADDING',  (0,0),(-1,-1), 14),
        ]))
        return t

    def _header(self, cw, etf_name, title_str):
        s = self.S()
        logo = Image(self.LOGO, width=3.6*cm, height=1.0*cm, kind='proportional') \
               if os.path.exists(self.LOGO) else Paragraph('CGF', s['h_name'])
        right = [Paragraph(etf_name, s['h_name']), Spacer(1, 2),
                 Paragraph(title_str, s['h_sub'])]
        hdr = Table([[logo, right]], colWidths=[4*cm, cw - 4*cm])
        hdr.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), BLACK),
            ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0),(-1,-1), 9),
            ('BOTTOMPADDING', (0,0),(-1,-1), 9),
            ('LEFTPADDING',   (0,0),(0,0),   12),
            ('RIGHTPADDING',  (1,0),(1,0),   12),
        ]))
        return [hdr, Spacer(1, 16)]

    # ── graphiques ───────────────────────────────────────────────────
    def _chart_vl_period(self, rows, par, cw_pt, h_in=3.2):
        dates = [r['date'] for r in rows]
        vls   = [r['vl']   for r in rows]
        fig, ax = plt.subplots(figsize=(cw_pt/72, h_in))
        fig.patch.set_facecolor('white'); ax.set_facecolor('white')
        xs = list(range(len(dates)))
        ax.plot(xs, vls, color='#1a3557', lw=2.0)
        ax.fill_between(xs, vls, min(vls) * 0.999, alpha=0.06, color='#1a3557')
        ax.axhline(par, color='#cccccc', ls='--', lw=0.8)
        vm, vM = min(vls), max(vls)
        amp = max(vM - vm, 0.5)
        ax.set_ylim(vm - amp * 0.3, vM + amp * 0.3)
        # Étiquettes axe x : un label par mois
        prev_month = None
        tick_pos, tick_lbl = [], []
        for i, d in enumerate(dates):
            m = d[:7]
            if m != prev_month:
                tick_pos.append(i); tick_lbl.append(pd.Timestamp(d).strftime('%b %y'))
                prev_month = m
        ax.set_xticks(tick_pos); ax.set_xticklabels(tick_lbl, fontsize=9)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:,.0f}'))
        ax.tick_params(colors='#777777', labelsize=8)
        for sp in ax.spines.values(): sp.set_color('#cccccc'); sp.set_linewidth(0.5)
        ax.grid(axis='y', color='#eeeeee', lw=0.5)
        plt.tight_layout(pad=0.3)
        buf = BytesIO(); plt.savefig(buf, format='png', dpi=160, bbox_inches='tight')
        plt.close(); buf.seek(0); return buf

    def _chart_base100_period(self, rows, cw_pt, h_in=3.0):
        fig, ax = plt.subplots(figsize=(cw_pt/72, h_in))
        fig.patch.set_facecolor('white'); ax.set_facecolor('white')
        v0 = rows[0]['vl']; b0 = rows[0]['etfdividende']
        etf_b100  = [r['vl'] / v0 * 100 for r in rows]
        brvm_b100 = [r['etfdividende'] / b0 * 100 if r['etfdividende'] and b0 else None for r in rows]
        xs     = list(range(len(rows)))
        ax.plot(xs, etf_b100, color='#1a3557', lw=2.0, label='CGF ETFDividende ETF')
        valid_b = [(i, v) for i, v in enumerate(brvm_b100) if v is not None]
        if valid_b:
            xi, yi = zip(*valid_b)
            ax.plot(xi, yi, color='#b8922f', lw=1.8, ls='--', label='ETFDividende')
        ax.axhline(100, color='#cccccc', ls=':', lw=0.8)
        all_vals = etf_b100 + [v for v in brvm_b100 if v]
        vmin, vmax = min(all_vals), max(all_vals)
        amp = max(vmax - vmin, 0.5)
        ax.set_ylim(vmin - amp * 0.3, vmax + amp * 0.3)
        prev_month = None; tick_pos, tick_lbl = [], []
        for i, r in enumerate(rows):
            m = r['date'][:7]
            if m != prev_month:
                tick_pos.append(i); tick_lbl.append(pd.Timestamp(r['date']).strftime('%b %y'))
                prev_month = m
        ax.set_xticks(tick_pos); ax.set_xticklabels(tick_lbl, fontsize=9)
        ax.set_ylabel('Base 100', fontsize=7.5, color='#777777')
        ax.legend(fontsize=8.5, framealpha=0)
        ax.tick_params(colors='#777777', labelsize=8)
        for sp in ax.spines.values(): sp.set_color('#cccccc'); sp.set_linewidth(0.5)
        ax.grid(axis='y', color='#eeeeee', lw=0.5)
        plt.tight_layout(pad=0.3)
        buf = BytesIO(); plt.savefig(buf, format='png', dpi=160, bbox_inches='tight')
        plt.close(); buf.seek(0); return buf

    def _chart_monthly_bars(self, monthly_summary, cw_pt, h_in=2.6):
        """Barres mensuelles ETF vs ETFDividende."""
        months = sorted(monthly_summary.keys())
        etf_perfs  = [monthly_summary[m]['perf_etf']  or 0 for m in months]
        brvm_perfs = [monthly_summary[m]['perf_brvm'] or 0 for m in months]
        labels = [pd.Timestamp(m + '-01').strftime('%b %y') for m in months]
        n = len(months)
        x = np.arange(n); w = 0.38
        fig, ax = plt.subplots(figsize=(cw_pt/72, h_in))
        fig.patch.set_facecolor('white'); ax.set_facecolor('white')
        ax.bar(x - w/2, etf_perfs,  w, label='ETF',   color='#1a3557', alpha=0.9)
        ax.bar(x + w/2, brvm_perfs, w, label='ETFDividende', color='#b8922f', alpha=0.9)
        ax.axhline(0, color='#333333', lw=0.7)
        ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.1f}%'))
        ax.legend(fontsize=8.5, framealpha=0)
        ax.tick_params(colors='#777777', labelsize=8)
        for sp in ['top','right']: ax.spines[sp].set_visible(False)
        for sp in ['left','bottom']: ax.spines[sp].set_color('#cccccc'); ax.spines[sp].set_linewidth(0.5)
        ax.grid(axis='y', color='#eeeeee', lw=0.5)
        plt.tight_layout(pad=0.3)
        buf = BytesIO(); plt.savefig(buf, format='png', dpi=160, bbox_inches='tight')
        plt.close(); buf.seek(0); return buf

    def _chart_hbar(self, labels, values, fig_w_pt, fig_h_in=2.4, bar_colors=None):
        n = len(labels)
        if bar_colors is None:
            bar_colors = ['#1a3557','#b8922f','#2d6a4f','#8b0000','#5a5a8a','#7c4a03','#888888']
        clrs = [bar_colors[i % len(bar_colors)] for i in range(n)]
        fig, ax = plt.subplots(figsize=(fig_w_pt/72, fig_h_in))
        fig.patch.set_facecolor('white'); ax.set_facecolor('white')
        ys   = list(range(n-1, -1, -1))
        bars = ax.barh(ys, values, height=0.55, color=clrs, edgecolor='white')
        ax.set_yticks(ys); ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlim(0, max(values) * 1.22)
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + max(values)*0.02, bar.get_y() + bar.get_height()/2,
                    f'{val:.1f}%', va='center', ha='left', fontsize=9,
                    fontweight='bold', color='#111111')
        ax.xaxis.set_visible(False)
        for sp in ['top','right','bottom']: ax.spines[sp].set_visible(False)
        ax.spines['left'].set_color('#cccccc'); ax.spines['left'].set_linewidth(0.5)
        ax.tick_params(left=False)
        plt.tight_layout(pad=0.5)
        buf = BytesIO(); plt.savefig(buf, format='png', dpi=160, bbox_inches='tight')
        plt.close(); buf.seek(0); return buf

    def _alloc_dicts(self, basket):
        sec, pays = {}, {}
        for r in basket:
            meta = TICKER_META.get(r['ticker'].upper())
            if not meta: continue
            s_, p_, _ = meta
            sec[s_]  = sec.get(s_, 0)  + r['poids_pct']
            pays[p_] = pays.get(p_, 0) + r['poids_pct']
        return sorted(sec.items(),  key=lambda x: x[1], reverse=True), \
               sorted(pays.items(), key=lambda x: x[1], reverse=True)

    def _detail_tbl(self, data, w, s):
        td = [[Paragraph(lbl, s['al_lbl']), Paragraph(f'{val:.1f}%', s['al_pct'])]
              for lbl, val in data]
        t = Table(td, colWidths=[w * 0.62, w * 0.38])
        sc_ = [('VALIGN',(0,0),(-1,-1),'MIDDLE'),
               ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),
               ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
               ('LINEABOVE',(0,0),(-1,-1),0.2,colors.HexColor('#e0e0e0'))]
        for i in range(len(data)):
            sc_.append(('BACKGROUND',(0,i),(-1,i), LGRAY if i%2==0 else WHITE))
        t.setStyle(TableStyle(sc_))
        return t

    def _stats_cards(self, rows, cw, s):
        """Carte avec métriques statistiques : vol, TE, Sharpe, drawdown."""
        vls = pd.Series([r['vl'] for r in rows])
        bvs = pd.Series([r['etfdividende'] for r in rows if r['etfdividende']])
        ret_etf  = vls.pct_change().dropna()
        vol_ann  = float(ret_etf.std() * np.sqrt(252) * 100) if len(ret_etf) >= 2 else None
        # Tracking error annualisée
        if len(bvs) >= 2:
            ret_bv = bvs.pct_change().dropna()
            idx    = ret_etf.index.intersection(ret_bv.index)
            diff   = ret_etf.loc[idx] - ret_bv.loc[idx]
            te_ann = float(diff.std() * np.sqrt(252) * 100) if len(diff) >= 2 else None
        else:
            te_ann = None
        # Max drawdown
        cum   = (1 + ret_etf).cumprod()
        roll_max = cum.cummax()
        dd = ((cum - roll_max) / roll_max * 100)
        mdd = float(dd.min()) if not dd.empty else None

        launch = self._load('launch_state.json') or {}
        par    = float(launch.get('par_fcfa', 100000))
        perf_total = (rows[-1]['vl'] / par - 1) * 100 if rows else None

        vol_str = f'{vol_ann:.2f}%' if vol_ann is not None else '—'
        te_str  = f'{te_ann:.2f}%'  if te_ann  is not None else '—'
        mdd_str = f'{mdd:.2f}%'     if mdd     is not None else '—'
        pt_str  = self._pct(perf_total)

        return self._cards_row([
            self._card_cell('PERF. DEPUIS LANCEMENT', pt_str,     'total ETF vs. valeur initiale', val_size='small'),
            self._card_cell('VOLATILITÉ ANNUALISÉE',  vol_str,   'écart-type rendements journaliers', val_size='small'),
            self._card_cell('TRACKING ERROR',          te_str,   'annualisée vs. ETFDividende', val_size='small'),
            self._card_cell('MAX DRAWDOWN',            mdd_str,  'pire perte peak-to-trough', val_size='small'),
        ], [cw/4]*4, pad=12)

    # ── RAPPORT SEMESTRIEL ──────────────────────────────────────────
    def generate_semiannual(self, year, semester, force=False):
        label = f'{year}-S{semester}'
        pdfs_dir = os.path.join(self.data_dir, 'pdfs', 'semestriel', str(year))
        os.makedirs(pdfs_dir, exist_ok=True)
        pdf_path = os.path.join(pdfs_dir, f'rapport_semestriel_{label}.pdf')
        if os.path.exists(pdf_path) and not force:
            print(f'Existant : {pdf_path}'); return pdf_path

        date_from = f'{year}-01-01' if semester == 1 else f'{year}-07-01'
        date_to   = f'{year}-06-30' if semester == 1 else f'{year}-12-31'
        title = f'Rapport semestriel  ·  {"1er" if semester==1 else "2ème"} semestre {year}'

        print(f'Rapport semestriel {label}...')
        nl      = self._load('nav_latest.json') or {}
        launch  = self._load('launch_state.json') or {}
        par     = float(launch.get('par_fcfa', 100000))
        etf_name= nl.get('etf_name', 'CGF ETFDividende ETF')
        basket  = nl.get('basket', [])

        rows = self._period_rows(date_from, date_to)
        if not rows:
            print(f'Aucune donnée pour {label}'); return None

        monthly = self._monthly_summary(rows)
        self._build_periodic_pdf(pdf_path, etf_name, title, rows, monthly, basket, par, cw_target=None)
        return pdf_path

    # ── RAPPORT ANNUEL ──────────────────────────────────────────────
    def generate_annual(self, year, force=False):
        pdfs_dir = os.path.join(self.data_dir, 'pdfs', 'annuel')
        os.makedirs(pdfs_dir, exist_ok=True)
        pdf_path = os.path.join(pdfs_dir, f'rapport_annuel_{year}.pdf')
        if os.path.exists(pdf_path) and not force:
            print(f'Existant : {pdf_path}'); return pdf_path

        title = f'Rapport annuel  ·  {year}'
        print(f'Rapport annuel {year}...')
        nl       = self._load('nav_latest.json') or {}
        launch   = self._load('launch_state.json') or {}
        par      = float(launch.get('par_fcfa', 100000))
        etf_name = nl.get('etf_name', 'CGF ETFDividende ETF')
        basket   = nl.get('basket', [])

        rows = self._period_rows(f'{year}-01-01', f'{year}-12-31')
        if not rows:
            print(f'Aucune donnée pour {year}'); return None

        monthly = self._monthly_summary(rows)
        self._build_periodic_pdf(pdf_path, etf_name, title, rows, monthly, basket, par)
        return pdf_path

    # ── constructeur de PDF partagé ──────────────────────────────────
    def _build_periodic_pdf(self, pdf_path, etf_name, title, rows, monthly, basket, par, cw_target=None):
        s  = self.S()
        cw = (self.PAGE_W - 2 * self.M) if cw_target is None else cw_target
        footer_note = (
            f'Document à usage interne  ·  CGF Gestion — Agréé CREPMF  ·  '
            f'Généré le {datetime.now().strftime("%d/%m/%Y %H:%M")} UTC  ·  '
            f'Les performances passées ne préjugent pas des performances futures.'
        )

        vl_start  = rows[0]['vl'];  vl_end = rows[-1]['vl']
        bv_start  = rows[0]['etfdividende']; bv_end = rows[-1]['etfdividende']
        perf_etf  = (vl_end / vl_start - 1) * 100
        perf_brvm = (bv_end / bv_start - 1) * 100 if bv_start and bv_end else None
        aum_end   = rows[-1]['aum']
        n_seances = len(rows)

        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
            leftMargin=self.M, rightMargin=self.M,
            topMargin=0.8*cm, bottomMargin=0.8*cm,
            title=f'{title} — {etf_name}', author='CGF Gestion')

        story = []

        # ══ PAGE 1 : KPI + VL + Base100 ══════════════════════════════
        story += self._header(cw, etf_name, title)

        # KPI principaux
        story.append(self._cards_row([
            self._card_cell('VL FIN DE PÉRIODE',   f'{vl_end:,.0f}',
                            f'FCFA / part  ·  {rows[-1]["date"]}', val_size='big'),
            self._card_cell('VL DÉBUT DE PÉRIODE',  f'{vl_start:,.0f}',
                            f'FCFA / part  ·  {rows[0]["date"]}', val_size='big'),
        ], [cw * 0.55, cw * 0.45], pad=16))
        story.append(Spacer(1, 6))

        story.append(self._cards_row([
            self._card_cell('PERFORMANCE ETF',   self._pct(perf_etf),
                            f'{rows[0]["date"]} → {rows[-1]["date"]}', val_size='med'),
            self._card_cell('PERFORMANCE ETFDividende', self._pct(perf_brvm),
                            'indice de cours', val_size='med'),
            self._card_cell('ACTIF NET',          f'{aum_end:,.1f} M',
                            f'FCFA  ·  fin de période', val_size='med'),
            self._card_cell('SÉANCES',            str(n_seances),
                            'jours de cotation', val_size='med'),
        ], [cw/4]*4, pad=12))
        story.append(Spacer(1, 6))

        # Graphique VL
        buf_vl = self._chart_vl_period(rows, par, cw - 28)
        story.append(self._wrap_card([
            Paragraph('ÉVOLUTION DE LA VALEUR LIQUIDATIVE', s['clbl']),
            Spacer(1,3),
            Paragraph(f'{n_seances} séances  ·  min {min(r["vl"] for r in rows):,.0f}  –  '
                      f'max {max(r["vl"] for r in rows):,.0f} FCFA', s['csub']),
            Spacer(1,8),
            Image(buf_vl, width=cw-28, height=3.2*72),
        ], cw))
        story.append(Spacer(1,10))
        story.append(HRFlowable(width=cw, thickness=0.4,
                                color=colors.HexColor('#cccccc'), spaceAfter=4))
        story.append(Paragraph(footer_note, s['note']))

        # ══ PAGE 2 : Base100 + Barres mensuelles + Stats ══════════════
        story.append(PageBreak())
        story += self._header(cw, etf_name, title)

        buf_b100 = self._chart_base100_period(rows, cw-28)
        story.append(self._wrap_card([
            Paragraph('PERFORMANCE RELATIVE', s['clbl']),
            Spacer(1,3),
            Paragraph(f'Base 100 = {_dfr(rows[0]["date"])}  ·  '
                      f'ETF {self._pct(perf_etf)}  ·  ETFDividende {self._pct(perf_brvm)}', s['csub']),
            Spacer(1,8),
            Image(buf_b100, width=cw-28, height=3.0*72),
        ], cw))
        story.append(Spacer(1,6))

        # Barres mensuelles si plusieurs mois
        if len(monthly) >= 2:
            buf_bars = self._chart_monthly_bars(monthly, cw-28)
            story.append(self._wrap_card([
                Paragraph('PERFORMANCES MENSUELLES  (ETF vs ETFDividende)', s['clbl']),
                Spacer(1,8),
                Image(buf_bars, width=cw-28, height=2.6*72),
            ], cw))
            story.append(Spacer(1,6))

        # Métriques statistiques
        story.append(self._stats_cards(rows, cw, s))
        story.append(Spacer(1,10))
        story.append(HRFlowable(width=cw, thickness=0.4,
                                color=colors.HexColor('#cccccc'), spaceAfter=4))
        story.append(Paragraph(footer_note, s['note']))

        # ══ PAGE 3 : Tableau mensuel + Allocation ══════════════════════
        story.append(PageBreak())
        story += self._header(cw, etf_name, title)

        # Tableau récap mensuel
        story.append(Paragraph('RÉCAPITULATIF PAR MOIS', s['clbl']))
        story.append(Spacer(1,5))
        cws_m = [cw*x for x in [0.14, 0.14, 0.14, 0.14, 0.16, 0.14, 0.14]]
        hrow  = [Paragraph(h, s['th']) for h in
                 ['Mois','VL début','VL fin','Perf. ETF','Perf. ETFDividende','AUM fin (M)','Séances']]
        trows = [hrow]
        for ym in sorted(monthly.keys()):
            m = monthly[ym]
            t = pd.Timestamp(ym + '-01')
            lbl = f'{MOIS_CAPS[t.month-1]} {t.year}'
            vp  = s['td_pos'] if (m['perf_etf'] or 0) > 0 else (s['td_neg'] if (m['perf_etf'] or 0) < 0 else s['td'])
            bp  = s['td_pos'] if (m['perf_brvm'] or 0) > 0 else (s['td_neg'] if (m['perf_brvm'] or 0) < 0 else s['td'])
            trows.append([
                Paragraph(lbl, s['td']),
                Paragraph(f"{m['vl_start']:,.0f}", s['td']),
                Paragraph(f"{m['vl_end']:,.0f}",   s['td']),
                Paragraph(self._pct(m['perf_etf']),  vp),
                Paragraph(self._pct(m['perf_brvm']), bp),
                Paragraph(f"{m['aum_end']:.1f}",     s['td']),
                Paragraph(str(m['n_seances']),        s['td']),
            ])
        sc = [
            ('BACKGROUND',(0,0),(-1,0), BLACK),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
            ('LINEABOVE',(0,1),(-1,-1),0.2,colors.HexColor('#dddddd')),
            ('BOX',(0,0),(-1,-1),0.6,BORDER),
        ]
        for i in range(1, len(trows)):
            if i%2==0: sc.append(('BACKGROUND',(0,i),(-1,i),LGRAY))
        t_m = Table(trows, colWidths=cws_m, repeatRows=1)
        t_m.setStyle(TableStyle(sc))
        story.append(t_m)
        story.append(Spacer(1,6))

        # Allocation sectorielle + géographique
        sec_data, pays_data = self._alloc_dicts(basket)
        n_sec, n_pays = len(sec_data), len(pays_data)
        h_both = max(1.8, max(n_sec, n_pays) * 0.38)
        w_sec   = (cw-6)*0.52; w_pays = (cw-6)*0.48
        ch_sec  = w_sec-28;    ch_pays = w_pays-28
        sec_clrs  = [SECTOR_COLORS.get(l, '#888888')  for l,_ in sec_data]
        pays_clrs = [COUNTRY_COLORS.get(l, '#888888') for l,_ in pays_data]
        buf_sec  = self._chart_hbar([l for l,_ in sec_data],  [v for _,v in sec_data],
                                    ch_sec,  h_both, sec_clrs)
        buf_pays = self._chart_hbar([l for l,_ in pays_data], [v for _,v in pays_data],
                                    ch_pays, h_both, pays_clrs)
        cell_sec  = [Paragraph('RÉPARTITION SECTORIELLE',  s['clbl']), Spacer(1,4),
                     Image(buf_sec,  width=ch_sec,  height=h_both*72), Spacer(1,8),
                     self._detail_tbl(sec_data,  ch_sec,  s)]
        cell_pays = [Paragraph('RÉPARTITION GÉOGRAPHIQUE', s['clbl']), Spacer(1,4),
                     Image(buf_pays, width=ch_pays, height=h_both*72), Spacer(1,8),
                     self._detail_tbl(pays_data, ch_pays, s)]
        t_alloc = Table([[cell_sec, cell_pays]], colWidths=[w_sec, w_pays])
        t_alloc.setStyle(TableStyle([
            ('BOX',(0,0),(-1,-1),0.6,BORDER),('LINEBEFORE',(1,0),(1,0),0.4,BORDER),
            ('BACKGROUND',(0,0),(-1,-1),WHITE),('VALIGN',(0,0),(-1,-1),'TOP'),
            ('TOPPADDING',(0,0),(-1,-1),14),('BOTTOMPADDING',(0,0),(-1,-1),14),
            ('LEFTPADDING',(0,0),(-1,-1),14),('RIGHTPADDING',(0,0),(-1,-1),14),
        ]))
        story.append(KeepTogether([
            t_alloc, Spacer(1,10),
            HRFlowable(width=cw, thickness=0.4, color=colors.HexColor('#cccccc'), spaceAfter=4),
            Paragraph(footer_note, s['note']),
        ]))

        doc.build(story)
        print(f'PDF : {pdf_path}')

    def run(self):
        import argparse
        p = argparse.ArgumentParser()
        p.add_argument('--period', choices=['semiannual','annual'], required=True)
        p.add_argument('--year',   type=int, default=datetime.now().year)
        p.add_argument('--semester', type=int, choices=[1,2], default=1)
        p.add_argument('--force', action='store_true')
        a = p.parse_args()
        if a.period == 'semiannual':
            self.generate_semiannual(a.year, a.semester, force=a.force)
        else:
            self.generate_annual(a.year, force=a.force)


if __name__ == '__main__':
    PeriodicReportGenerator().run()
