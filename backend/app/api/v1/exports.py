"""
Export API endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.export_service import ExportService

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("/plans/{plan_id}/pdf")
async def export_plan_to_pdf(
    plan_id: str,
    lang: Optional[str] = Query(None, description="Language code: fr, en, de"),
    accept_language: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export a study plan to PDF
    
    Args:
        plan_id: Study plan ID
        lang: Target language code ('fr', 'en', 'de')
        accept_language: Optional header fallback
        db: Database session
        current_user: Authenticated user
        
    Returns:
        PDF file as streaming response
        
    Raises:
        404: Plan not found
        500: PDF generation failed
    """
    try:
        # Determine language (Query param takes precedence, then header, default 'fr')
        target_lang = lang or (accept_language.split(',')[0].strip() if accept_language else 'fr')
        target_lang = target_lang.lower()[:2]
        if target_lang not in ['fr', 'en', 'de']:
            target_lang = 'fr'

        # Create export service
        export_service = ExportService(db)
        
        # Generate PDF
        pdf_buffer = await export_service.generate_pdf(plan_id, current_user, lang=target_lang)
        
        # Return as streaming response
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=study_plan_{plan_id}.pdf"
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except TimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {str(e)}"
        )
