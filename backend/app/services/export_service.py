"""
PDF Export Service — Design premium pour les plans d'étude AI Study Planner
Layout paysage, couleurs par matière, header stylé, stats visuelles
"""
from datetime import datetime, timedelta, date as date_type
from io import BytesIO
from typing import Optional
import asyncio

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus.flowables import Flowable

from sqlalchemy.orm import Session
from app.models.study_plan import StudyPlan
from app.models.study_session import StudySession
from app.models.user import User


# ─── Palette de couleurs ────────────────────────────────────────────────────

PRIMARY       = colors.HexColor('#4F46E5')   # Indigo-600
PRIMARY_DARK  = colors.HexColor('#312E81')   # Indigo-900
PRIMARY_LIGHT = colors.HexColor('#818CF8')   # Indigo-400
ACCENT        = colors.HexColor('#7C3AED')   # Violet-600
BG_HEADER     = colors.HexColor('#1E1B4B')   # Indigo-950
BG_LIGHT      = colors.HexColor('#F5F3FF')   # Violet-50
BG_MID        = colors.HexColor('#EDE9FE')   # Violet-100
BORDER_COLOR  = colors.HexColor('#DDD6FE')   # Violet-200
TEXT_DARK     = colors.HexColor('#1E1B4B')   # Indigo-950
TEXT_MUTED    = colors.HexColor('#6B7280')   # Gray-500
TEXT_WHITE    = colors.HexColor('#FFFFFF')
TEXT_LIGHT    = colors.HexColor('#C4B5FD')   # Violet-300
GOLD          = colors.HexColor('#F59E0B')   # Amber-500
SUCCESS       = colors.HexColor('#10B981')   # Emerald-500

# Palette de couleurs par matière (10 couleurs distinctes)
SUBJECT_PALETTE = [
    ('#3B82F6', '#EFF6FF'),  # Blue
    ('#8B5CF6', '#F5F3FF'),  # Violet
    ('#10B981', '#ECFDF5'),  # Emerald
    ('#F59E0B', '#FFFBEB'),  # Amber
    ('#EF4444', '#FEF2F2'),  # Red
    ('#06B6D4', '#ECFEFF'),  # Cyan
    ('#EC4899', '#FDF2F8'),  # Pink
    ('#F97316', '#FFF7ED'),  # Orange
    ('#14B8A6', '#F0FDFA'),  # Teal
    ('#6366F1', '#EEF2FF'),  # Indigo-light
]

JOURS_FR = {
    'Monday': 'Lundi',
    'Tuesday': 'Mardi',
    'Wednesday': 'Mercredi',
    'Thursday': 'Jeudi',
    'Friday': 'Vendredi',
    'Saturday': 'Samedi',
    'Sunday': 'Dimanche',
}
DAYS_OF_WEEK = list(JOURS_FR.keys())


# ─── Flowable : ligne décorative ────────────────────────────────────────────

class ColoredRule(Flowable):
    """Ligne colorée avec dégradé simulé."""
    def __init__(self, width, height=3, color=PRIMARY):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.color = color

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)


class StatBox(Flowable):
    """Boîte de statistique stylée."""
    def __init__(self, label, value, color=PRIMARY, width=4.5*cm, height=2.2*cm):
        Flowable.__init__(self)
        self.label = label
        self.value = value
        self.color = color
        self.width = width
        self.height = height

    def draw(self):
        c = self.canv
        w, h = self.width, self.height
        radius = 8

        # Fond blanc avec bordure colorée
        c.setFillColor(colors.white)
        c.setStrokeColor(self.color)
        c.setLineWidth(1.5)
        c.roundRect(0, 0, w, h, radius, fill=1, stroke=1)

        # Barre colorée en haut
        c.setFillColor(self.color)
        c.setStrokeColor(colors.transparent)
        c.roundRect(0, h - 6, w, 6, radius, fill=1, stroke=0)
        c.rect(0, h - 12, w, 6, fill=1, stroke=0)

        # Valeur (grande)
        c.setFillColor(TEXT_DARK)
        c.setFont('Helvetica-Bold', 18)
        c.drawCentredString(w / 2, h * 0.28, str(self.value))

        # Label (petit)
        c.setFillColor(TEXT_MUTED)
        c.setFont('Helvetica', 7.5)
        c.drawCentredString(w / 2, h * 0.12, self.label)


