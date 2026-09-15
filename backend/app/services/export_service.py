"""
PDF Export Service — Premium Study Plan Generator for AI Study Planner
Landscape layout, clear typography, academic schedule integration, no overlap.
"""
from datetime import datetime, timedelta, date as date_type, time as time_type
from io import BytesIO
from typing import Optional, List, Dict
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
from app.models.student_profile import StudentProfile
from app.models.study_program import StudyProgram
from app.models.class_schedule import ClassSchedule
from app.models.user import User


# ─── Color Palette ─────────────────────────────────────────────────────────

PRIMARY       = colors.HexColor('#4F46E5')   # Indigo-600
PRIMARY_DARK  = colors.HexColor('#312E81')   # Indigo-900
PRIMARY_LIGHT = colors.HexColor('#818CF8')   # Indigo-400
ACCENT        = colors.HexColor('#7C3AED')   # Violet-600
BG_HEADER     = colors.HexColor('#1E1B4B')   # Indigo-950
BG_LIGHT      = colors.HexColor('#F8FAFC')   # Slate-50
BG_MID        = colors.HexColor('#EEF2FF')   # Indigo-50
BORDER_COLOR  = colors.HexColor('#E2E8F0')   # Slate-200
TEXT_DARK     = colors.HexColor('#0F172A')   # Slate-900
TEXT_MUTED    = colors.HexColor('#64748B')   # Slate-500
TEXT_WHITE    = colors.HexColor('#FFFFFF')
TEXT_LIGHT    = colors.HexColor('#C4B5FD')   # Violet-300
GOLD          = colors.HexColor('#F59E0B')   # Amber-500
SUCCESS       = colors.HexColor('#10B981')   # Emerald-500

# Academic fixed slot styling (Soft Navy Blue)
ACADEMIC_BG   = colors.HexColor('#DBEAFE')   # Blue-100
ACADEMIC_FG   = colors.HexColor('#1E3A8A')   # Blue-900

# Subject palette (10 distinct color pairs)
SUBJECT_PALETTE = [
    ('#2563EB', '#EFF6FF'),  # Blue
    ('#7C3AED', '#F5F3FF'),  # Violet
    ('#059669', '#ECFDF5'),  # Emerald
    ('#D97706', '#FFFBEB'),  # Amber
    ('#DC2626', '#FEF2F2'),  # Red
    ('#0891B2', '#ECFEFF'),  # Cyan
    ('#DB2777', '#FDF2F8'),  # Pink
    ('#EA580C', '#FFF7ED'),  # Orange
    ('#0D9488', '#F0FDFA'),  # Teal
    ('#4F46E5', '#EEF2FF'),  # Indigo
]

