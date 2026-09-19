"""
PDF Export Service — Premium Luminous Study Plan Generator for AI Study Planner
Light & Executive Academic design, 2-page complete dossier, rich pedagogical notes,
exam milestones countdown, and full multilingual support (FR, EN, DE).
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
    Spacer, PageBreak, KeepTogether, Flowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas as pdf_canvas

from sqlalchemy.orm import Session
from app.models.study_plan import StudyPlan
from app.models.study_session import StudySession
from app.models.student_profile import StudentProfile
from app.models.study_program import StudyProgram
from app.models.class_schedule import ClassSchedule
from app.models.subject import Subject
from app.models.user import User


# ─── Color Palette (Luminous Executive Light) ──────────────────────────────

PRIMARY          = colors.HexColor('#4F46E5')  # Indigo-600
PRIMARY_DARK     = colors.HexColor('#3730A3')  # Indigo-800
PRIMARY_LIGHT    = colors.HexColor('#EEF2FF')  # Indigo-50
PRIMARY_BORDER   = colors.HexColor('#C7D2FE')  # Indigo-200

ACCENT           = colors.HexColor('#7C3AED')  # Violet-600
ACCENT_LIGHT     = colors.HexColor('#F5F3FF')  # Violet-50
ACCENT_BORDER    = colors.HexColor('#DDD6FE')  # Violet-200

BG_PAGE          = colors.HexColor('#FFFFFF')  # Pure White
BG_LIGHT         = colors.HexColor('#F8FAFC')  # Slate-50
BG_MID           = colors.HexColor('#F1F5F9')  # Slate-100
BORDER_COLOR     = colors.HexColor('#E2E8F0')  # Slate-200
BORDER_DARK      = colors.HexColor('#CBD5E1')  # Slate-300

TEXT_DARK        = colors.HexColor('#0F172A')  # Slate-900 (High contrast)
TEXT_MID         = colors.HexColor('#334155')  # Slate-700
TEXT_MUTED       = colors.HexColor('#64748B')  # Slate-500
TEXT_WHITE       = colors.HexColor('#FFFFFF')

GOLD             = colors.HexColor('#D97706')  # Amber-600
GOLD_LIGHT       = colors.HexColor('#FFFBEB')  # Amber-50
GOLD_BORDER      = colors.HexColor('#FDE68A')  # Amber-200

SUCCESS          = colors.HexColor('#059669')  # Emerald-600
SUCCESS_LIGHT    = colors.HexColor('#ECFDF5')  # Emerald-50
SUCCESS_BORDER   = colors.HexColor('#A7F3D0')  # Emerald-200

DANGER           = colors.HexColor('#DC2626')  # Red-600
DANGER_LIGHT     = colors.HexColor('#FEF2F2')  # Red-50
DANGER_BORDER    = colors.HexColor('#FECACA')  # Red-200

# Academic fixed slot styling (Soft Navy Blue)
ACADEMIC_BG      = colors.HexColor('#EFF6FF')  # Blue-50
ACADEMIC_FG      = colors.HexColor('#1D4ED8')  # Blue-700
ACADEMIC_BORDER  = colors.HexColor('#BFDBFE')  # Blue-200

# Subject palette (10 distinct color pairs: foreground, background)
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


# ─── Multilingual Localization Dictionary ──────────────────────────────────

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
        'header_main': "PLAN D'ÉTUDE HEBDOMADAIRE",
        'week_subtitle': "Semaine du {start} au {end}",
        'program': "Filière",
        'program_label': "Filière",
        'semester_label': "Semestre",
        'cursus_label': "Cursus",
        'generated_on': "Généré le",
        'page': "Page {page}",
        'page_prefix': "Page",
        'page_x_of_y': "Page {page} sur {total}",
        'stats': {
            'ai_sessions': "Sessions IA",
            'academic_hours': "Cours Univ",
            'ai_hours': "Heures IA",
            'subjects': "Matières",
            'status': "Statut",
            'status_edited': "Modifié",
            'status_generated': "Généré",
        },
        'kpis': {
            'total_workload': "Charge Globale",
            'academic_classes': "Cours Univ (Fixes)",
            'ai_study_hours': "Travail Perso (IA)",
            'study_sessions': "Sessions d'Étude",
            'subjects_count': "Matières Traitées",
            'next_exam': "Prochain Examen",
        },
        'days_countdown': "J - {days}",
        'no_exam_scheduled': "Aucun proche",
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
        # Page 2 Translations
        'roadmap_title': "FEUILLE DE ROUTE PÉDAGOGIQUE & PROGRAMME DÉTAILLÉ",
        'ai_strategy_title': "💡 Stratégie d'Apprentissage & Conseils Pédagogiques IA",
        'ai_strategy_fallback': "Planning optimisé par l'IA pour équilibrer la charge hebdomadaire, consolider les notions clés et préparer efficacement vos examens.",
        'subject_goals_title': "Objectifs par Matière & Échéances d'Examens",
        'session_details_title': "Programme Détaillé des Sessions & Consignes de Révision (Notes IA)",
        'study_tips_title': "Méthode de Travail & Bonnes Pratiques",
        'study_tips_content': "<b>💡 Conseils pour maximiser l'efficacité :</b> Privilégiez le rappel actif (testez-vous sans relire passivement le cours) • Utilisez la technique Pomodoro (blocs de 25-50 min avec pauses actives) • Dormez suffisamment pour consolider la mémorisation à long terme.",
        'col_subject': "Matière",
        'col_hours': "Volume Prévu / Cible",
        'col_difficulty': "Difficulté & Priorité",
        'col_exam': "Échéance Examen",
        'col_status': "Statut",
        'col_check': "Fait",
        'col_day_time': "Jour & Horaire",
        'col_activity': "Activité",
        'col_directives': "Consignes & Thèmes de Révision (Notes IA)",
        'hours_suffix': "h",
        'status_in_progress': "En cours",
        'status_validated': "Validé",
        'status_retake': "Rattrapage",
        'priority_labels': {
            1: "Basse",
            2: "Moyenne",
            3: "Haute",
            4: "Prioritaire",
            5: "Critique",
        },
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
        'header_main': "WEEKLY STUDY PLAN",
        'week_subtitle': "Week from {start} to {end}",
        'program': "Program",
        'program_label': "Program",
        'semester_label': "Semester",
        'cursus_label': "Track",
        'generated_on': "Generated on",
        'page': "Page {page}",
        'page_prefix': "Page",
        'page_x_of_y': "Page {page} of {total}",
        'stats': {
            'ai_sessions': "AI Sessions",
            'academic_hours': "Univ Classes",
            'ai_hours': "AI Hours",
            'subjects': "Subjects",
            'status': "Status",
            'status_edited': "Edited",
            'status_generated': "Generated",
        },
        'kpis': {
            'total_workload': "Total Workload",
            'academic_classes': "Univ Classes (Fixed)",
            'ai_study_hours': "Self-Study (AI)",
            'study_sessions': "Study Sessions",
            'subjects_count': "Covered Subjects",
            'next_exam': "Next Exam",
        },
        'days_countdown': "D - {days}",
        'no_exam_scheduled': "None upcoming",
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
        # Page 2 Translations
        'roadmap_title': "PEDAGOGICAL ROADMAP & DETAILED ACTION PLAN",
        'ai_strategy_title': "💡 AI Learning Strategy & Pedagogical Guidance",
        'ai_strategy_fallback': "AI-optimized schedule designed to balance weekly workload, reinforce essential concepts, and prepare thoroughly for upcoming exams.",
        'subject_goals_title': "Subject Objectives & Exam Milestones",
        'session_details_title': "Detailed Session Program & Study Directives (AI Notes)",
        'study_tips_title': "Study Methodology & Best Practices",
        'study_tips_content': "<b>💡 Productivity tips:</b> Emphasize Active Recall (self-test without passively reading notes) • Use the Pomodoro technique (25-50 min focus blocks with active breaks) • Prioritize quality sleep to facilitate long-term memory consolidation.",
        'col_subject': "Subject",
        'col_hours': "Planned / Target Hours",
        'col_difficulty': "Difficulty & Priority",
        'col_exam': "Exam Date",
        'col_status': "Status",
        'col_check': "Done",
        'col_day_time': "Day & Time",
        'col_activity': "Activity",
        'col_directives': "Directives & Revision Topics (AI Notes)",
        'hours_suffix': "h",
        'status_in_progress': "In progress",
        'status_validated': "Completed",
        'status_retake': "Retake",
        'priority_labels': {
            1: "Low",
            2: "Medium",
            3: "High",
            4: "Priority",
            5: "Critical",
        },
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
        'header_main': "WÖCHENTLICHER STUDIENPLAN",
        'week_subtitle': "Woche vom {start} bis {end}",
        'program': "Studiengang",
        'program_label': "Studiengang",
        'semester_label': "Semester",
        'cursus_label': "Studiengang",
        'generated_on': "Erstellt am",
        'page': "Seite {page}",
        'page_prefix': "Seite",
        'page_x_of_y': "Seite {page} von {total}",
        'stats': {
            'ai_sessions': "KI-Sitzungen",
            'academic_hours': "Vorlesungen",
            'ai_hours': "KI-Stunden",
            'subjects': "Fächer",
            'status': "Status",
            'status_edited': "Bearbeitet",
            'status_generated': "Generiert",
        },
        'kpis': {
            'total_workload': "Gesamtbelastung",
            'academic_classes': "Vorlesungen (Fest)",
            'ai_study_hours': "Selbststudium (KI)",
            'study_sessions': "Lerneinheiten",
            'subjects_count': "Behandelte Fächer",
            'next_exam': "Nächste Prüfung",
        },
        'days_countdown': "T - {days}",
        'no_exam_scheduled': "Keine anstehende",
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
        # Page 2 Translations
        'roadmap_title': "PÄDAGOGISCHER LEITFADEN & DETAILLIERTER ABLAUFPLAN",
        'ai_strategy_title': "💡 KI-Lernstrategie & Pädagogische Empfehlungen",
        'ai_strategy_fallback': "KI-optimierter Studienplan zur ausgewogenen Verteilung der Wochenbelastung, Festigung zentraler Themen und gezielten Prüfungsvorbereitung.",
        'subject_goals_title': "Fachziele & Prüfungstermine",
        'session_details_title': "Detailliertes Sitzungsprogramm & Lernanweisungen (KI-Notizen)",
        'study_tips_title': "Arbeitsmethodik & Best Practices",
        'study_tips_content': "<b>💡 Empfehlungen für maximale Lerneffizienz:</b> Nutzen Sie aktives Erinnern (Selbsttests ohne Vorlage) • Setzen Sie die Pomodoro-Methode ein (25-50 Min. Fokus mit Bewegungspausen) • Ausreichend Schlaf ist essenziell für die Langzeitkonsolidierung.",
        'col_subject': "Fach",
        'col_hours': "Geplante / Soll-Stunden",
        'col_difficulty': "Schwierigkeit & Priorität",
        'col_exam': "Prüfungstermin",
        'col_status': "Status",
        'col_check': "Erledigt",
        'col_day_time': "Tag & Uhrzeit",
        'col_activity': "Aktivität",
        'col_directives': "Lerninhalte & Themenschwerpunkte (KI-Notizen)",
        'hours_suffix': " Std.",
        'status_in_progress': "Laufend",
        'status_validated': "Abgeschlossen",
        'status_retake': "Wiederholung",
        'priority_labels': {
            1: "Niedrig",
            2: "Mittel",
            3: "Hoch",
            4: "Prioritär",
            5: "Kritisch",
        },
    },
}

JOURS_FR = PDF_TRANSLATIONS['fr']['days']
DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


# ─── Numbered Canvas (Two-Pass Dynamic Page Numbers & Light Header/Footer) ──

class NumberedCanvas(pdf_canvas.Canvas):
    """
    Two-pass canvas that accurately calculates the total number of pages
    and draws an elegant, light-themed top accent bar and footer with 'Page X of Y'.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, num_pages: int):
        w, h = self._pagesize
        self.saveState()

        # 1. Subtle, elegant top accent bar (3.5 pt)
        self.setFillColor(PRIMARY)
        self.rect(0, h - 3.5, w, 3.5, fill=1, stroke=0)

        # 2. Crisp, light footer
        footer_y = 0.7 * cm
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.6)
        self.line(1.2 * cm, footer_y + 0.4 * cm, w - 1.2 * cm, footer_y + 0.4 * cm)

        self.setFont('Helvetica', 7.5)
        self.setFillColor(TEXT_MUTED)
        now_str = datetime.now().strftime('%d/%m/%Y %H:%M')

        t_dict = getattr(self, 'custom_t', PDF_TRANSLATIONS['fr'])
        gen_prefix = t_dict.get('generated_on', 'Généré le')
        brand_text = f"AI Study Planner  •  {gen_prefix} {now_str}"
        self.drawString(1.2 * cm, footer_y, brand_text)

        page_pattern = t_dict.get('page_x_of_y', 'Page {page} sur {total}')
        page_str = page_pattern.format(page=self._pageNumber, total=num_pages)
        self.drawRightString(w - 1.2 * cm, footer_y, page_str)

        self.restoreState()


