"""
Academic Profile Service
========================

Manages student academic profile data, linking students to the
university → filière → cursus → semester hierarchy from the
Super Admin Platform (same DB).

All Super Admin data is fetched via super_admin_client (cached 24h).
"""
from __future__ import annotations

import logging
from typing import List, Optional, Dict

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.student_profile import StudentProfile
from app.schemas.academic_profile import (
    AcademicProfileUpdate,
    AcademicProfileResponse,
    UniversityResponse,
    FiliereResponse,
    CursusResponse,
    SemesterStructure,
    SemesterInfo,
)
import app.services.super_admin_client as client

logger = logging.getLogger(__name__)


class AcademicProfileService:
    """Service for managing student academic profile linked to Super Admin Platform."""

    # ------------------------------------------------------------------
    # Reference data (proxy to super_admin_client with schema mapping)
    # ------------------------------------------------------------------

    def get_universities(self, db: Session) -> List[UniversityResponse]:
        """
        Fetch all active universities from Super Admin Platform.

        Requirements: 1.1, 17.2
        """
        raw = client.fetch_universities(db)
        return [
            UniversityResponse(
                id=u["id"],
                name=u["name"],
                code=u.get("code"),
            )
            for u in raw
        ]

    def get_filieres(self, db: Session, university_id: int) -> List[FiliereResponse]:
        """
        Fetch study programs (filières) for a university.

        Raises:
            HTTPException 404 if university not found / has no programs.

        Requirements: 1.2, 17.3
        """
        # Validate university exists
        universities = client.fetch_universities(db)
        valid_ids = {u["id"] for u in universities}
        if university_id not in valid_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"University with id={university_id} not found",
            )

        raw = client.fetch_filieres(db, university_id)
        return [
            FiliereResponse(
                id=f["id"],
                name=f["name"],
                code=f.get("code"),
                university_id=university_id,
            )
            for f in raw
        ]

    def get_cursus_options(self, db: Session, filiere_id: int) -> List[CursusResponse]:
        """
        Fetch academic tracks (cursus) for a study program.

        Raises:
            HTTPException 404 if filière not found / has no tracks.

        Requirements: 1.3, 17.4
        """
        raw = client.fetch_cursus(db, filiere_id)
        if not raw:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No cursus found for filiere_id={filiere_id}",
            )
        return [
            CursusResponse(
                id=c["id"],
                name=c["name"],
                code=c.get("code"),
                filiere_id=filiere_id,
                total_ects=c.get("total_ects"),
            )
            for c in raw
        ]

    def get_semester_structure(self, db: Session, cursus_id: int) -> SemesterStructure:
        """
        Fetch the complete semester structure for a cursus.

        Raises:
            HTTPException 404 if cursus not found.

        Requirements: 1.3, 17.5
        """
        raw = client.fetch_semester_structure(db, cursus_id)
        if raw is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cursus with id={cursus_id} not found",
            )
        return SemesterStructure(
            cursus_id=raw["cursus_id"],
            cursus_name=raw["cursus_name"],
            total_ects=raw.get("total_ects"),
            semesters=[
                SemesterInfo(
                    id=s["id"],
                    number=s["number"],
                    name=s.get("name"),
                    ects_required=s.get("ects_required"),
                )
                for s in raw["semesters"]
            ],
        )

    # ------------------------------------------------------------------
    # Profile read / write
    # ------------------------------------------------------------------

    def get_academic_profile(self, db: Session, user_id: int) -> AcademicProfileResponse:
        """
        Retrieve the academic profile fields for a student.
        Resolves human-readable names from Super Admin Platform.

        Requirements: 1.4, 1.5, 1.7
        """
        profile = (
            db.query(StudentProfile)
            .filter(StudentProfile.user_id == user_id)
            .first()
        )
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found",
            )

        # Resolve names from Super Admin Platform (cached)
        university_name = self._resolve_university_name(db, profile.university_id)
        filiere_name = self._resolve_filiere_name(db, profile.filiere_id)
        cursus_name = self._resolve_cursus_name(db, profile.cursus_id)

        return AcademicProfileResponse(
            university_id=profile.university_id,
            filiere_id=profile.filiere_id,
            cursus_id=profile.cursus_id,
            current_semester=profile.current_semester,
            academic_year=profile.academic_year,
            retake_semesters=profile.retake_semesters or [],
            university_name=university_name,
            filiere_name=filiere_name,
            cursus_name=cursus_name,
            updated_at=profile.updated_at,
        )

    def update_academic_profile(
        self,
        db: Session,
        user_id: int,
        profile_data: AcademicProfileUpdate,
    ) -> AcademicProfileResponse:
        """
        Update academic profile fields, validating IDs against Super Admin Platform.

        Raises:
            HTTPException 400 if any provided ID fails validation.
            HTTPException 404 if student profile doesn't exist.

        Requirements: 1.4, 1.5, 1.6, 1.7
        """
        profile = (
            db.query(StudentProfile)
            .filter(StudentProfile.user_id == user_id)
            .first()
        )
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found. Create a profile first.",
            )

        update_dict = profile_data.model_dump(exclude_none=True)

        # Validate university_id if provided
        if "university_id" in update_dict:
            self._validate_university_id(db, update_dict["university_id"])

        # Validate filiere_id if provided
        if "filiere_id" in update_dict:
            uni_id = update_dict.get("university_id", profile.university_id)
            self._validate_filiere_id(db, update_dict["filiere_id"], uni_id)

        # Validate cursus_id if provided
        if "cursus_id" in update_dict:
            filiere_id = update_dict.get("filiere_id", profile.filiere_id)
            self._validate_cursus_id(db, update_dict["cursus_id"], filiere_id)

        # Apply updates
        for field, value in update_dict.items():
            setattr(profile, field, value)

        db.commit()
        db.refresh(profile)

        logger.info(
            "[AcademicProfileService] Updated academic profile for user_id=%d: %s",
            user_id,
            list(update_dict.keys()),
        )
        return self.get_academic_profile(db, user_id)

    # ------------------------------------------------------------------
    # Private validation helpers
    # ------------------------------------------------------------------

    def _validate_university_id(self, db: Session, university_id: int) -> None:
        universities = client.fetch_universities(db)
        valid_ids = {u["id"] for u in universities}
        if university_id not in valid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid university_id={university_id}. Not found in Super Admin Platform.",
            )

    def _validate_filiere_id(
        self, db: Session, filiere_id: int, university_id: Optional[int]
    ) -> None:
        if university_id is None:
            return  # Cannot validate without university context
        filieres = client.fetch_filieres(db, university_id)
        valid_ids = {f["id"] for f in filieres}
        if filiere_id not in valid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid filiere_id={filiere_id} for university_id={university_id}. "
                    "Not found in Super Admin Platform."
                ),
            )

    def _validate_cursus_id(
        self, db: Session, cursus_id: int, filiere_id: Optional[int]
    ) -> None:
        if filiere_id is None:
            return  # Cannot validate without filière context
        cursus_list = client.fetch_cursus(db, filiere_id)
        valid_ids = {c["id"] for c in cursus_list}
        if cursus_id not in valid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid cursus_id={cursus_id} for filiere_id={filiere_id}. "
                    "Not found in Super Admin Platform."
                ),
            )

    # ------------------------------------------------------------------
    # Private name resolution helpers
    # ------------------------------------------------------------------

    def _resolve_university_name(
        self, db: Session, university_id: Optional[int]
    ) -> Optional[str]:
        if university_id is None:
            return None
        universities = client.fetch_universities(db)
        for u in universities:
            if u["id"] == university_id:
                return u["name"]
        return None

    def _resolve_filiere_name(
        self, db: Session, filiere_id: Optional[int]
    ) -> Optional[str]:
        if filiere_id is None:
            return None
        # We need a university_id to query filieres — use a broad search
        universities = client.fetch_universities(db)
        for u in universities:
            filieres = client.fetch_filieres(db, u["id"])
            for f in filieres:
                if f["id"] == filiere_id:
                    return f["name"]
        return None

    def _resolve_cursus_name(
        self, db: Session, cursus_id: Optional[int]
    ) -> Optional[str]:
        if cursus_id is None:
            return None
        structure = client.fetch_semester_structure(db, cursus_id)
        if structure:
            return structure.get("cursus_name")
        return None


# Module-level singleton
academic_profile_service = AcademicProfileService()