PDF_TRANSLATIONS = {
    'fr': {
        'days': {
            'Monday': 'Lundi',
            'Tuesday': 'Mardi',
            'Wednesday': 'Mercredi',
            'Thursday': 'Jeudi',
            'Friday': 'Vendredi',
            'Saturday': 'Samedi',
            'Sunday': 'Dimanche',
        },
        'title': "Plan d'Étude",
        'header_title': "Plan d'Étude",
        'week_subtitle': "Semaine du {start} au {end}",
        'program': "Filière",
        'program_label': "Filière",
        'generated_on': "Généré le",
        'page': "Page {page}",
        'page_prefix': "Page",
        'stats': {
            'ai_sessions': "Sessions IA",
            'academic_hours': "Cours Univ",
            'ai_hours': "Heures IA",
            'subjects': "Matières",
            'status': "Statut",
            'status_edited': "Modifié",
            'status_generated': "Généré",
        },
        'schedule_title': "Planning de la Semaine (Cours & Révisions IA)",
        'calendar_title': "Planning de la Semaine (Cours & Révisions IA)",
        'time_slot': "Créneau",
        'slot_label': "Créneau",
        'empty_schedule': "Aucune session ou cours planifié pour cette semaine.",
        'no_sessions': "Aucune session ou cours planifié pour cette semaine.",
        'academic_types': {
            'CM': 'Cours (CM)',
            'TD': 'TD (Travaux Dirigés)',
            'TP': 'TP (Travaux Pratiques)',
            'EXAM': 'Examen',
        },
        'study_tasks': {
            'lecture_review': 'Révision Cours',
            'exercise_practice': 'Exercices',
            'exam_preparation': 'Prépa Examen',
            'project_work': 'Projet',
            'reading': 'Lecture',
            'practice': 'Pratique',
            'university_class': 'Cours Univ',
        },
        'task_types': {
            'lecture_review': 'Révision Cours',
            'exercise_practice': 'Exercices',
            'exam_preparation': 'Prépa Examen',
            'project_work': 'Projet',
            'reading': 'Lecture',
            'practice': 'Pratique',
            'university_class': 'Cours Univ',
        },
        'legend': "Légende des Matières et Cours",
        'academic_class_legend': "Cours Universitaires Fixes (CM, TD, TP)",
        'fallback_study': "Étude IA",
        'fallback_subject': "Révision",
        'fallback_user': "Étudiant",
    },
    'en': {
        'days': {
            'Monday': 'Monday',
            'Tuesday': 'Tuesday',
            'Wednesday': 'Wednesday',
            'Thursday': 'Thursday',
            'Friday': 'Friday',
            'Saturday': 'Saturday',
            'Sunday': 'Sunday',
        },
        'title': "Study Plan",
        'header_title': "Study Plan",
        'week_subtitle': "Week from {start} to {end}",
        'program': "Program",
        'program_label': "Program",
        'generated_on': "Generated on",
        'page': "Page {page}",
        'page_prefix': "Page",
        'stats': {
            'ai_sessions': "AI Sessions",
            'academic_hours': "Univ Classes",
            'ai_hours': "AI Hours",
            'subjects': "Subjects",
            'status': "Status",
            'status_edited': "Edited",
            'status_generated': "Generated",
        },
        'schedule_title': "Weekly Schedule (Classes & AI Study)",
        'calendar_title': "Weekly Schedule (Classes & AI Study)",
        'time_slot': "Time Slot",
        'slot_label': "Time Slot",
        'empty_schedule': "No study sessions or classes scheduled for this week.",
        'no_sessions': "No study sessions or classes scheduled for this week.",
        'academic_types': {
            'CM': 'Lecture (CM)',
            'TD': 'Tutorial (TD)',
            'TP': 'Practical Work (TP)',
            'EXAM': 'Exam',
        },
        'study_tasks': {
            'lecture_review': 'Lecture Review',
            'exercise_practice': 'Exercises',
            'exam_preparation': 'Exam Prep',
            'project_work': 'Project',
            'reading': 'Reading',
            'practice': 'Practice',
            'university_class': 'Univ Class',
        },
        'task_types': {
            'lecture_review': 'Lecture Review',
            'exercise_practice': 'Exercises',
            'exam_preparation': 'Exam Prep',
            'project_work': 'Project',
            'reading': 'Reading',
            'practice': 'Practice',
            'university_class': 'Univ Class',
        },
        'legend': "Subjects & Courses Legend",
        'academic_class_legend': "Fixed University Classes (CM, TD, TP)",
        'fallback_study': "AI Study",
        'fallback_subject': "Study",
        'fallback_user': "Student",
    },
    'de': {
        'days': {
            'Monday': 'Montag',
            'Tuesday': 'Dienstag',
            'Wednesday': 'Mittwoch',
            'Thursday': 'Donnerstag',
            'Friday': 'Freitag',
            'Saturday': 'Samstag',
            'Sunday': 'Sonntag',
        },
        'title': "Studienplan",
        'header_title': "Studienplan",
        'week_subtitle': "Woche vom {start} bis {end}",
        'program': "Studiengang",
        'program_label': "Studiengang",
        'generated_on': "Erstellt am",
        'page': "Seite {page}",
        'page_prefix': "Seite",
        'stats': {
            'ai_sessions': "KI-Sitzungen",
            'academic_hours': "Vorlesungen",
            'ai_hours': "KI-Stunden",
            'subjects': "Fächer",
            'status': "Status",
            'status_edited': "Bearbeitet",
            'status_generated': "Generiert",
        },
        'schedule_title': "Wochenplan (Kurse & KI-Lernen)",
        'calendar_title': "Wochenplan (Kurse & KI-Lernen)",
        'time_slot': "Zeitfenster",
        'slot_label': "Zeitfenster",
        'empty_schedule': "Keine Lernsitzungen oder Vorlesungen für diese Woche geplant.",
        'no_sessions': "Keine Lernsitzungen oder Vorlesungen für diese Woche geplant.",
        'academic_types': {
            'CM': 'Vorlesung (CM)',
            'TD': 'Übung (TD)',
            'TP': 'Praktikum (TP)',
            'EXAM': 'Prüfung',
        },
        'study_tasks': {
            'lecture_review': 'Vorlesungswiederholung',
            'exercise_practice': 'Übungsaufgaben',
            'exam_preparation': 'Prüfungsvorbereitung',
            'project_work': 'Projektarbeit',
            'reading': 'Lektüre',
            'practice': 'Praxis',
            'university_class': 'Vorlesung',
        },
        'task_types': {
            'lecture_review': 'Vorlesungswiederholung',
            'exercise_practice': 'Übungsaufgaben',
            'exam_preparation': 'Prüfungsvorbereitung',
            'project_work': 'Projektarbeit',
            'reading': 'Lektüre',
            'practice': 'Praxis',
            'university_class': 'Vorlesung',
        },
        'legend': "Legende der Fächer und Vorlesungen",
        'academic_class_legend': "Feste Vorlesungen (CM, TD, TP)",
        'fallback_study': "KI-Lernen",
        'fallback_subject': "Lernen",
        'fallback_user': "Student",
    },
}