def get_numbered_canvas_class(translation_dict: dict):
    class LocalizedNumberedCanvas(NumberedCanvas):
        custom_t = translation_dict
    return LocalizedNumberedCanvas


# ─── Flowables ─────────────────────────────────────────────────────────────

class ColoredRule(Flowable):
    """Decorative rule line."""
    def __init__(self, width, height=1.5, color=PRIMARY):
        super().__init__()
        self.width = width
        self.height = height
        self.color = color

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)


class StatBox(Flowable):
    """Clean, luminous Stat Card with top accent bar, bold value and muted label."""
    def __init__(self, label: str, value: str, color=PRIMARY, width=4.3*cm, height=1.4*cm):
        super().__init__()
        self.label = str(label)
        self.value = str(value)
        self.color = color
        self.width = width
        self.height = height

    def draw(self):
        c = self.canv
        w, h = self.width, self.height
        radius = 5

        # Card container (White background + soft border)
        c.setFillColor(colors.white)
        c.setStrokeColor(BORDER_COLOR)
        c.setLineWidth(0.8)
        c.roundRect(0, 0, w, h, radius, fill=1, stroke=1)

        # Top accent bar (3 pt)
        c.setFillColor(self.color)
        c.setStrokeColor(colors.transparent)
        c.rect(0, h - 3.0, w, 3.0, fill=1, stroke=0)

        # Value text (centered, bold, 11pt, high-contrast dark)
        c.setFillColor(TEXT_DARK)
        c.setFont('Helvetica-Bold', 11)
        c.drawCentredString(w / 2, h * 0.44, self.value)

        # Label text (centered, muted, 6.5pt)
        c.setFillColor(TEXT_MUTED)
        c.setFont('Helvetica', 6.5)
        c.drawCentredString(w / 2, h * 0.16, self.label.upper())