# ─── Service principal ───────────────────────────────────────────────────────

class ExportService:
    """Service d'export PDF premium pour les plans d'étude."""

    MAX_FILE_SIZE  = 10 * 1024 * 1024   # 10 MB
    TIMEOUT_SECONDS = 15
    DAYS_OF_WEEK   = DAYS_OF_WEEK

    def __init__(self, db: Session):
        self.db = db
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    # ── Styles ────────────────────────────────────────────────────────────

    def _setup_styles(self):
        self.styles.add(ParagraphStyle(
            'HeroTitle',
            parent=self.styles['Normal'],
            fontSize=22,
            textColor=TEXT_WHITE,
            fontName='Helvetica-Bold',
            alignment=TA_LEFT,
            spaceAfter=2,
        ))
        self.styles.add(ParagraphStyle(
            'HeroSub',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=TEXT_LIGHT,
            fontName='Helvetica',
            alignment=TA_LEFT,
        ))
        self.styles.add(ParagraphStyle(
            'SectionTitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=TEXT_DARK,
            fontName='Helvetica-Bold',
            spaceBefore=12,
            spaceAfter=6,
        ))
        self.styles.add(ParagraphStyle(
            'CellSubject',
            parent=self.styles['Normal'],
            fontSize=7.5,
            fontName='Helvetica-Bold',
            textColor=TEXT_DARK,
            alignment=TA_CENTER,
            leading=10,
        ))
        self.styles.add(ParagraphStyle(
            'CellTime',
            parent=self.styles['Normal'],
            fontSize=6.5,
            fontName='Helvetica',
            textColor=TEXT_MUTED,
            alignment=TA_CENTER,
            leading=9,
        ))
        self.styles.add(ParagraphStyle(
            'CellType',
            parent=self.styles['Normal'],
            fontSize=6,
            fontName='Helvetica',
            textColor=TEXT_MUTED,
            alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            'LegendItem',
            parent=self.styles['Normal'],
            fontSize=8,
            fontName='Helvetica',
            textColor=TEXT_DARK,
        ))
        self.styles.add(ParagraphStyle(
            'FooterText',
            parent=self.styles['Normal'],
            fontSize=7.5,
            textColor=TEXT_MUTED,
            fontName='Helvetica',
            alignment=TA_CENTER,
        ))

    # ── Entrée publique ───────────────────────────────────────────────────

    async def generate_pdf(self, plan_id: str, user: User) -> BytesIO:
        try:
            return await asyncio.wait_for(
                self._generate_pdf_internal(plan_id, user),
                timeout=self.TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"PDF generation exceeded {self.TIMEOUT_SECONDS}s")

    async def _generate_pdf_internal(self, plan_id: str, user: User) -> BytesIO:
        # Récupérer le plan par UUID
        plan = self.db.query(StudyPlan).filter(
            StudyPlan.plan_id == plan_id,
            StudyPlan.user_id == user.id,
        ).first()
        if not plan:
            raise ValueError(f"Plan {plan_id} introuvable")

        # Sessions
        sessions = self.db.query(StudySession).filter(
            StudySession.study_plan_id == plan.id,
        ).order_by(StudySession.day, StudySession.start_time).all()

        # Calculer la palette couleurs par matière
        subject_names = list(dict.fromkeys(
            s.subject.name for s in sessions if s.subject
        ))
        subject_colors = {
            name: SUBJECT_PALETTE[i % len(SUBJECT_PALETTE)]
            for i, name in enumerate(subject_names)
        }

        buffer = BytesIO()
        page_size = landscape(A4)
        margin = 1.4 * cm

        doc = SimpleDocTemplate(
            buffer,
            pagesize=page_size,
            leftMargin=margin,
            rightMargin=margin,
            topMargin=1.2 * cm,
            bottomMargin=1.8 * cm,
            title=f"Plan d'etude - {user.name}",
            author="AI Study Planner",
        )

        # Mémoriser pour le canvas callback
        self._plan  = plan
        self._user  = user
        self._sessions = sessions

        story = []
        story.extend(self._build_hero(user, plan, sessions))
        story.append(Spacer(1, 0.6 * cm))
        story.extend(self._build_stats(sessions, plan))
        story.append(Spacer(1, 0.5 * cm))
        story.extend(self._build_calendar(sessions, subject_colors, page_size, margin))
        story.append(Spacer(1, 0.4 * cm))
        story.extend(self._build_legend(subject_colors))

        doc.build(
            story,
            onFirstPage=self._draw_page_background,
            onLaterPages=self._draw_page_background,
        )

        buffer.seek(0, 2)
        size = buffer.tell()
        if size > self.MAX_FILE_SIZE:
            raise ValueError(f"PDF trop volumineux: {size} bytes")
        buffer.seek(0)
        return buffer

    # ── Canvas callbacks ──────────────────────────────────────────────────

    def _draw_page_background(self, canv, doc):
        """Fond de page et footer."""
        w, h = doc.pagesize

        # Fond général très légèrement teinté
        canv.saveState()
        canv.setFillColor(colors.HexColor('#FAFAFA'))
        canv.rect(0, 0, w, h, fill=1, stroke=0)

        # ── Header band ──────────────────────────────────────────────────
        band_h = 3.0 * cm
        canv.setFillColor(BG_HEADER)
        canv.rect(0, h - band_h, w, band_h, fill=1, stroke=0)

        # Accent stripe
        canv.setFillColor(ACCENT)
        canv.rect(0, h - band_h - 4, w, 4, fill=1, stroke=0)

        # Cercles décoratifs dans le header
        canv.setFillColor(colors.HexColor('#312E81'))
        canv.setStrokeColor(colors.transparent)
        canv.circle(w - 1.5 * cm, h - 0.3 * cm, 2.2 * cm, fill=1, stroke=0)
        canv.circle(w - 3.8 * cm, h - 0.2 * cm, 1.2 * cm, fill=1, stroke=0)
        canv.circle(0.5 * cm, h - band_h + 0.3 * cm, 0.8 * cm, fill=1, stroke=0)

        # ── Footer ───────────────────────────────────────────────────────
        canv.setFillColor(BG_HEADER)
        canv.rect(0, 0, w, 1.3 * cm, fill=1, stroke=0)
        canv.setFillColor(ACCENT)
        canv.rect(0, 1.3 * cm, w, 2, fill=1, stroke=0)

        # Texte footer
        canv.setFillColor(TEXT_LIGHT)
        canv.setFont('Helvetica', 7)
        now = datetime.now().strftime('%d/%m/%Y %H:%M')
        canv.drawString(1.4 * cm, 0.5 * cm, f"AI Study Planner  |  Genere le {now}")
        page_num = canv.getPageNumber()
        canv.drawRightString(w - 1.4 * cm, 0.5 * cm, f"Page {page_num}")

        canv.restoreState()

    # ── Hero block (titre dans le header) ─────────────────────────────────

    def _build_hero(self, user: User, plan: StudyPlan, sessions: list) -> list:
        """Titre dans le header (positionné via Spacer négatif artifice)."""
        # Le header band est dessiné sur le canvas — on positionne le texte via Table
        week_start = plan.week_start
        week_end   = week_start + timedelta(days=6)

        title_para = Paragraph(
            f"Plan d'Etude  <font color='#818CF8'>|</font>  {user.name}",
            self.styles['HeroTitle'],
        )
        sub_para = Paragraph(
            f"Semaine du {week_start.strftime('%d %B %Y')} au {week_end.strftime('%d %B %Y')}",
            self.styles['HeroSub'],
        )
        # Conteneur transparent pour aligner avec le header (hauteur = band)
        data = [[title_para], [sub_para]]
        t = Table(data, colWidths=['100%'])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.transparent),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        return [t]

    # ── Stats ─────────────────────────────────────────────────────────────

    def _build_stats(self, sessions: list, plan: StudyPlan) -> list:
        total_hours = self._compute_total_hours(sessions)
        subjects    = list(dict.fromkeys(s.subject.name for s in sessions if s.subject))
        completed   = sum(1 for s in sessions if getattr(s, 'completed', False))

        boxes = [
            StatBox('Sessions', len(sessions),      PRIMARY,  4.5 * cm),
            StatBox('Heures totales', f'{total_hours:.1f}h', ACCENT,  4.5 * cm),
            StatBox('Matieres', len(subjects),       SUCCESS,  4.5 * cm),
            StatBox('Terminees', completed,          GOLD,    4.5 * cm),
            StatBox('Statut', 'Modifie' if plan.edited else 'Genere', TEXT_MUTED, 4.5 * cm),
        ]

        # On les dispose en une ligne via Table
        data = [boxes]
        t = Table(data, colWidths=[4.8 * cm] * 5)
        t.setStyle(TableStyle([
            ('ALIGN',        (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',   (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 0),
            ('LEFTPADDING',  (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND',   (0, 0), (-1, -1), colors.transparent),
        ]))
        return [t]

    # ── Calendrier ────────────────────────────────────────────────────────

    def _build_calendar(
        self,
        sessions: list,
        subject_colors: dict,
        page_size: tuple,
        margin: float,
    ) -> list:
        elements = []

        # Titre section
        elements.append(Paragraph('Planning de la semaine', self.styles['SectionTitle']))
        elements.append(ColoredRule(page_size[0] - 2 * margin, 2, PRIMARY))
        elements.append(Spacer(1, 4))

        # Regrouper par jour
        by_day = {d: [] for d in DAYS_OF_WEEK}
        for s in sessions:
            if s.day in by_day:
                by_day[s.day].append(s)
        for d in DAYS_OF_WEEK:
            by_day[d].sort(key=lambda s: s.start_time)

        max_slots = max((len(v) for v in by_day.values()), default=0)
        if max_slots == 0:
            elements.append(Paragraph(
                '<para align="center">Aucune session planifiee.</para>',
                self.styles['Normal'],
            ))
            return elements

        # Largeurs des colonnes
        usable_w = page_size[0] - 2 * margin
        label_w  = 1.6 * cm
        day_w    = (usable_w - label_w) / 7

        # ── En-tête ───────────────────────────────────────────────────────
        header_row = [Paragraph('<b>Creneau</b>', ParagraphStyle(
            'DH', parent=self.styles['Normal'], fontSize=7.5,
            fontName='Helvetica-Bold', textColor=TEXT_WHITE, alignment=TA_CENTER,
        ))]
        for day in DAYS_OF_WEEK:
            header_row.append(Paragraph(
                f'<b>{JOURS_FR[day]}</b>',
                ParagraphStyle('DH2', parent=self.styles['Normal'],
                               fontSize=7.5, fontName='Helvetica-Bold',
                               textColor=TEXT_WHITE, alignment=TA_CENTER),
            ))

        # ── Lignes de données ─────────────────────────────────────────────
        data_rows = [header_row]
        for i in range(max_slots):
            row = [Paragraph(
                f'<b>#{i+1}</b>',
                ParagraphStyle('Slot', parent=self.styles['Normal'],
                               fontSize=7, fontName='Helvetica-Bold',
                               textColor=colors.HexColor('#6B7280'), alignment=TA_CENTER),
            )]
            for day in DAYS_OF_WEEK:
                sessions_day = by_day[day]
                if i < len(sessions_day):
                    s = sessions_day[i]
                    subj = s.subject.name if s.subject else '?'
                    try:
                        start_str = s.start_time.strftime('%H:%M')
                        end_str   = s.end_time.strftime('%H:%M')
                    except AttributeError:
                        start_str = str(s.start_time)[:5]
                        end_str   = str(s.end_time)[:5]
                    cell_color_hex, _ = subject_colors.get(subj, ('#6366F1', '#EEF2FF'))
                    cell_para = Paragraph(
                        f'<font color="{cell_color_hex}"><b>{subj}</b></font><br/>'
                        f'<font color="#6B7280" size="6">{start_str} - {end_str}</font><br/>'
                        f'<font color="#9CA3AF" size="5.5">{s.task_type}</font>',
                        ParagraphStyle('Cell', parent=self.styles['Normal'],
                                       fontSize=7.5, alignment=TA_CENTER,
                                       leading=10, leftPadding=2, rightPadding=2),
                    )
                    row.append(cell_para)
                else:
                    row.append('')
            data_rows.append(row)

        col_widths = [label_w] + [day_w] * 7

        table = Table(data_rows, colWidths=col_widths, repeatRows=1)

        # Style de base
        ts = [
            # En-tête
            ('BACKGROUND',   (0, 0), (-1, 0), BG_HEADER),
            ('TEXTCOLOR',    (0, 0), (-1, 0), TEXT_WHITE),
            ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',     (0, 0), (-1, 0), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
            # Colonne label
            ('BACKGROUND',   (0, 1), (0, -1), BG_MID),
            ('FONTNAME',     (0, 1), (0, -1), 'Helvetica-Bold'),
            # Grille
            ('GRID',         (0, 0), (-1, -1), 0.4, BORDER_COLOR),
            ('LINEBELOW',    (0, 0), (-1, 0),  1.5, PRIMARY),
            # Alignement
            ('ALIGN',        (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
            # Padding
            ('TOPPADDING',   (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 5),
            ('LEFTPADDING',  (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]

        # Colorer le fond de chaque cellule non-vide avec la couleur de la matière (pâle)
        for row_idx in range(1, max_slots + 1):
            for col_idx, day in enumerate(DAYS_OF_WEEK, start=1):
                day_sessions = by_day[day]
                slot_idx = row_idx - 1
                if slot_idx < len(day_sessions):
                    s = day_sessions[slot_idx]
                    subj = s.subject.name if s.subject else '?'
                    _, bg_hex = subject_colors.get(subj, ('#6366F1', '#EEF2FF'))
                    ts.append((
                        'BACKGROUND',
                        (col_idx, row_idx), (col_idx, row_idx),
                        colors.HexColor(bg_hex),
                    ))

        table.setStyle(TableStyle(ts))
        elements.append(table)
        return elements

    # ── Légende matières ──────────────────────────────────────────────────

    def _build_legend(self, subject_colors: dict) -> list:
        if not subject_colors:
            return []

        elements = [
            Paragraph('Legende des matieres', self.styles['SectionTitle']),
            ColoredRule(10 * cm, 2, PRIMARY_LIGHT),
            Spacer(1, 6),
        ]

        legend_items = []
        for subj, (fg_hex, bg_hex) in subject_colors.items():
            swatch = Paragraph(
                f'<font color="{fg_hex}">&#9632;</font>  {subj}',
                ParagraphStyle('Leg', parent=self.styles['Normal'],
                               fontSize=8, fontName='Helvetica',
                               textColor=TEXT_DARK),
            )
            legend_items.append(swatch)

        # Disposer en grille 4 colonnes
        cols = 4
        rows = [legend_items[i:i+cols] for i in range(0, len(legend_items), cols)]
        # Padder la dernière ligne
        while len(rows[-1]) < cols:
            rows[-1].append('')

        t = Table(rows, colWidths=[6 * cm] * cols)
        t.setStyle(TableStyle([
            ('TOPPADDING',   (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 4),
            ('LEFTPADDING',  (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND',   (0, 0), (-1, -1), colors.white),
            ('BOX',          (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('INNERGRID',    (0, 0), (-1, -1), 0.3, BORDER_COLOR),
            ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(t)
        return elements

    # ── Utilitaires ───────────────────────────────────────────────────────

    @staticmethod
    def _compute_total_hours(sessions: list) -> float:
        total = 0
        for s in sessions:
            try:
                st = s.start_time
                et = s.end_time
                if hasattr(st, 'hour'):
                    start_min = st.hour * 60 + st.minute
                    end_min   = et.hour * 60 + et.minute
                else:
                    parts = str(st).split(':')
                    start_min = int(parts[0]) * 60 + int(parts[1])
                    parts = str(et).split(':')
                    end_min   = int(parts[0]) * 60 + int(parts[1])
                total += max(0, end_min - start_min)
            except Exception:
                pass
        return round(total / 60, 1)
