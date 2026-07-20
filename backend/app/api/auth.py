"""Authentication API — register, login, OAuth, refresh, password reset."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.config import settings
from app.models.user import User
from app.models.profile import UserProfile
from app.repositories.user_repository import UserRepository
from app.schemas.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.services.email_service import EmailService

logger = structlog.get_logger()
router = APIRouter(prefix="/auth", tags=["Authentication"])


def _build_token_response(user_id: str) -> TokenResponse:
    access_token = create_access_token({"sub": user_id})
    refresh_token = create_refresh_token({"sub": user_id})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    repo = UserRepository(db)

    if await repo.email_exists(payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if await repo.username_exists(payload.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    user = await repo.create(user)

    # Create default profile
    profile = UserProfile(user_id=user.id)
    db.add(profile)
    await db.commit()

    logger.info("User registered", user_id=str(user.id), email=user.email)
    return _build_token_response(str(user.id))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    repo = UserRepository(db)
    user = await repo.get_by_email(payload.email)

    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    from datetime import datetime, timezone
    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    logger.info("User logged in", user_id=str(user.id))
    return _build_token_response(str(user.id))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using a valid refresh token."""
    token_data = decode_token(payload.refresh_token)
    if not token_data or token_data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = token_data.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    import uuid
    try:
        uuid_user_id = uuid.UUID(str(user_id))
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    repo = UserRepository(db)
    user = await repo.get_by_id(uuid_user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")

    return _build_token_response(str(user.id))


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
):
    """Send password reset email."""
    repo = UserRepository(db)
    user = await repo.get_by_email(payload.email)

    # Always return 200 to prevent email enumeration
    if user:
        token = create_password_reset_token(user.email)
        reset_url = f"{settings.APP_URL}/reset-password?token={token}"
        email_service = EmailService()
        await email_service.send_password_reset(user.email, user.full_name, reset_url)
        logger.info("Password reset email sent", email=user.email)

    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
):
    """Reset password using token."""
    token_data = decode_token(payload.token)
    if not token_data or token_data.get("type") != "password_reset":
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    repo = UserRepository(db)
    user = await repo.get_by_email(token_data["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(payload.new_password)
    await db.commit()

    return {"message": "Password reset successful"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return current_user


# ─── Google OAuth ──────────────────────────────────────────────────────────────

@router.get("/google")
async def google_oauth_start():
    """Redirect to Google OAuth consent screen."""
    from authlib.integrations.httpx_client import AsyncOAuth2Client  # type: ignore
    client = AsyncOAuth2Client(
        client_id=settings.GOOGLE_CLIENT_ID,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
        scope="openid email profile",
    )
    url, state = client.create_authorization_url(
        "https://accounts.google.com/o/oauth2/v2/auth"
    )
    return {"auth_url": url, "state": state}


@router.get("/google/callback")
async def google_oauth_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Handle Google OAuth callback."""
    import httpx
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        token_data = token_resp.json()
        user_resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        google_user = user_resp.json()

    repo = UserRepository(db)
    user = await repo.get_by_google_id(google_user["sub"])

    if not user:
        # Check if email already exists
        user = await repo.get_by_email(google_user["email"])
        if user:
            user.google_id = google_user["sub"]
            user.avatar_url = google_user.get("picture")
        else:
            import re
            base_username = re.sub(r"[^a-z0-9_]", "", google_user.get("name", "user").lower())[:20]
            username = base_username
            suffix = 1
            while await repo.username_exists(username):
                username = f"{base_username}{suffix}"
                suffix += 1

            user = User(
                email=google_user["email"],
                username=username,
                full_name=google_user.get("name", ""),
                google_id=google_user["sub"],
                avatar_url=google_user.get("picture"),
                is_verified=True,
            )
            user = await repo.create(user)
            profile = UserProfile(user_id=user.id)
            db.add(profile)

        await db.commit()

    return _build_token_response(str(user.id))


# ─── GitHub OAuth ──────────────────────────────────────────────────────────────

@router.get("/github")
async def github_oauth_start():
    """Redirect to GitHub OAuth consent screen."""
    from authlib.integrations.httpx_client import AsyncOAuth2Client  # type: ignore
    client = AsyncOAuth2Client(
        client_id=settings.GITHUB_CLIENT_ID,
        redirect_uri=settings.GITHUB_REDIRECT_URI,
        scope="user:email read:user",
    )
    url, state = client.create_authorization_url(
        "https://github.com/login/oauth/authorize"
    )
    return {"auth_url": url, "state": state}


@router.get("/github/callback")
async def github_oauth_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Handle GitHub OAuth callback."""
    import httpx
    async with httpx.AsyncClient() as client:
        # Exchange code for token
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
            },
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to retrieve access token from GitHub")

        # Fetch user profile
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        github_user = user_resp.json()

        # Fetch user emails
        email_resp = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        emails = email_resp.json()
        primary_email = None
        if isinstance(emails, list):
            for e in emails:
                if e.get("primary"):
                    primary_email = e.get("email")
                    break
            if not primary_email and emails:
                primary_email = emails[0].get("email")

        email = primary_email or github_user.get("email") or f"{github_user.get('login')}@users.noreply.github.com"

    repo = UserRepository(db)
    user = await repo.get_by_github_id(str(github_user["id"]))

    if not user:
        # Check if email already exists
        user = await repo.get_by_email(email)
        if user:
            user.github_id = str(github_user["id"])
            if not user.avatar_url:
                user.avatar_url = github_user.get("avatar_url")
        else:
            import re
            base_username = re.sub(r"[^a-z0-9_]", "", github_user.get("login", "user").lower())[:20]
            username = base_username
            suffix = 1
            while await repo.username_exists(username):
                username = f"{base_username}{suffix}"
                suffix += 1

            user = User(
                email=email,
                username=username,
                full_name=github_user.get("name") or github_user.get("login") or "GitHub User",
                github_id=str(github_user["id"]),
                avatar_url=github_user.get("avatar_url"),
                is_verified=True,
            )
            user = await repo.create(user)
            profile = UserProfile(user_id=user.id)
            db.add(profile)

        await db.commit()

    return _build_token_response(str(user.id))
