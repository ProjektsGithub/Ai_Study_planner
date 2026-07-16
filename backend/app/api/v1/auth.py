"""
Authentication endpoints
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    validate_password_strength,
)
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    TokenRefresh,
    UserResponse,
    MessageResponse,
    UserUpdate,
    PasswordChange,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.models.user import User
from app.services.email_service import EmailService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    - **email**: Valid email address (RFC 5322)
    - **password**: Password meeting complexity requirements
    - **name**: User's full name (1-100 characters)
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    is_valid, error_message = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        name=user_data.name,
        created_at=datetime.now(timezone.utc),
        is_active=True,
        failed_login_attempts=0,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password.
    
    Returns JWT access and refresh tokens.
    
    - **email**: User email address
    - **password**: User password
    """
    # Get user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    
    # Check if user exists and password is correct
    if not user or not verify_password(credentials.password, user.password_hash):
        # Increment failed login attempts if user exists
        if user:
            user.failed_login_attempts += 1
            user.last_failed_login = datetime.now(timezone.utc)
            db.commit()
            
            # Check if account should be locked (5 failed attempts within 15 minutes)
            if user.failed_login_attempts >= 5:
                if user.last_failed_login and (datetime.now(timezone.utc) - user.last_failed_login) < timedelta(minutes=15):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Account temporarily locked due to multiple failed login attempts. Please try again later."
                    )
                else:
                    # Reset counter if last failed login was more than 15 minutes ago
                    user.failed_login_attempts = 1
                    db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if account is locked
    if user.failed_login_attempts >= 5:
        if user.last_failed_login and (datetime.now(timezone.utc) - user.last_failed_login) < timedelta(minutes=15):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account temporarily locked due to multiple failed login attempts. Please try again later."
            )
        else:
            # Reset counter if last failed login was more than 15 minutes ago
            user.failed_login_attempts = 0
            db.commit()
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Reset failed login attempts on successful login
    user.failed_login_attempts = 0
    db.commit()
    
    # Get user roles for token payload
    from app.models.user_role import UserRole
    from app.models.admin_role import AdminRole
    
    user_roles = db.query(UserRole).filter(
        UserRole.user_id == user.id
    ).join(AdminRole).filter(
        AdminRole.is_active == True
    ).all()
    
    # Prepare role data for JWT payload
    roles = []
    for user_role in user_roles:
        roles.append({
            "role_id": user_role.role_id,
            "role_name": user_role.role.name,
            "role_display_name": user_role.role.display_name,
            "university_id": user_role.university_id,
            "program_id": user_role.program_id
        })
    
    # Create tokens with role information (sub must be string per JWT spec)
    access_token = create_access_token(data={"sub": str(user.id)}, roles=roles)
    refresh_token = create_refresh_token(data={"sub": str(user.id)}, roles=roles)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid JWT refresh token
    """
    # Decode refresh token
    payload = decode_token(token_data.refresh_token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Convert user_id to integer
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user roles for token payload
    from app.models.user_role import UserRole
    from app.models.admin_role import AdminRole
    
    user_roles = db.query(UserRole).filter(
        UserRole.user_id == user.id
    ).join(AdminRole).filter(
        AdminRole.is_active == True
    ).all()
    
    # Prepare role data for JWT payload
    roles = []
    for user_role in user_roles:
        roles.append({
            "role_id": user_role.role_id,
            "role_name": user_role.role.name,
            "role_display_name": user_role.role.display_name,
            "university_id": user_role.university_id,
            "program_id": user_role.program_id
        })
    
    # Create new tokens with role information
    access_token = create_access_token(data={"sub": str(user.id)}, roles=roles)
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)}, roles=roles)
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user.
    
    Note: Since we're using stateless JWT tokens, actual token invalidation
    would require a token blacklist. For now, this endpoint serves as a
    placeholder and the client should discard the tokens.
    """
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Requires valid JWT access token in Authorization header.
    """
    return current_user


@router.put("/update-profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update authenticated user's profile details (name, email).
    """
    if profile_data.email is not None and profile_data.email != current_user.email:
        # Check if email is already taken
        existing_user = db.query(User).filter(User.email == profile_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = profile_data.email
        
    if profile_data.name is not None:
        current_user.name = profile_data.name
        
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change authenticated user's password.
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
        
    # Validate new password strength
    is_valid, error_message = validate_password_strength(password_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
        
    # Update password
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Demande de réinitialisation du mot de passe.

    Envoie un email avec un lien de réinitialisation valable 1 heure.
    Retourne toujours le même message pour ne pas révéler si l'email existe.
    """
    user = db.query(User).filter(User.email == request.email).first()

    # Réponse générique même si l'utilisateur n'existe pas (sécurité)
    generic_message = "Si cet email est associé à un compte, vous recevrez un lien de réinitialisation dans quelques minutes."

    if not user or not user.is_active:
        return {"message": generic_message}

    # Générer un token sécurisé
    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    # Stocker le hash en DB avec expiration 1 heure
    user.reset_password_token = token_hash
    user.reset_password_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()

    # Envoyer l'email (le token en clair est transmis dans l'URL)
    email_service = EmailService()
    email_service.send_password_reset_email(
        recipient_email=user.email,
        recipient_name=user.name,
        reset_token=raw_token,
    )

    return {"message": generic_message}


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Réinitialise le mot de passe à partir d'un token valide.

    - **token**: Token reçu par email
    - **new_password**: Nouveau mot de passe (min. 8 caractères)
    """
    # Hasher le token reçu pour le comparer au hash stocké
    token_hash = hashlib.sha256(request.token.encode()).hexdigest()

    user = db.query(User).filter(
        User.reset_password_token == token_hash
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de réinitialisation invalide ou expiré.",
        )

    # Vérifier l'expiration
    if not user.reset_password_token_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de réinitialisation invalide ou expiré.",
        )

    expires = user.reset_password_token_expires
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires:
        # Nettoyer le token expiré
        user.reset_password_token = None
        user.reset_password_token_expires = None
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de réinitialisation expiré. Veuillez refaire une demande.",
        )

    # Valider la force du nouveau mot de passe
    is_valid, error_message = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )

    # Mettre à jour le mot de passe et invalider le token
    user.password_hash = get_password_hash(request.new_password)
    user.reset_password_token = None
    user.reset_password_token_expires = None
    user.failed_login_attempts = 0
    db.commit()

    return {"message": "Mot de passe réinitialisé avec succès. Vous pouvez maintenant vous connecter."}
