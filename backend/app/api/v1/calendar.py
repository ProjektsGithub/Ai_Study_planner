"""
Calendar API endpoints — Export iCal (.ics)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.calendar_service import CalendarService

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/plans/{plan_id}/ics", summary="Exporter le plan en fichier .ics (iCalendar)")
async def export_plan_to_ics(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Génère et retourne un fichier iCalendar (.ics) pour le plan d'étude donné.

    Le fichier est compatible avec Google Calendar, Apple Calendar et Outlook.
    Chaque session de travail devient un événement distinct.

    Args:
        plan_id: ID du plan d'étude
    Returns:
        Fichier .ics en réponse streaming (Content-Type: text/calendar)
    """
    try:
        service = CalendarService(db)
        ics_content = service.generate_ics(plan_id, current_user)

        filename = f"study_plan_{plan_id}.ics"
        return Response(
            content=ics_content,
            media_type="text/calendar; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "text/calendar; charset=utf-8",
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération du calendrier : {str(exc)}",
        )