JOURS_FR = PDF_TRANSLATIONS['fr']['days']
DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


# ─── Flowables ─────────────────────────────────────────────────────────────

class ColoredRule(Flowable):
    """Decorative rule line."""
    def __init__(self, width, height=2, color=PRIMARY):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.color = color

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)


class StatBox(Flowable):
    """Clean, un-clipped Stat Box flowable with distinct label & value baselines."""
    def __init__(self, label, value, color=PRIMARY, width=4.8*cm, height=1.8*cm):
        Flowable.__init__(self)
        self.label = label
        self.value = value
        self.color = color
        self.width = width
        self.height = height

    def draw(self):
        c = self.canv
        w, h = self.width, self.height
        radius = 6

        # Card container
        c.setFillColor(colors.white)
        c.setStrokeColor(self.color)
        c.setLineWidth(1.2)
        c.roundRect(0, 0, w, h, radius, fill=1, stroke=1)

        # Top accent bar (3mm)
        c.setFillColor(self.color)
        c.setStrokeColor(colors.transparent)
        c.rect(0, h - 3.5, w, 3.5, fill=1, stroke=0)

        # Value text (centered, bold, 13pt)
        c.setFillColor(TEXT_DARK)
        c.setFont('Helvetica-Bold', 13)
        c.drawCentredString(w / 2, h * 0.46, str(self.value))

        # Label text (centered, muted, 7.5pt)
        c.setFillColor(TEXT_MUTED)
        c.setFont('Helvetica', 7.5)
        c.drawCentredString(w / 2, h * 0.18, str(self.label))


# ─── Export Service ─────────────────────────────────────────────────────────

