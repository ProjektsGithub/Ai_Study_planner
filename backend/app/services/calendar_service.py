"""
Calendar Service — Export iCal (.ics) des plans d'étude
Compatible Google Calendar, Apple Calendar, Outlook
"""
from datetime import datetime, timedelta, timezone, date
from typing import Optional
import logging

from sqlalchemy.orm import Session
from app.models.study_plan import StudyPlan
from app.models.study_session import StudySession
from app.models.user import User

logger = logging.getLogger(__name__)

# Mapping jours français → numéro (lundi = 0)
DAY_MAP = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2,
    "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6,
}


class CalendarService:
    """Service de génération de fichiers iCalendar (.ics)"""

    def __init__(self, db: Session):
        self.db = db

    def generate_ics(self, plan_id: str, user: User) -> str:
        """
        Génère un fichier .ics pour un plan d'étude donné.

        Args:
            plan_id: UUID du plan d'étude (champ plan_id)
            user: Utilisateur authentifié

        Returns:
            Contenu du fichier .ics en chaîne de caractères

        Raises:
            ValueError: Si le plan n'est pas trouvé
        """
        plan = self.db.query(StudyPlan).filter(
            StudyPlan.plan_id == plan_id,
            StudyPlan.user_id == user.id
        ).first()

        if not plan:
            raise ValueError(f"Plan d'étude {plan_id} introuvable")

        sessions = self.db.query(StudySession).filter(
            StudySession.study_plan_id == plan.id
        ).all()

        # Déterminer la date de début de semaine
        week_start: date = plan.week_start if hasattr(plan, "week_start") and plan.week_start else date.today()

        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//AI Study Planner//FR",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:Plan d'étude — semaine du {week_start.strftime('%d/%m/%Y')}",
            "X-WR-TIMEZONE:Europe/Paris",
        ]

        for session in sessions:
            event_lines = self._session_to_vevent(session, week_start, user)
            lines.extend(event_lines)

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines) + "\r\n"

    def _session_to_vevent(
        self,
        session: StudySession,
        week_start: date,
        user: User,
    ) -> list[str]:
        """Convertit une session d'étude en bloc VEVENT iCal."""
        try:
            # Résoudre la date exacte à partir du jour de la semaine
            day_offset = DAY_MAP.get(session.day, 0)
            session_date = week_start + timedelta(days=day_offset)

            # Parser les heures — start_time/end_time sont des objets Python time
            st = session.start_time
            et = session.end_time
            if hasattr(st, 'hour'):
                # Python time object
                sh, sm = st.hour, st.minute
                eh, em = et.hour, et.minute
            else:
                # Fallback si c'est une string "HH:MM"
                sh, sm = map(int, str(st).split(":"))
                eh, em = map(int, str(et).split(":"))

            dt_start = datetime(
                session_date.year, session_date.month, session_date.day,
                sh, sm, 0, tzinfo=timezone.utc
            )
            dt_end = datetime(
                session_date.year, session_date.month, session_date.day,
                eh, em, 0, tzinfo=timezone.utc
            )

            # Nom du sujet
            subject_name = session.subject.name if session.subject else "Matière inconnue"
            task_type = getattr(session, "task_type", "Étude")
            description = f"Matière: {subject_name}\\nType: {task_type}\\nPlan: AI Study Planner"

            uid = f"session-{session.id}-plan-{session.study_plan_id}@aiplanner"
            now_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            dt_start_str = dt_start.strftime("%Y%m%dT%H%M%SZ")
            dt_end_str = dt_end.strftime("%Y%m%dT%H%M%SZ")

            return [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now_stamp}",
                f"DTSTART:{dt_start_str}",
                f"DTEND:{dt_end_str}",
                f"SUMMARY:{subject_name} — {task_type}",
                f"DESCRIPTION:{description}",
                f"ORGANIZER;CN={user.name}:mailto:{user.email}",
                "STATUS:CONFIRMED",
                "TRANSP:OPAQUE",
                "END:VEVENT",
            ]
        except Exception as exc:
            logger.warning(f"Impossible de convertir la session {session.id}: {exc}")
            return []

    @staticmethod
    def build_google_calendar_url(
        title: str,
        start_dt: datetime,
        end_dt: datetime,
        description: str = "",
        location: str = "",
    ) -> str:
        """
        Génère un deep-link Google Calendar pour pré-remplir la création d'un événement.
        Format: https://calendar.google.com/calendar/render?action=TEMPLATE&...
        """
        fmt = "%Y%m%dT%H%M%S"
        dates = f"{start_dt.strftime(fmt)}/{end_dt.strftime(fmt)}"
        import urllib.parse
        params = {
            "action": "TEMPLATE",
            "text": title,
            "dates": dates,
            "details": description,
            "location": location,
        }
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v})
        return f"https://calendar.google.com/calendar/render?{query}"
