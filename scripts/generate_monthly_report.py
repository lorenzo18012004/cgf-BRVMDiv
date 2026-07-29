"""
generate_monthly_report.py — Rapport mensuel CGF ETFDividende ETF
Usage : python generate_monthly_report.py [--month YYYY-MM] [--force]
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
    _date_fr, _dfr, MOIS_FR,
)

MOIS_CAPS = [m.capitalize() for m in MOIS_FR]


class MonthlyReportGenerator(BaseScript):

    def __init__(self):
        super().__init__()
        self.PAGE_W, self.PAGE_H = A4
        self.M = 1.8 * cm
        self.LOGO = os.path.join(self.root_dir, '1780762763961.jpg')

    def _load(self, f):
        p = os.path.join(self.data_dir, f)
        if not os.path.exists(p): return None
        import json; return json.load(open(p, encoding='utf-8'))

    def _pdfs_dir(self, year):
        return os.path.join(self.data_dir, 'pdfs', 'mensuel', str(year))

    # ── collecte des données du mois ────────────────────────────────
    def _month_data(self, year, month):
        """Retourne une liste de dicts {date, vl, etfdividende, aum} pour chaque séance."""
        ih      = self._load('nav_intraday_history.json') or {}
        brvm_h  = self._load('etfdividende_index_history.json') or {}
        launch  = self._load('launch_state.json') or {}
        par     = float(launch.get('par_fcfa', 100000))

        rows = []
        for d, snaps in sorted(ih.items()):
            t = pd.Timestamp(d)
            if t.year != year or t.month != month or not snaps:
                continue
            lp  = snaps[-1]
            vl  = float(lp.get('vl_live_fcfa') or lp.get('vl_fcfa') or lp.get('vl') or par)
            bv  = float(lp.get('etfdividende_official') or brvm_h.get(d) or 0) or None
            aum = float(lp.get('aum_mfcfa') or 0)
            rows.append({'date': d, 'vl': vl, 'etfdividende': bv, 'aum': aum})
        return rows

    # ── styles ───────────────────────────────────────────────────────
    def S(self):
        return {
            'h_name': ParagraphStyle('hn', fontName='Helvetica-Bold', fontSize=11,
                      textColor=WHITE, alignment=TA_RIGHT, leading=14),
            'h_sub':  ParagraphStyle('hs', fontName='Helvetica', fontSize=7.5,
                      textColor=colors.HexColor('#bbbbbb'), alignment=TA_RIGHT, leading=10),
            'clbl':   ParagraphStyle('cl', fontName='Helvetica', fontSize=6.5,
                      textColor=GRAY, leading=9),
            'cval':   ParagraphStyle('cv', fontName='Helvetica-Bold', fontSize=30,
                      textColor=BLACK, leading=36),
            'mval':   ParagraphStyle('mv', fontName='Helvetica-Bold', fontSize=20,
                      textColor=BLACK, leading=24),
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
    def _chart_vl_month(self, rows, par, cw_pt):
        dates = [r['date'] for r in rows]
        vls   = [r['vl']   for r in rows]
        fig, ax = plt.subplots(figsize=(cw_pt/72, 3.0))
        fig.patch.set_facecolor('white'); ax.set_facecolor('white')
        xs = list(range(len(dates)))
        ax.plot(xs, vls, color='#1a3557', lw=2.2, marker='o', ms=5)
        ax.fill_between(xs, vls, min(vls) * 0.9995, alpha=0.06, color='#1a3557')
        ax.axhline(par, color='#cccccc', ls='--', lw=0.8, alpha=0.7)
        vm, vM = min(vls), max(vls)
        ax.annotate(f'{vm:,.0f}', xy=(vls.index(vm), vm), xytext=(0,-14),
                    textcoords='offset points', fontsize=8, color='#991b1b', ha='center', fontweight='bold')
        ax.annotate(f'{vM:,.0f}', xy=(vls.index(vM), vM), xytext=(0,7),
                    textcoords='offset points', fontsize=8, color='#166534', ha='center', fontweight='bold')
        step = max(1, len(dates) // 10)
        ax.set_xticks(xs[::step])
        ax.set_xticklabels([pd.Timestamp(d).strftime('%d/%m') for d in dates[::step]], fontsize=9)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:,.0f}'))
        amp = max(vM - vm, 0.5)
        ax.set_ylim(vm - amp * 0.35, vM + amp * 0.35)
        ax.tick_params(colors='#777777', labelsize=8)
        for sp in ax.spines.values(): sp.set_color('#cccccc'); sp.set_linewidth(0.5)
        ax.grid(axis='y', color='#eeeeee', lw=0.5)
        plt.tight_layout(pad=0.3)
        buf = BytesIO(); plt.savefig(buf, format='png', dpi=160, bbox_inches='tight')
        plt.close(); buf.seek(0); return buf

    def _chart_base100_month(self, rows, brvm_al, par, cw_pt):
        fig, ax = plt.subplots(figsize=(cw_pt/72, 2.8))
        fig.patch.set_facecolor('white'); ax.set_facecolor('white')
        first_vl = rows[0]['vl']; first_bv = rows[0]['etfdividende']
        etf_b100  = [r['vl'] / first_vl * 100 for r in rows]
        brvm_b100 = [r['etfdividende'] / first_bv * 100 if r['etfdividende'] and first_bv else None for r in rows]
        xs     = list(range(len(rows)))
        labels = [pd.Timestamp(r['date']).strftime('%d/%m') for r in rows]
        ax.plot(xs, etf_b100, color='#1a3557', lw=2.2, marker='o', ms=4, label='CGF ETFDividende ETF')
        valid_b = [(i, v) for i, v in enumerate(brvm_b100) if v is not None]
        if valid_b:
            xi, yi = zip(*valid_b)
            ax.plot(xi, yi, color='#b8922f', lw=1.8, ls='--', marker='s', ms=3, label='ETFDividende')
        ax.axhline(100, color='#cccccc', ls=':', lw=0.8)
        all_vals = etf_b100 + [v for v in brvm_b100 if v]
        vmin, vmax = min(all_vals), max(all_vals)
        amp = max(vmax - vmin, 0.5)
        ax.set_ylim(vmin - amp * 0.35, vmax + amp * 0.35)
        step = max(1, len(xs) // 10)
        ax.set_xticks(xs[::step]); ax.set_xticklabels(labels[::step], fontsize=9)
        ax.set_ylabel('Base 100', fontsize=7.5, color='#777777')
        ax.legend(fontsize=8.5, framealpha=0)
        ax.tick_params(colors='#777777', labelsize=8)
        for sp in ax.spines.values(): sp.set_color('#cccccc'); sp.set_linewidth(0.5)
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
        ys = list(range(n-1, -1, -1))
        bars = ax.barh(ys, values, height=0.55, color=clrs, edgecolor='white')
        ax.set_yticks(ys); ax.set_yticklabels(labels, fontsize=9, color='#111111')
        ax.set_xlim(0, max(values) * 1.22)
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + max(values)*0.02, bar.get_y() + bar.get_height()/2,
                    f'{val:.1f}%', va='center', ha='left', fontsize=9, fontweight='bold', color='#111111')
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

    # ── génération ───────────────────────────────────────────────────
    def generate(self, month_str=None, force=False):
        if month_str is None:
            t = pd.Timestamp.now()
            month_str = t.strftime('%Y-%m')
        year, month = int(month_str[:4]), int(month_str[5:7])
        pdfs_dir = self._pdfs_dir(year)
        os.makedirs(pdfs_dir, exist_ok=True)
        pdf_path = os.path.join(pdfs_dir, f'rapport_mensuel_{month_str}.pdf')
        if os.path.exists(pdf_path) and not force:
            print(f'Existant : {pdf_path}'); return pdf_path

        print(f'Rapport mensuel {month_str}...')
        nl     = self._load('nav_latest.json')          or {}
        launch = self._load('launch_state.json')        or {}
        brvm_h = self._load('etfdividende_index_history.json') or {}

        par        = float(launch.get('par_fcfa', 100000))
        etf_name   = nl.get('etf_name', 'CGF ETFDividende ETF')
        brvm_al    = float(launch.get('etfdividende_index_at_launch') or 0) or None

        rows = self._month_data(year, month)
        if not rows:
            print(f'Aucune donnée pour {month_str}'); return None

        vl_start  = rows[0]['vl']
        vl_end    = rows[-1]['vl']
        bv_start  = rows[0]['etfdividende']
        bv_end    = rows[-1]['etfdividende']
        aum_end   = rows[-1]['aum']
        n_seances = len(rows)

        perf_etf  = (vl_end / vl_start - 1) * 100
        perf_brvm = (bv_end / bv_start - 1) * 100 if bv_start and bv_end else None
        td_mois   = perf_etf - perf_brvm if perf_brvm is not None else None

        # Volatilité mensuelle (écart-type des rendements journaliers)
        vls = pd.Series([r['vl'] for r in rows])
        vol_m = float(vls.pct_change().dropna().std() * 100) if len(rows) > 2 else None

        basket = nl.get('basket', [])

        s  = self.S()
        cw = self.PAGE_W - 2 * self.M
        title = f'Rapport mensuel  ·  {MOIS_CAPS[month-1]} {year}'
        footer_note = (
            f'Document à usage interne  ·  CGF Gestion — Agréé CREPMF  ·  '
            f'Généré le {datetime.now().strftime("%d/%m/%Y %H:%M")} UTC  ·  '
            f'Les performances passées ne préjugent pas des performances futures.'
        )

        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
            leftMargin=self.M, rightMargin=self.M,
            topMargin=0.8*cm, bottomMargin=0.8*cm,
            title=f'Rapport mensuel — {etf_name} — {month_str}',
            author='CGF Gestion')

        story = []

        # ══ PAGE 1 ════════════════════════════════════════════════════
        story += self._header(cw, etf_name, title)

        # ── KPI VL ────────────────────────────────────────────────────
        story.append(self._cards_row([
            self._card_cell('VL FIN DE MOIS', f'{vl_end:,.0f}',
                            f'FCFA / part  ·  {rows[-1]["date"]}', val_size='big'),
            self._card_cell('VL DÉBUT DE MOIS', f'{vl_start:,.0f}',
                            f'FCFA / part  ·  {rows[0]["date"]}', val_size='big'),
        ], [cw * 0.55, cw * 0.45], pad=16))
        story.append(Spacer(1, 6))

        # ── Métriques de performance ───────────────────────────────────
        td_str  = f'{td_mois:+.2f}%' if td_mois is not None else '—'
        vol_str = f'{vol_m:.2f}%' if vol_m is not None else '—'
        story.append(self._cards_row([
            self._card_cell('PERF. ETF DU MOIS',  self._pct(perf_etf),
                            f'du {rows[0]["date"]} au {rows[-1]["date"]}', val_size='med'),
            self._card_cell('PERF. ETFDividende',        self._pct(perf_brvm),
                            'indice de cours du mois', val_size='med'),
            self._card_cell('ÉCART ETF / ETFDividende',  td_str,
                            'surperformance mensuelle', val_size='med'),
            self._card_cell('VOLATILITÉ JOURNALIÈRE', vol_str,
                            f'écart-type  ·  {n_seances} séances', val_size='med'),
        ], [cw / 4] * 4, pad=12))
        story.append(Spacer(1, 6))

        # ── Graphique VL du mois ───────────────────────────────────────
        buf_vl = self._chart_vl_month(rows, par, cw - 28)
        story.append(self._wrap_card([
            Paragraph('ÉVOLUTION DE LA VALEUR LIQUIDATIVE', s['clbl']),
            Spacer(1, 3),
            Paragraph(f'{n_seances} séances  ·  min {min(r["vl"] for r in rows):,.0f}  –  '
                      f'max {max(r["vl"] for r in rows):,.0f} FCFA  ·  '
                      f'AUM fin de mois : {aum_end:,.1f} M FCFA', s['csub']),
            Spacer(1, 8),
            Image(buf_vl, width=cw - 28, height=3.0 * 72),
        ], cw))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width=cw, thickness=0.4,
                                color=colors.HexColor('#cccccc'), spaceAfter=4))
        story.append(Paragraph(footer_note, s['note']))

        # ══ PAGE 2 ════════════════════════════════════════════════════
        story.append(PageBreak())
        story += self._header(cw, etf_name, title)

        # ── Base 100 du mois ───────────────────────────────────────────
        if len(rows) >= 2 and bv_start:
            buf_b100 = self._chart_base100_month(rows, brvm_al, par, cw - 28)
            story.append(self._wrap_card([
                Paragraph('PERFORMANCE RELATIVE DU MOIS', s['clbl']),
                Spacer(1, 3),
                Paragraph(f'Base 100 = {_dfr(rows[0]["date"])}  ·  '
                          f'ETF {self._pct(perf_etf)}  ·  ETFDividende {self._pct(perf_brvm)}', s['csub']),
                Spacer(1, 8),
                Image(buf_b100, width=cw - 28, height=2.8 * 72),
            ], cw))
            story.append(Spacer(1, 6))

        # ── Tableau des séances ────────────────────────────────────────
        story.append(Paragraph(f'DÉTAIL DES SÉANCES  ·  {n_seances} jours de cotation', s['clbl']))
        story.append(Spacer(1, 5))
        cws_t = [cw * x for x in [0.16, 0.18, 0.18, 0.18, 0.16, 0.14]]
        hrow  = [Paragraph(h, s['th']) for h in
                 ['Date', 'VL (FCFA)', 'ETFDividende', 'Var. VL', 'Var. ETFDividende', 'AUM (M)']]
        trows = [hrow]
        for i, r in enumerate(rows):
            vl_prev   = rows[i-1]['vl']    if i > 0 else None
            bv_prev   = rows[i-1]['etfdividende'] if i > 0 else None
            var_vl    = (r['vl'] / vl_prev - 1) * 100    if vl_prev else None
            var_brvm  = (r['etfdividende'] / bv_prev - 1) * 100 if bv_prev and r['etfdividende'] else None
            s_vvl  = s['td_pos'] if (var_vl or 0) > 0 else (s['td_neg'] if (var_vl or 0) < 0 else s['td'])
            s_vbv  = s['td_pos'] if (var_brvm or 0) > 0 else (s['td_neg'] if (var_brvm or 0) < 0 else s['td'])
            trows.append([
                Paragraph(pd.Timestamp(r['date']).strftime('%d/%m/%Y'), s['td']),
                Paragraph(f"{r['vl']:,.0f}", s['td']),
                Paragraph(f"{r['etfdividende']:.2f}" if r['etfdividende'] else '—', s['td']),
                Paragraph(self._pct(var_vl) if var_vl is not None else '—', s_vvl),
                Paragraph(self._pct(var_brvm) if var_brvm is not None else '—', s_vbv),
                Paragraph(f"{r['aum']:.1f}", s['td']),
            ])
        sc = [
            ('BACKGROUND',    (0,0),(-1,0),  BLACK),
            ('ALIGN',         (0,0),(-1,-1), 'CENTER'),
            ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0),(-1,-1), 2),
            ('BOTTOMPADDING', (0,0),(-1,-1), 2),
            ('LINEABOVE',     (0,1),(-1,-1), 0.2, colors.HexColor('#dddddd')),
            ('BOX',           (0,0),(-1,-1), 0.6, BORDER),
        ]
        for i in range(1, len(trows)):
            if i % 2 == 0: sc.append(('BACKGROUND', (0,i),(-1,i), LGRAY))
        t_seances = Table(trows, colWidths=cws_t, repeatRows=1)
        t_seances.setStyle(TableStyle(sc))
        story.append(t_seances)
        story.append(Spacer(1, 6))

        # ── Allocation sectorielle + géographique ─────────────────────
        sec_data, pays_data = self._alloc_dicts(basket)
        n_sec, n_pays = len(sec_data), len(pays_data)
        h_both = max(1.8, max(n_sec, n_pays) * 0.38)
        w_sec   = (cw - 6) * 0.52; w_pays  = (cw - 6) * 0.48
        ch_sec  = w_sec  - 28;     ch_pays = w_pays - 28

        sec_clrs  = [SECTOR_COLORS.get(l, '#888888')  for l, _ in sec_data]
        pays_clrs = [COUNTRY_COLORS.get(l, '#888888') for l, _ in pays_data]
        buf_sec  = self._chart_hbar([l for l,_ in sec_data],  [v for _,v in sec_data],
                                    ch_sec,  h_both, sec_clrs)
        buf_pays = self._chart_hbar([l for l,_ in pays_data], [v for _,v in pays_data],
                                    ch_pays, h_both, pays_clrs)

        def _detail_tbl(data, w, s):
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

        cell_sec  = [Paragraph('RÉPARTITION SECTORIELLE', s['clbl']), Spacer(1,4),
                     Image(buf_sec,  width=ch_sec,  height=h_both*72),
                     Spacer(1,8), _detail_tbl(sec_data,  ch_sec,  s)]
        cell_pays = [Paragraph('RÉPARTITION GÉOGRAPHIQUE', s['clbl']), Spacer(1,4),
                     Image(buf_pays, width=ch_pays, height=h_both*72),
                     Spacer(1,8), _detail_tbl(pays_data, ch_pays, s)]

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
        story.append(KeepTogether([
            t_alloc,
            Spacer(1, 10),
            HRFlowable(width=cw, thickness=0.4, color=colors.HexColor('#cccccc'), spaceAfter=4),
            Paragraph(footer_note, s['note']),
        ]))

        doc.build(story)
        print(f'PDF : {pdf_path}')
        return pdf_path

    def run(self):
        import argparse
        p = argparse.ArgumentParser()
        p.add_argument('--month', default=None, help='YYYY-MM')
        p.add_argument('--force', action='store_true')
        a = p.parse_args()
        self.generate(month_str=a.month, force=a.force)


if __name__ == '__main__':
    MonthlyReportGenerator().run()
