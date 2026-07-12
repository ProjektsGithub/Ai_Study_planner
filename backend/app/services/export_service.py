"""
PDF Export Service for Study Plans
Generates formatted weekly calendar PDFs
"""
from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional
import asyncio

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

from sqlalchemy.orm import Session
from app.models.study_plan import StudyPlan
from app.models.study_session import StudySession
from app.models.user import User


class ExportService:
    """Service for exporting study plans to PDF"""
    
    # Constants
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
    TIMEOUT_SECONDS = 5
    MIN_FONT_SIZE = 10
    
    # Days of week
    DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Colors for subjects (matching frontend)
    SUBJECT_COLORS = [
        colors.HexColor('#3B82F6'),  # blue
        colors.HexColor('#10B981'),  # green
        colors.HexColor('#8B5CF6'),  # purple
        colors.HexColor('#EC4899'),  # pink
        colors.HexColor('#F59E0B'),  # yellow
        colors.HexColor('#6366F1'),  # indigo
        colors.HexColor('#EF4444'),  # red
        colors.HexColor('#14B8A6'),  # teal
        colors.HexColor('#F97316'),  # orange
        colors.HexColor('#06B6D4'),  # cyan
    ]
    
    def __init__(self, db: Session):
        self.db = db
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1F2937'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#6B7280'),
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#9CA3AF'),
            alignment=TA_CENTER
        ))
    
    async def generate_pdf(
        self,
        plan_id: int,
        user: User
    ) -> BytesIO:
        """
        Generate PDF for a study plan
        
        Args:
            plan_id: Study plan ID
            user: User object
            
        Returns:
            BytesIO: PDF file buffer
            
        Raises:
            ValueError: If plan not found or generation fails
            TimeoutError: If generation exceeds timeout
        """
        try:
            # Apply timeout
            return await asyncio.wait_for(
                self._generate_pdf_internal(plan_id, user),
                timeout=self.TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"PDF generation exceeded {self.TIMEOUT_SECONDS} seconds")
    
    async def _generate_pdf_internal(
        self,
        plan_id: int,
        user: User
    ) -> BytesIO:
        """Internal PDF generation logic"""
        # Fetch study plan
        plan = self.db.query(StudyPlan).filter(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == user.id
        ).first()
        
        if not plan:
            raise ValueError(f"Study plan {plan_id} not found")
        
        # Fetch sessions
        sessions = self.db.query(StudySession).filter(
            StudySession.study_plan_id == plan_id
        ).all()
        
        # Create PDF buffer
        buffer = BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Build content
        story = []
        
        # Add header
        story.extend(self._create_header(user, plan))
        
        # Add calendar
        if sessions:
            story.extend(self._create_calendar(sessions))
        else:
            story.append(self._create_empty_message())
        
        # Add summary
        story.extend(self._create_summary(plan, sessions))
        
        # Build PDF
        doc.build(
            story,
            onFirstPage=self._add_footer,
            onLaterPages=self._add_footer
        )
        
        # Check file size
        buffer.seek(0, 2)  # Seek to end
        size = buffer.tell()
        if size > self.MAX_FILE_SIZE:
            raise ValueError(f"PDF size ({size} bytes) exceeds limit ({self.MAX_FILE_SIZE} bytes)")
        
        buffer.seek(0)  # Reset to beginning
        return buffer
    
    def _create_header(self, user: User, plan: StudyPlan) -> list:
        """Create PDF header"""
        elements = []
        
        # Title
        title = Paragraph(
            f"📚 Plan d'Étude - {user.full_name or user.email}",
            self.styles['CustomTitle']
        )
        elements.append(title)
        
        # Week info
        week_start = plan.week_start
        week_end = week_start + timedelta(days=6)
        subtitle = Paragraph(
            f"Semaine du {week_start.strftime('%d/%m/%Y')} au {week_end.strftime('%d/%m/%Y')}",
            self.styles['CustomSubtitle']
        )
        elements.append(subtitle)
        
        # Summary line
        summary = Paragraph(
            f"Total: {plan.total_hours:.1f}h | Créé le {plan.created_at.strftime('%d/%m/%Y à %H:%M')}",
            self.styles['Normal']
        )
        elements.append(summary)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _create_calendar(self, sessions: list) -> list:
        """Create calendar grid"""
        elements = []
        
        # Group sessions by day
        sessions_by_day = {day: [] for day in self.DAYS_OF_WEEK}
        for session in sessions:
            sessions_by_day[session.day].append(session)
        
        # Sort sessions by start time within each day
        for day in self.DAYS_OF_WEEK:
            sessions_by_day[day].sort(key=lambda s: s.start_time)
        
        # Create table data
        data = []
        
        # Header row
        header = ['Jour'] + self.DAYS_OF_WEEK
        data.append(header)
        
        # Find max sessions in any day
        max_sessions = max(len(sessions_by_day[day]) for day in self.DAYS_OF_WEEK)
        
        # Create rows for each session slot
        for i in range(max_sessions):
            row = [f"Session {i+1}"]
            for day in self.DAYS_OF_WEEK:
                if i < len(sessions_by_day[day]):
                    session = sessions_by_day[day][i]
                    cell_text = (
                        f"{session.subject.name}\n"
                        f"{session.start_time} - {session.end_time}\n"
                        f"{session.task_type}"
                    )
                    row.append(cell_text)
                else:
                    row.append('')
            data.append(row)
        
        # Create table
        col_widths = [2*cm] + [2.3*cm] * 7
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        # Style table
        table_style = TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # First column
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#F3F4F6')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (0, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            
            # Data cells
            ('FONTSIZE', (1, 1), (-1, -1), 8),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ])
        
        table.setStyle(table_style)
        elements.append(table)
        
        return elements
    
    def _create_empty_message(self) -> Paragraph:
        """Create message for empty calendar"""
        return Paragraph(
            "<para align='center'><b>Aucune session planifiée</b><br/>"
            "Ce plan d'étude ne contient aucune session.</para>",
            self.styles['Normal']
        )
    
    def _create_summary(self, plan: StudyPlan, sessions: list) -> list:
        """Create summary section"""
        elements = []
        
        elements.append(Spacer(1, 1*cm))
        
        # Summary title
        summary_title = Paragraph("<b>Résumé</b>", self.styles['Heading2'])
        elements.append(summary_title)
        elements.append(Spacer(1, 0.3*cm))
        
        # Statistics
        num_sessions = len(sessions)
        total_hours = plan.total_hours
        subjects = set(s.subject.name for s in sessions)
        num_subjects = len(subjects)
        
        stats_data = [
            ['Nombre de sessions:', str(num_sessions)],
            ['Total d\'heures:', f"{total_hours:.1f}h"],
            ['Matières:', str(num_subjects)],
            ['Statut:', 'Modifié' if plan.edited else 'Généré'],
        ]
        
        stats_table = Table(stats_data, colWidths=[5*cm, 5*cm])
        stats_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(stats_table)
        
        # Subject list
        if subjects:
            elements.append(Spacer(1, 0.5*cm))
            subjects_title = Paragraph("<b>Matières:</b>", self.styles['Normal'])
            elements.append(subjects_title)
            
            for subject in sorted(subjects):
                subject_para = Paragraph(f"• {subject}", self.styles['Normal'])
                elements.append(subject_para)
        
        return elements
    
    def _add_footer(self, canvas_obj, doc):
        """Add footer to page"""
        canvas_obj.saveState()
        
        # Page number
        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num}"
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.HexColor('#9CA3AF'))
        canvas_obj.drawCentredString(A4[0] / 2, 1*cm, text)
        
        # Timestamp
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        canvas_obj.drawRightString(A4[0] - 1.5*cm, 1*cm, f"Généré le {timestamp}")
        
        canvas_obj.restoreState()