class ExportService:
    """Service d'export PDF premium avec support des cours universitaires."""

    MAX_FILE_SIZE   = 10 * 1024 * 1024   # 10 MB
    TIMEOUT_SECONDS = 15
    DAYS_OF_WEEK    = DAYS_OF_WEEK

    def __init__(self, db: Session):
        self.db = db
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        self.styles.add(ParagraphStyle(
            'SectionTitle',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=TEXT_DARK,
            fontName='Helvetica-Bold',
            spaceBefore=8,
            spaceAfter=4,
        ))
        self.styles.add(ParagraphStyle(
            'LegendItem',
            parent=self.styles['Normal'],
            fontSize=8,
            fontName='Helvetica',
            textColor=TEXT_DARK,
        ))

    async def generate_pdf(self, plan_id: str, user: User, lang: str = "fr") -> BytesIO:
        try:
            return await asyncio.wait_for(
                self._generate_pdf_internal(plan_id, user, lang=lang),
                timeout=self.TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"PDF generation exceeded {self.TIMEOUT_SECONDS}s")

    async def _generate_pdf_internal(self, plan_id: str, user: User, lang: str = "fr") -> BytesIO:
        self.lang = (lang or 'fr').strip().lower()[:2]
        if self.lang not in PDF_TRANSLATIONS:
            self.lang = 'fr'
        self.t = PDF_TRANSLATIONS[self.lang]

        plan = self.db.query(StudyPlan).filter(
            StudyPlan.plan_id == plan_id,
            StudyPlan.user_id == user.id,
        ).first()
        if not plan:
            raise ValueError(f"Plan {plan_id} introuvable")

        # Personal AI study sessions
        sessions = self.db.query(StudySession).filter(
            StudySession.study_plan_id == plan.id,
        ).order_by(StudySession.day, StudySession.start_time).all()

        # University class schedule slots (ClassSchedule)
        profile = self.db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
        academic_slots = []
        program_name = None
        if profile and profile.filiere_id:
            prog = self.db.query(StudyProgram).filter(StudyProgram.id == profile.filiere_id).first()
            if prog:
                program_name = prog.name
                matching_prog_ids = [
                    p.id for p in self.db.query(StudyProgram.id).filter(
                        StudyProgram.name == prog.name,
                        StudyProgram.is_deleted == False
                    ).all()
                ]
            else:
                matching_prog_ids = [profile.filiere_id]

            base_query = self.db.query(ClassSchedule).filter(
                ClassSchedule.study_program_id.in_(matching_prog_ids),
                ClassSchedule.is_deleted == False
            )
            query = base_query
            if profile.cursus_id:
                query = query.filter((ClassSchedule.academic_track_id == profile.cursus_id) | (ClassSchedule.academic_track_id == None))
            if profile.current_semester:
                from app.models.semester import Semester
                sem_ids = [
                    s.id for s in self.db.query(Semester.id).filter(
                        Semester.semester_number == profile.current_semester,
                        Semester.is_deleted == False
                    ).all()
                ]
                if sem_ids:
                    query = query.filter((ClassSchedule.semester_id.in_(sem_ids)) | (ClassSchedule.semester_id == None))

            academic_slots = query.all()
            if not academic_slots and not profile.cursus_id:
                academic_slots = base_query.all()

        # Subject color palette mapping
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
            topMargin=3.4 * cm,   # Clear of the 3.0cm top canvas banner
            bottomMargin=1.4 * cm,
            title=f"{self.t['header_title']} - {user.name}",
            author="AI Study Planner",
        )

        # Store metadata for canvas header drawing
        self._user_name = user.name or self.t['fallback_user']
        week_start = plan.week_start
        week_end = week_start + timedelta(days=6)
        prog_info = f"  |  {self.t['program_label']}: {program_name}" if program_name else ""
        self._subtitle = self.t['week_subtitle'].format(
            start=week_start.strftime('%d/%m/%Y'),
            end=week_end.strftime('%d/%m/%Y')
        ) + prog_info

        story = []
        story.extend(self._build_stats(sessions, academic_slots, plan))
        story.append(Spacer(1, 0.4 * cm))
        story.extend(self._build_calendar(sessions, academic_slots, subject_colors, page_size, margin))
        story.append(Spacer(1, 0.3 * cm))
        story.extend(self._build_legend(subject_colors, has_academic=len(academic_slots) > 0))

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

    # ── Canvas Callback (Top Banner & Footer) ──────────────────────────────

    def _draw_page_background(self, canv, doc):
        w, h = doc.pagesize

        canv.saveState()
        canv.setFillColor(colors.HexColor('#F8FAFC'))
        canv.rect(0, 0, w, h, fill=1, stroke=0)

        # Top Header Banner (3.0 cm)
        band_h = 3.0 * cm
        canv.setFillColor(BG_HEADER)
        canv.rect(0, h - band_h, w, band_h, fill=1, stroke=0)

        # Decorative background circles
        canv.setFillColor(colors.HexColor('#312E81'))
        canv.circle(w - 1.5 * cm, h - 0.3 * cm, 2.2 * cm, fill=1, stroke=0)
        canv.circle(w - 3.8 * cm, h - 0.2 * cm, 1.2 * cm, fill=1, stroke=0)

        # Bottom accent line below top banner
        canv.setFillColor(ACCENT)
        canv.rect(0, h - band_h - 3, w, 3, fill=1, stroke=0)

        # ── Title & Subtitle drawn cleanly on canvas (No overflow/overlap) ──
        canv.setFillColor(TEXT_WHITE)
        canv.setFont('Helvetica-Bold', 17)
        canv.drawString(1.4 * cm, h - 1.3 * cm, f"{self.t['header_title']}  |  {self._user_name}")

        canv.setFillColor(TEXT_LIGHT)
        canv.setFont('Helvetica', 9.5)
        canv.drawString(1.4 * cm, h - 2.2 * cm, self._subtitle)

        # ── Footer Banner ──────────────────────────────────────────────────
        footer_h = 1.0 * cm
        canv.setFillColor(BG_HEADER)
        canv.rect(0, 0, w, footer_h, fill=1, stroke=0)
        canv.setFillColor(ACCENT)
        canv.rect(0, footer_h, w, 2, fill=1, stroke=0)

        canv.setFillColor(TEXT_LIGHT)
        canv.setFont('Helvetica', 7)
        now = datetime.now().strftime('%d/%m/%Y %H:%M')
        canv.drawString(1.4 * cm, 0.35 * cm, f"AI Study Planner  |  {self.t['generated_on']} {now}")
        canv.drawRightString(w - 1.4 * cm, 0.35 * cm, f"{self.t['page_prefix']} {canv.getPageNumber()}")

        canv.restoreState()

    # ── Stats Section ──────────────────────────────────────────────────────

    def _build_stats(self, sessions: list, academic_slots: list, plan: StudyPlan) -> list:
        total_ai_hours = self._compute_total_hours(sessions)
        total_academic_hours = self._compute_total_hours_academic(academic_slots)
        subjects = list(dict.fromkeys(s.subject.name for s in sessions if s.subject))
        completed = sum(1 for s in sessions if getattr(s, 'completed', False))

        status_text = self.t['stats']['status_edited'] if plan.edited else self.t['stats']['status_generated']
        boxes = [
            StatBox(self.t['stats']['ai_sessions'], len(sessions), PRIMARY, 4.8 * cm),
            StatBox(self.t['stats']['academic_hours'], f'{total_academic_hours:.1f}h', colors.HexColor('#2563EB'), 4.8 * cm),
            StatBox(self.t['stats']['ai_hours'], f'{total_ai_hours:.1f}h', ACCENT, 4.8 * cm),
            StatBox(self.t['stats']['subjects'], len(subjects), SUCCESS, 4.8 * cm),
            StatBox(self.t['stats']['status'], status_text, GOLD, 4.8 * cm),
        ]

        data = [boxes]
        t = Table(data, colWidths=[5.1 * cm] * 5)
        t.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('BACKGROUND', (0, 0), (-1, -1), colors.transparent),
        ]))
        return [t]

    # ── Calendar Section (Includes University Class Schedules) ───────────

    def _build_calendar(
        self,
        sessions: list,
        academic_slots: list,
        subject_colors: dict,
        page_size: tuple,
        margin: float,
    ) -> list:
        elements = []

        elements.append(Paragraph(self.t['calendar_title'], self.styles['SectionTitle']))
        elements.append(ColoredRule(page_size[0] - 2 * margin, 2, PRIMARY))
        elements.append(Spacer(1, 4))

        # Group both AI sessions and Academic Class Slots by Day
        by_day = {d: [] for d in DAYS_OF_WEEK}

        # Add AI sessions
        for s in sessions:
            if s.day in by_day:
                try:
                    st_str = s.start_time.strftime('%H:%M') if hasattr(s.start_time, 'strftime') else str(s.start_time)[:5]
                    et_str = s.end_time.strftime('%H:%M') if hasattr(s.end_time, 'strftime') else str(s.end_time)[:5]
                except Exception:
                    st_str, et_str = '00:00', '00:00'
                
                subj_name = s.subject.name if s.subject else self.t['fallback_subject']
                fg_hex, bg_hex = subject_colors.get(subj_name, ('#4F46E5', '#EEF2FF'))
                task_label = self.t['task_types'].get(s.task_type, s.task_type or self.t['fallback_study'])
                
                by_day[s.day].append({
                    'is_academic': False,
                    'title': subj_name,
                    'time_str': f"{st_str} - {et_str}",
                    'sub_info': task_label,
                    'fg_hex': fg_hex,
                    'bg_hex': bg_hex,
                    'sort_key': st_str,
                })

        # Add Fixed University Class Slots
        for cs in academic_slots:
            if cs.day_of_week in by_day:
                try:
                    st_str = cs.start_time.strftime('%H:%M') if hasattr(cs.start_time, 'strftime') else str(cs.start_time)[:5]
                    et_str = cs.end_time.strftime('%H:%M') if hasattr(cs.end_time, 'strftime') else str(cs.end_time)[:5]
                except Exception:
                    st_str, et_str = '00:00', '00:00'
                
                type_labels = self.t['academic_types']
                type_label = type_labels.get(cs.session_type, cs.session_type or type_labels.get('CM', 'Cours'))
                room_str = f" ({cs.room_location})" if cs.room_location else ""
                by_day[cs.day_of_week].append({
                    'is_academic': True,
                    'title': cs.course_name,
                    'time_str': f"{st_str} - {et_str}",
                    'sub_info': f"🏛️ {type_label}{room_str}",
                    'fg_hex': '#1E3A8A', # Academic Dark Navy
                    'bg_hex': '#DBEAFE', # Academic Soft Blue
                    'sort_key': st_str,
                })

        # Sort each day by start time
        for d in DAYS_OF_WEEK:
            by_day[d].sort(key=lambda item: item['sort_key'])

        max_slots = max((len(v) for v in by_day.values()), default=0)
        if max_slots == 0:
            elements.append(Paragraph(
                f'<para align="center">{self.t["no_sessions"]}</para>',
                self.styles['Normal'],
            ))
            return elements

        usable_w = page_size[0] - 2 * margin
        label_w  = 1.6 * cm
        day_w    = (usable_w - label_w) / 7

        # Table Header Row
        header_row = [Paragraph(f'<b>{self.t["slot_label"]}</b>', ParagraphStyle(
            'DH', parent=self.styles['Normal'], fontSize=7.5,
            fontName='Helvetica-Bold', textColor=TEXT_WHITE, alignment=TA_CENTER,
        ))]
        for day in DAYS_OF_WEEK:
            header_row.append(Paragraph(
                f'<b>{self.t["days"][day]}</b>',
                ParagraphStyle('DH2', parent=self.styles['Normal'],
                               fontSize=7.5, fontName='Helvetica-Bold',
                               textColor=TEXT_WHITE, alignment=TA_CENTER),
            ))

        # Data Rows
        data_rows = [header_row]
        for i in range(max_slots):
            row = [Paragraph(
                f'<b>#{i+1}</b>',
                ParagraphStyle('Slot', parent=self.styles['Normal'],
                               fontSize=7, fontName='Helvetica-Bold',
                               textColor=colors.HexColor('#64748B'), alignment=TA_CENTER),
            )]
            for day in DAYS_OF_WEEK:
                day_events = by_day[day]
                if i < len(day_events):
                    evt = day_events[i]
                    cell_para = Paragraph(
                        f'<font color="{evt["fg_hex"]}"><b>{evt["title"]}</b></font><br/>'
                        f'<font color="#475569" size="6">{evt["time_str"]}</font><br/>'
                        f'<font color="{evt["fg_hex"]}" size="5.5"><b>{evt["sub_info"]}</b></font>',
                        ParagraphStyle('Cell', parent=self.styles['Normal'],
                                       fontSize=7.5, alignment=TA_CENTER,
                                       leading=9.5, leftPadding=2, rightPadding=2),
                    )
                    row.append(cell_para)
                else:
                    row.append('')
            data_rows.append(row)

        col_widths = [label_w] + [day_w] * 7
        table = Table(data_rows, colWidths=col_widths, repeatRows=1)

        ts = [
            ('BACKGROUND', (0, 0), (-1, 0), BG_HEADER),
            ('TEXTCOLOR', (0, 0), (-1, 0), TEXT_WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
            ('BACKGROUND', (0, 1), (0, -1), BG_MID),
            ('GRID', (0, 0), (-1, -1), 0.4, BORDER_COLOR),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, PRIMARY),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ]

        # Apply specific background colors per cell event
        for row_idx in range(1, max_slots + 1):
            for col_idx, day in enumerate(DAYS_OF_WEEK, start=1):
                day_events = by_day[day]
                slot_idx = row_idx - 1
                if slot_idx < len(day_events):
                    evt = day_events[slot_idx]
                    ts.append((
                        'BACKGROUND',
                        (col_idx, row_idx), (col_idx, row_idx),
                        colors.HexColor(evt['bg_hex']),
                    ))

        table.setStyle(TableStyle(ts))
        elements.append(table)
        return elements

    # ── Legend Section ─────────────────────────────────────────────────────

    def _build_legend(self, subject_colors: dict, has_academic: bool = False) -> list:
        elements = [
            Paragraph(self.t['legend'], self.styles['SectionTitle']),
            ColoredRule(10 * cm, 2, PRIMARY_LIGHT),
            Spacer(1, 4),
        ]

        legend_items = []
        
        # Include Academic Course Legend Swatch if academic slots exist
        if has_academic:
            legend_items.append(Paragraph(
                f'<font color="#1E3A8A">&#9632;</font>  <b>🏛️ {self.t["academic_class_legend"]}</b>',
                ParagraphStyle('LegAcad', parent=self.styles['Normal'],
                               fontSize=8, fontName='Helvetica-Bold', textColor=colors.HexColor('#1E3A8A')),
            ))

        for subj, (fg_hex, bg_hex) in subject_colors.items():
            swatch = Paragraph(
                f'<font color="{fg_hex}">&#9632;</font>  {subj}',
                ParagraphStyle('Leg', parent=self.styles['Normal'],
                               fontSize=8, fontName='Helvetica',
                               textColor=TEXT_DARK),
            )
            legend_items.append(swatch)

        if not legend_items:
            return []

        cols = 3
        rows = [legend_items[i:i+cols] for i in range(0, len(legend_items), cols)]
        while len(rows[-1]) < cols:
            rows[-1].append('')

        t = Table(rows, colWidths=[8 * cm] * cols)
        t.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, BORDER_COLOR),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(t)
        return elements

    # ── Utilities ──────────────────────────────────────────────────────────

    @staticmethod
    def _compute_total_hours(sessions: list) -> float:
        total = 0
        for s in sessions:
            try:
                st, et = s.start_time, s.end_time
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

    @staticmethod
    def _compute_total_hours_academic(academic_slots: list) -> float:
        total = 0
        for cs in academic_slots:
            try:
                st, et = cs.start_time, cs.end_time
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
