"""
Pydantic schemas for ECTS progression tracking.

All float fields carry 2 decimal precision per requirement 3.8.
"""
from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List
from datetime import datetime
import math


def _round2(v: Optional[float]) -> Optional[float]:
    """Round a float to 2 decimal places, or return None."""
    if v is None:
        return None
    return round(v, 2)


class ECTSProgressionResponse(BaseModel):
    """ECTS progression snapshot for a student"""
    user_id: int
    ects_obtained: float = Field(..., description="Total ECTS credits earned from validated courses")
    ects_required: float = Field(..., description="Total ECTS required for graduation")
    ects_remaining: float = Field(..., description="ECTS still to be earned")
    progression_percentage: float = Field(
        ...,
        description="(ects_obtained / ects_required) * 100, 2 decimal places"
    )
    last_calculated_at: Optional[datetime] = None

    @field_serializer("ects_obtained")
    def serialize_ects_obtained(self, v: float) -> float:
        return round(v, 2)

    @field_serializer("ects_required")
    def serialize_ects_required(self, v: float) -> float:
        return round(v, 2)

    @field_serializer("ects_remaining")
    def serialize_ects_remaining(self, v: float) -> float:
        return round(v, 2)

    @field_serializer("progression_percentage")
    def serialize_progression_percentage(self, v: float) -> float:
        return round(v, 2)

    model_config = {"from_attributes": True}


class ECTSSemesterBreakdown(BaseModel):
    """ECTS breakdown for a specific semester"""
    semester: int = Field(..., description="Semester number")
    ects_obtained: float = Field(
        ...,
        description="ECTS earned in this semester (validated courses)"
    )
    ects_required: float = Field(
        ...,
        description="Total ECTS available in this semester"
    )
    ects_remaining: float = Field(
        ...,
        description="ECTS still to earn in this semester"
    )
    progression_percentage: float = Field(
        ...,
        description="Percentage of semester ECTS earned"
    )

    @field_serializer("ects_obtained", "ects_required", "ects_remaining", "progression_percentage")
    def serialize_float(self, v: float) -> float:
        return round(v, 2)

    model_config = {"from_attributes": True}


class ECTSProgressWithBreakdown(ECTSProgressionResponse):
    """Extended ECTS response with per-semester breakdown"""
    semester_breakdown: List[ECTSSemesterBreakdown] = []
