"""
Authentication schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserRegister(BaseModel):
    """Schema for user registration"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=100, description="User password")
    name: str = Field(..., min_length=1, max_length=100, description="User full name")


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class Token(BaseModel):
    """Schema for token response"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenRefresh(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str = Field(..., description="JWT refresh token")


class UserResponse(BaseModel):
    """Schema for user response"""
    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User name")
    is_active: bool = Field(..., description="Account active status")
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Schema for simple message response"""
    message: str = Field(..., description="Response message")


class UserUpdate(BaseModel):
    """Schema for updating basic user information"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="User full name")
    email: Optional[EmailStr] = Field(None, description="User email address")


class PasswordChange(BaseModel):
    """Schema for password change request"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request"""
    email: EmailStr = Field(..., description="User email address")


class ResetPasswordRequest(BaseModel):
    """Schema for password reset using token"""
    token: str = Field(..., min_length=10, description="Reset token received by email")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")