# ─── Export Service ─────────────────────────────────────────────────────────

class ExportService:
    """Service d'export PDF premium, lumineux et complet pour plans d'étude IA."""

    MAX_FILE_SIZE   = 10 * 1024 * 1024   # 10 MB
    TIMEOUT_SECONDS = 15
    DAYS_OF_WEEK    = DAYS_OF_WEEK

    def __init__(self, db: Optional[Session]):
        self.db = db
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        self.styles.add(ParagraphStyle(
            'HeaderTitle',
            parent=self.styles['Normal'],
            fontSize=13,
            textColor=TEXT_DARK,
            fontName='Helvetica-Bold',
            leading=15,
        ))
        self.styles.add(ParagraphStyle(
            'HeaderSubtitle',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=TEXT_MUTED,
            fontName='Helvetica',
            leading=10,
        ))
        self.styles.add(ParagraphStyle(
            'SectionTitle',
            parent=self.styles['Normal'],
            fontSize=9.5,
            textColor=PRIMARY_DARK,
            fontName='Helvetica-Bold',
            spaceBefore=4,
            spaceAfter=2,
        ))
        self.styles.add(ParagraphStyle(
            'LegendItem',
            parent=self.styles['Normal'],
            fontSize=7.5,
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

        plan = None
        sessions = []
        academic_slots = []
        subjects = []
        program_name = None
        cursus_name = None
        current_semester = None

        if self.db:
            q = self.db.query(StudyPlan).filter(StudyPlan.user_id == user.id)
            if isinstance(plan_id, int) or (isinstance(plan_id, str) and str(plan_id).isdigit()):
                q = q.filter((StudyPlan.id == int(plan_id)) | (StudyPlan.plan_id == str(plan_id)))
            else:
                q = q.filter(StudyPlan.plan_id == str(plan_id))
            plan = q.first()
            if not plan:
                raise ValueError(f"Plan {plan_id} introuvable")

            # Personal AI study sessions
            sessions = self.db.query(StudySession).filter(
                StudySession.study_plan_id == plan.id,
            ).order_by(StudySession.day, StudySession.start_time).all()

            # Student profile & academic curriculum
            profile = self.db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
            if profile:
                current_semester = profile.current_semester
                if profile.filiere_id:
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

            # User subjects list for goals & exams breakdown
            subjects = self.db.query(Subject).filter(
                Subject.user_id == user.id
            ).order_by(Subject.priority.desc(), Subject.name).all()

        if not plan:
            # Fallback mock plan for testing without DB
            class FallbackPlan:
                plan_id = "test-plan"
                week_start = date_type.today()
                edited = False
                summary = ""
                created_at = datetime.utcnow()
            plan = FallbackPlan()

        # Subject color palette mapping
        subject_names = list(dict.fromkeys(
            s.subject.name for s in sessions if getattr(s, 'subject', None) and getattr(s.subject, 'name', None)
        ))
        if not subject_names and subjects:
            subject_names = [s.name for s in subjects]

        subject_colors = {
            name: SUBJECT_PALETTE[i % len(SUBJECT_PALETTE)]
            for i, name in enumerate(subject_names)
        }

        buffer = BytesIO()
        page_size = landscape(A4)
        margin = 1.2 * cm

        doc = SimpleDocTemplate(
            buffer,
            pagesize=page_size,
            leftMargin=margin,
            rightMargin=margin,
            topMargin=1.2 * cm,
            bottomMargin=1.4 * cm,
            title=f"{self.t['header_title']} - {user.name or self.t['fallback_user']}",
            author="AI Study Planner",
        )

        user_name = user.name or user.full_name if hasattr(user, 'full_name') and user.full_name else (user.name or self.t['fallback_user'])
        user_email = getattr(user, 'email', '')

        # ── Construction du Story (Page 1 + Page 2) ─────────────────────────
        story = []

        # ════════════════════════════════════════════════════════════════════
        # PAGE 1 : VUE D'ENSEMBLE & EMPLOI DU TEMPS HEBDOMADAIRE (VISUEL)
        # ════════════════════════════════════════════════════════════════════
        story.extend(self._build_header_page1(
            user_name=user_name,
            user_email=user_email,
            program_name=program_name,
            semester=current_semester,
            plan=plan,
            page_size=page_size,
            margin=margin
        ))
        story.append(Spacer(1, 0.25 * cm))

        # KPIs bar (6 cards)
        story.extend(self._build_kpi_bar(sessions, academic_slots, subjects, plan, page_size, margin))
        story.append(Spacer(1, 0.3 * cm))

        # Master Calendar Grid (Classes + AI sessions)
        story.extend(self._build_calendar(sessions, academic_slots, subject_colors, page_size, margin))
        story.append(Spacer(1, 0.25 * cm))

        # Color & Activity Legend
        story.extend(self._build_legend(subject_colors, has_academic=len(academic_slots) > 0, page_size=page_size, margin=margin))

        # ════════════════════════════════════════════════════════════════════
        # PAGE 2 : FEUILLE DE ROUTE PÉDAGOGIQUE & CONSIGNES DÉTAILLÉES (IA)
        # ════════════════════════════════════════════════════════════════════
        story.append(PageBreak())

        story.extend(self._build_header_page2(user_name=user_name, plan=plan, page_size=page_size, margin=margin))
        story.append(Spacer(1, 0.25 * cm))

        # 1. AI Strategic Guidance & Pedagogical Reasoning (plan.summary)
        story.extend(self._build_ai_strategy(plan, page_size, margin))
        story.append(Spacer(1, 0.25 * cm))

        # 2. Subject Objectives & Exam Milestones Table
        story.extend(self._build_subject_goals(subjects, sessions, plan, page_size, margin))
        story.append(Spacer(1, 0.25 * cm))

        # 3. Detailed Daily Session Roadmap with Notes (session.notes) & Checkboxes
        story.extend(self._build_detailed_sessions(sessions, subject_colors, page_size, margin))
        story.append(Spacer(1, 0.25 * cm))

        # 4. Study Best Practices & Methodological Tips Box
        story.extend(self._build_study_tips(page_size, margin))

        # ── Document Build avec NumberedCanvas ──────────────────────────────
        canvas_maker = get_numbered_canvas_class(self.t)
        doc.build(story, canvasmaker=canvas_maker)

        buffer.seek(0, 2)
        size = buffer.tell()
        if size > self.MAX_FILE_SIZE:
            raise ValueError(f"PDF trop volumineux: {size} bytes")
        buffer.seek(0)
        return buffer

    # ── Page 1 : En-tête Luminous ──────────────────────────────────────────

    def _build_header_page1(
        self,
        user_name: str,
        user_email: str,
        program_name: Optional[str],
        semester: Optional[int],
        plan: StudyPlan,
        page_size: tuple,
        margin: float
    ) -> list:
        usable_w = page_size[0] - 2 * margin
        week_start = getattr(plan, 'week_start', None) or getattr(plan, 'week_start_date', None) or date_type.today()
        week_end = week_start + timedelta(days=6)

        left_para = Paragraph(
            f'<b><font size="13" color="#0F172A">{self.t["header_main"]}</font></b><br/>'
            f'<font size="9" color="#4F46E5"><b>👤 {user_name}</b></font>'
            f'{f" <font size=7.5 color=\"#64748B\">({user_email})</font>" if user_email else ""}',
            self.styles['HeaderTitle']
        )

        prog_parts = []
        if program_name:
            prog_parts.append(f"{self.t['program_label']}: {program_name}")
        if semester:
            prog_parts.append(f"{self.t['semester_label']} {semester}")
        status_label = self.t['stats']['status_edited'] if getattr(plan, 'edited', False) else self.t['stats']['status_generated']
        prog_parts.append(f"{self.t['stats']['status']}: {status_label}")
        meta_sub = " • ".join(prog_parts)

        right_para = Paragraph(
            f'<b><font size="8.5" color="#0F172A">🗓️ {self.t["week_subtitle"].format(start=week_start.strftime("%d/%m/%Y"), end=week_end.strftime("%d/%m/%Y"))}</font></b><br/>'
            f'<font size="7.5" color="#64748B">{meta_sub}</font>',
            ParagraphStyle('H1Right', parent=self.styles['HeaderSubtitle'], alignment=TA_RIGHT)
        )

        table = Table([[left_para, right_para]], colWidths=[usable_w * 0.55, usable_w * 0.45])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        return [table]

    # ── Page 1 : KPIs Bar (6 White Luminous Cards) ─────────────────────────

    def _build_kpi_bar(
        self,
        sessions: list,
        academic_slots: list,
        subjects: list,
        plan: StudyPlan,
        page_size: tuple,
        margin: float
    ) -> list:
        total_ai_hours = self._compute_total_hours(sessions)
        total_academic_hours = self._compute_total_hours_academic(academic_slots)
        total_workload = round(total_ai_hours + total_academic_hours, 1)

        distinct_subjects = list(dict.fromkeys(
            s.subject.name for s in sessions if getattr(s, 'subject', None) and getattr(s.subject, 'name', None)
        ))
        subj_count = len(distinct_subjects) if distinct_subjects else (len(subjects) if subjects else 0)

        # Calculate nearest exam
        nearest_exam_str = self.t['no_exam_scheduled']
        week_start = getattr(plan, 'week_start', None) or getattr(plan, 'week_start_date', None) or date_type.today()
        upcoming = []
        for s in (subjects or []):
            if getattr(s, 'exam_date', None):
                delta = (s.exam_date - week_start).days
                if delta >= 0:
                    upcoming.append(delta)
        if upcoming:
            nearest_exam_str = self.t['days_countdown'].format(days=min(upcoming))

        kpis = self.t.get('kpis', {})
        usable_w = page_size[0] - 2 * margin
        box_w = usable_w / 6 - 0.1 * cm

        boxes = [
            StatBox(kpis.get('total_workload', 'Charge Globale'), f"{total_workload:.1f}h", PRIMARY, box_w),
            StatBox(kpis.get('academic_classes', 'Cours Univ'), f"{total_academic_hours:.1f}h", colors.HexColor('#2563EB'), box_w),
            StatBox(kpis.get('ai_study_hours', 'Travail Perso'), f"{total_ai_hours:.1f}h", ACCENT, box_w),
            StatBox(kpis.get('study_sessions', 'Sessions'), f"{len(sessions)}", SUCCESS, box_w),
            StatBox(kpis.get('subjects_count', 'Matières'), f"{subj_count}", colors.HexColor('#0891B2'), box_w),
            StatBox(kpis.get('next_exam', 'Prochain Examen'), nearest_exam_str, GOLD, box_w),
        ]

        t = Table([boxes], colWidths=[usable_w / 6] * 6)
        t.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 1),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1),
            ('BACKGROUND', (0, 0), (-1, -1), colors.transparent),
        ]))
        return [t]

    # ── Page 1 : Calendar Section (Luminous Academic + AI Grid) ────────────

    def _build_calendar(
        self,
        sessions: list,
        academic_slots: list,
        subject_colors: dict,
        page_size: tuple,
        margin: float,
    ) -> list:
        usable_w = page_size[0] - 2 * margin
        elements = []

        elements.append(Paragraph(f'<b>{self.t["calendar_title"]}</b>', self.styles['SectionTitle']))
        elements.append(ColoredRule(usable_w, 1.5, PRIMARY))
        elements.append(Spacer(1, 3))

        # Group by day
        by_day = {d: [] for d in DAYS_OF_WEEK}

        # AI Sessions
        for s in sessions:
            if s.day in by_day:
                try:
                    st_str = s.start_time.strftime('%H:%M') if hasattr(s.start_time, 'strftime') else str(s.start_time)[:5]
                    et_str = s.end_time.strftime('%H:%M') if hasattr(s.end_time, 'strftime') else str(s.end_time)[:5]
                except Exception:
                    st_str, et_str = '00:00', '00:00'

                subj_name = s.subject.name if getattr(s, 'subject', None) and getattr(s.subject, 'name', None) else self.t['fallback_subject']
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

        # Academic slots (University fixed schedules)
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
                    'fg_hex': '#1D4ED8',  # Blue-700
                    'bg_hex': '#EFF6FF',  # Blue-50
                    'sort_key': st_str,
                })

        for d in DAYS_OF_WEEK:
            by_day[d].sort(key=lambda item: item['sort_key'])

        max_slots = max((len(v) for v in by_day.values()), default=0)
        if max_slots == 0:
            elements.append(Paragraph(
                f'<para align="center">{self.t["no_sessions"]}</para>',
                self.styles['Normal'],
            ))
            return elements

        label_w = 1.5 * cm
        day_w = (usable_w - label_w) / 7

        header_row = [Paragraph(f'<b><font color="white">{self.t["slot_label"]}</font></b>', ParagraphStyle(
            'DH', parent=self.styles['Normal'], fontSize=7.5,
            fontName='Helvetica-Bold', textColor=TEXT_WHITE, alignment=TA_CENTER,
        ))]
        for day in DAYS_OF_WEEK:
            header_row.append(Paragraph(
                f'<b><font color="white">{self.t["days"][day]}</font></b>',
                ParagraphStyle('DH2', parent=self.styles['Normal'],
                               fontSize=7.5, fontName='Helvetica-Bold',
                               textColor=TEXT_WHITE, alignment=TA_CENTER),
            ))

        data_rows = [header_row]
        for i in range(max_slots):
            row = [Paragraph(
                f'<b>#{i+1}</b>',
                ParagraphStyle('Slot', parent=self.styles['Normal'],
                               fontSize=7, fontName='Helvetica-Bold',
                               textColor=TEXT_MUTED, alignment=TA_CENTER),
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
                                       leading=9, leftPadding=1, rightPadding=1),
                    )
                    row.append(cell_para)
                else:
                    row.append('')
            data_rows.append(row)

        col_widths = [label_w] + [day_w] * 7
        table = Table(data_rows, colWidths=col_widths, repeatRows=1)

        ts = [
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), TEXT_WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
            ('BACKGROUND', (0, 1), (0, -1), BG_MID),
            ('GRID', (0, 0), (-1, -1), 0.4, BORDER_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 1),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1),
        ]

        # Apply soft pastel colors per event cell
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

    # ── Page 1 : Legend Section ────────────────────────────────────────────

    def _build_legend(
        self,
        subject_colors: dict,
        has_academic: bool = False,
        page_size: tuple = landscape(A4),
        margin: float = 1.2 * cm
    ) -> list:
        usable_w = page_size[0] - 2 * margin
        elements = [
            Paragraph(f'<b>{self.t["legend"]}</b>', self.styles['SectionTitle']),
            ColoredRule(8 * cm, 1.2, PRIMARY_BORDER),
            Spacer(1, 2),
        ]

        legend_items = []
        if has_academic:
            legend_items.append(Paragraph(
                f'<font color="#1D4ED8">&#9632;</font>  <b>🏛️ {self.t["academic_class_legend"]}</b>',
                ParagraphStyle('LegAcad', parent=self.styles['Normal'],
                               fontSize=7.5, fontName='Helvetica-Bold', textColor=ACADEMIC_FG),
            ))

        for subj, (fg_hex, bg_hex) in subject_colors.items():
            swatch = Paragraph(
                f'<font color="{fg_hex}">&#9632;</font>  <b>{subj}</b>',
                ParagraphStyle('Leg', parent=self.styles['Normal'],
                               fontSize=7.5, fontName='Helvetica', textColor=TEXT_DARK),
            )
            legend_items.append(swatch)

        if not legend_items:
            return []

        cols = 4
        rows = [legend_items[i:i+cols] for i in range(0, len(legend_items), cols)]
        while len(rows[-1]) < cols:
            rows[-1].append('')

        col_w = usable_w / cols
        t = Table(rows, colWidths=[col_w] * cols)
        t.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, BORDER_COLOR),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(t)
        return elements

    # ── Page 2 : En-tête Luminous ──────────────────────────────────────────

    def _build_header_page2(
        self,
        user_name: str,
        plan: StudyPlan,
        page_size: tuple,
        margin: float
    ) -> list:
        usable_w = page_size[0] - 2 * margin
        week_start = getattr(plan, 'week_start', None) or getattr(plan, 'week_start_date', None) or date_type.today()
        week_end = week_start + timedelta(days=6)

        left_para = Paragraph(
            f'<b><font size="12" color="#0F172A">{self.t["roadmap_title"]}</font></b>',
            self.styles['HeaderTitle']
        )
        right_para = Paragraph(
            f'<b><font size="8" color="#0F172A">👤 {user_name}</font></b> &nbsp;•&nbsp; '
            f'<font size="8" color="#64748B">{self.t["week_subtitle"].format(start=week_start.strftime("%d/%m/%Y"), end=week_end.strftime("%d/%m/%Y"))}</font>',
            ParagraphStyle('H2Right', parent=self.styles['HeaderSubtitle'], alignment=TA_RIGHT)
        )

        table = Table([[left_para, right_para]], colWidths=[usable_w * 0.65, usable_w * 0.35])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        return [table]

    # ── Page 2 : Stratégie IA & Conseils Pédagogiques (plan.summary) ────────

    def _build_ai_strategy(self, plan: StudyPlan, page_size: tuple, margin: float) -> list:
        usable_w = page_size[0] - 2 * margin
        summary_raw = getattr(plan, 'summary', '')
        if isinstance(summary_raw, str) and summary_raw.strip():
            summary_text = summary_raw.strip()
        else:
            summary_text = self.t['ai_strategy_fallback']

        card_para = Paragraph(
            f'<b><font size="8.5" color="#3730A3">{self.t["ai_strategy_title"]}</font></b><br/>'
            f'<font size="7.5" color="#1E293B">{summary_text}</font>',
            ParagraphStyle('AIStrategyPara', parent=self.styles['Normal'], leading=10.5)
        )

        table = Table([[card_para]], colWidths=[usable_w])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), PRIMARY_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.8, PRIMARY_BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        return [table]

    # ── Page 2 : Tableau Objectifs par Matière & Échéances d'Examens ────────

    def _build_subject_goals(
        self,
        subjects: list,
        sessions: list,
        plan: StudyPlan,
        page_size: tuple,
        margin: float
    ) -> list:
        usable_w = page_size[0] - 2 * margin
        elements = [
            Paragraph(f'<b>{self.t["subject_goals_title"]}</b>', self.styles['SectionTitle']),
            ColoredRule(usable_w, 1.2, PRIMARY_BORDER),
            Spacer(1, 2),
        ]

        # Calculate planned hours per subject
        planned_hours = {}
        for s in sessions:
            name = s.subject.name if getattr(s, 'subject', None) and getattr(s.subject, 'name', None) else self.t['fallback_subject']
            try:
                st, et = s.start_time, s.end_time
                if hasattr(st, 'hour'):
                    mins = (et.hour * 60 + et.minute) - (st.hour * 60 + st.minute)
                else:
                    p1 = str(st).split(':')
                    p2 = str(et).split(':')
                    mins = (int(p2[0]) * 60 + int(p2[1])) - (int(p1[0]) * 60 + int(p1[1]))
                planned_hours[name] = planned_hours.get(name, 0.0) + max(0, mins) / 60
            except Exception:
                pass

        week_start = getattr(plan, 'week_start', None) or getattr(plan, 'week_start_date', None) or date_type.today()

        header_cells = [
            Paragraph(f'<b>{self.t["col_subject"]}</b>', ParagraphStyle('TH1', fontSize=7, fontName='Helvetica-Bold', textColor=TEXT_DARK)),
            Paragraph(f'<b>{self.t["col_hours"]}</b>', ParagraphStyle('TH2', fontSize=7, fontName='Helvetica-Bold', textColor=TEXT_DARK, alignment=TA_CENTER)),
            Paragraph(f'<b>{self.t["col_difficulty"]}</b>', ParagraphStyle('TH3', fontSize=7, fontName='Helvetica-Bold', textColor=TEXT_DARK, alignment=TA_CENTER)),
            Paragraph(f'<b>{self.t["col_exam"]}</b>', ParagraphStyle('TH4', fontSize=7, fontName='Helvetica-Bold', textColor=TEXT_DARK, alignment=TA_CENTER)),
            Paragraph(f'<b>{self.t["col_status"]}</b>', ParagraphStyle('TH5', fontSize=7, fontName='Helvetica-Bold', textColor=TEXT_DARK, alignment=TA_CENTER)),
        ]
        table_rows = [header_cells]

        # Populate subjects rows
        display_subjects = subjects if subjects else []
        if not display_subjects and planned_hours:
            # Fallback to session subjects if subject model objects not queried
            class SubjProxy:
                def __init__(self, name, hours):
                    self.name = name
                    self.target_weekly_hours = hours
                    self.difficulty = 3
                    self.priority = 3
                    self.exam_date = None
                    self.validation_status = "in_progress"
            display_subjects = [SubjProxy(name, hrs) for name, hrs in planned_hours.items()]

        for subj in display_subjects[:8]:  # Keep compact
            name = getattr(subj, 'name', self.t['fallback_subject'])
            plan_h = planned_hours.get(name, 0.0)
            target_h = getattr(subj, 'target_weekly_hours', None) or 0.0
            diff = getattr(subj, 'difficulty', 3)
            prio = getattr(subj, 'priority', 3)
            exam_d = getattr(subj, 'exam_date', None)

            # Hours display
            hrs_text = f"<b>{plan_h:.1f}h</b>" + (f" / {target_h:.1f}h" if target_h > 0 else "")

            # Stars / Priority display
            stars = "★" * min(5, max(1, diff)) + "☆" * (5 - min(5, max(1, diff)))
            prio_name = self.t.get('priority_labels', {}).get(prio, f"P{prio}")
            diff_text = f"<font color='#D97706'>{stars}</font> <font color='#64748B' size=6>({prio_name})</font>"

            # Exam countdown display
            if exam_d:
                delta = (exam_d - week_start).days
                date_str = exam_d.strftime('%d/%m/%Y')
                if delta >= 0:
                    exam_text = f"<font color='#DC2626'><b>{date_str}</b></font> <font color='#D97706' size=6>({self.t['days_countdown'].format(days=delta)})</font>"
                else:
                    exam_text = f"<font color='#64748B'>{date_str} (Passé)</font>"
            else:
                exam_text = f"<font color='#94A3B8'>—</font>"

            # Validation status display
            val_stat = getattr(subj, 'validation_status', 'in_progress')
            stat_label = self.t.get('status_validated', 'Validé') if val_stat == 'validated' else self.t.get('status_in_progress', 'En cours')
            stat_color = '#059669' if val_stat == 'validated' else '#2563EB'
            stat_text = f"<font color='{stat_color}'><b>{stat_label}</b></font>"

            table_rows.append([
                Paragraph(f"<b>{name}</b>", ParagraphStyle('TR1', fontSize=7, textColor=TEXT_DARK)),
                Paragraph(hrs_text, ParagraphStyle('TR2', fontSize=7, alignment=TA_CENTER)),
                Paragraph(diff_text, ParagraphStyle('TR3', fontSize=7, alignment=TA_CENTER)),
                Paragraph(exam_text, ParagraphStyle('TR4', fontSize=7, alignment=TA_CENTER)),
                Paragraph(stat_text, ParagraphStyle('TR5', fontSize=7, alignment=TA_CENTER)),
            ])

        col_w = [usable_w * 0.30, usable_w * 0.16, usable_w * 0.18, usable_w * 0.20, usable_w * 0.16]
        t = Table(table_rows, colWidths=col_w)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BG_MID),
            ('GRID', (0, 0), (-1, -1), 0.4, BORDER_COLOR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(t)
        return elements

    # ── Page 2 : Programme Détaillé des Sessions avec Notes (Directives IA) ──

    def _build_detailed_sessions(
        self,
        sessions: list,
        subject_colors: dict,
        page_size: tuple,
        margin: float
    ) -> list:
        usable_w = page_size[0] - 2 * margin
        elements = [
            Paragraph(f'<b>{self.t["session_details_title"]}</b>', self.styles['SectionTitle']),
            ColoredRule(usable_w, 1.2, PRIMARY_BORDER),
            Spacer(1, 2),
        ]

        if not sessions:
            elements.append(Paragraph(
                f'<font color="#64748B" size=7.5>{self.t["no_sessions"]}</font>',
                self.styles['Normal']
            ))
            return elements

        header_cells = [
            Paragraph(f'<b>{self.t["col_check"]}</b>', ParagraphStyle('DH0', fontSize=7, fontName='Helvetica-Bold', textColor=TEXT_DARK, alignment=TA_CENTER)),
            Paragraph(f'<b>{self.t["col_day_time"]}</b>', ParagraphStyle('DH1', fontSize=7, fontName='Helvetica-Bold', textColor=TEXT_DARK)),
            Paragraph(f'<b>{self.t["col_subject"]}</b>', ParagraphStyle('DH2', fontSize=7, fontName='Helvetica-Bold', textColor=TEXT_DARK)),
            Paragraph(f'<b>{self.t["col_activity"]}</b>', ParagraphStyle('DH3', fontSize=7, fontName='Helvetica-Bold', textColor=TEXT_DARK)),
            Paragraph(f'<b>{self.t["col_directives"]}</b>', ParagraphStyle('DH4', fontSize=7, fontName='Helvetica-Bold', textColor=TEXT_DARK)),
        ]
        table_rows = [header_cells]

        # Sort sessions by day index, then start_time
        day_indices = {d: i for i, d in enumerate(DAYS_OF_WEEK)}
        sorted_sessions = sorted(
            sessions,
            key=lambda s: (day_indices.get(s.day, 99), str(s.start_time))
        )

        for s in sorted_sessions[:12]:  # Limit to 12 rows per page budget
            try:
                st_str = s.start_time.strftime('%H:%M') if hasattr(s.start_time, 'strftime') else str(s.start_time)[:5]
                et_str = s.end_time.strftime('%H:%M') if hasattr(s.end_time, 'strftime') else str(s.end_time)[:5]
            except Exception:
                st_str, et_str = '00:00', '00:00'

            day_translated = self.t['days'].get(s.day, s.day)
            subj_name = s.subject.name if getattr(s, 'subject', None) and getattr(s.subject, 'name', None) else self.t['fallback_subject']
            fg_hex, _ = subject_colors.get(subj_name, ('#4F46E5', '#EEF2FF'))
            task_label = self.t['task_types'].get(s.task_type, s.task_type or self.t['fallback_study'])

            # Physical checkbox [  ]
            is_completed = getattr(s, 'completed', False)
            check_mark = "☑" if is_completed else "[ &nbsp; ]"

            # Rich Notes from AI / curriculum topics
            notes_str = getattr(s, 'notes', '') or ''
            if not notes_str.strip():
                notes_str = f"{task_label} des chapitres en cours et consolidation méthodologique."

            table_rows.append([
                Paragraph(f"<b><font size=8>{check_mark}</font></b>", ParagraphStyle('D0', fontSize=8, alignment=TA_CENTER)),
                Paragraph(f"<b>{day_translated}</b><br/><font size=6 color='#64748B'>{st_str} - {et_str}</font>", ParagraphStyle('D1', fontSize=7, leading=8)),
                Paragraph(f"<b><font color='{fg_hex}'>{subj_name}</font></b>", ParagraphStyle('D2', fontSize=7)),
                Paragraph(f"<b>{task_label}</b>", ParagraphStyle('D3', fontSize=7, textColor=PRIMARY_DARK)),
                Paragraph(f"<font color='#334155'>{notes_str}</font>", ParagraphStyle('D4', fontSize=6.5, leading=8)),
            ])

        col_w = [usable_w * 0.05, usable_w * 0.15, usable_w * 0.17, usable_w * 0.15, usable_w * 0.48]
        t = Table(table_rows, colWidths=col_w)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BG_MID),
            ('GRID', (0, 0), (-1, -1), 0.4, BORDER_COLOR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(t)
        return elements

    # ── Page 2 : Encadré Conseils Méthodologiques ──────────────────────────

    def _build_study_tips(self, page_size: tuple, margin: float) -> list:
        usable_w = page_size[0] - 2 * margin
        tips_html = self.t.get('study_tips_content', '')

        tips_para = Paragraph(
            f'<font size="7" color="#334155">{tips_html}</font>',
            ParagraphStyle('TipsPara', parent=self.styles['Normal'], leading=9.5)
        )

        table = Table([[tips_para]], colWidths=[usable_w])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), SUCCESS_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.6, SUCCESS_BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        return [table]

    # ── Legacy Flowable Wrappers (Maintained for Backward Compatibility) ───

    def _build_stats(self, sessions: list, academic_slots: list, plan: StudyPlan) -> list:
        """Legacy helper maintained for test suites."""
        page_size = landscape(A4)
        margin = 1.2 * cm
        return self._build_kpi_bar(sessions, academic_slots, [], plan, page_size, margin)

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
