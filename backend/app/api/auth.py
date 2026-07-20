"""Authentication API — register, login, OAuth, refresh, password reset."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    create_email_verification_token,
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


from fastapi.responses import HTMLResponse

@router.post("/send-verification-email")
async def send_verification_email(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send an email verification link to the logged-in user."""
    token = create_email_verification_token(current_user.email)
    verify_url = f"{settings.API_URL}/api/auth/verify-email?token={token}"
    
    email_service = EmailService()
    subject = "Verify your email address - AI Opportunity Scout"
    
    html = f"""
    <!DOCTYPE html>
    <html><body style="margin:0;padding:0;background:#0f0f1a;font-family:'Segoe UI',Arial,sans-serif;">
    <div style="max-width:600px;margin:0 auto;padding:20px;">
      <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:16px 16px 0 0;padding:32px 28px;text-align:center;">
        <h1 style="color:#fff;font-size:22px;margin:0;">🚀 AI Opportunity Scout</h1>
      </div>
      <div style="background:#1a1a2e;padding:24px;border-radius:0 0 16px 16px;border:1px solid #3a3a5c;">
        <p style="color:#e2e8f0;font-size:16px;">Hello {current_user.full_name},</p>
        <p style="color:#94a3b8;font-size:15px;line-height:1.5;">Please verify your email address to activate your account and start receiving hourly digests of new hackathons and coding contests.</p>
        <div style="text-align:center;margin:30px 0;">
          <a href="{verify_url}" style="display:inline-block;padding:12px 28px;background:#6366f1;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px;">Verify Email</a>
        </div>
        <p style="color:#64748b;font-size:13px;word-break:break-all;">Or copy and paste this link in your browser:<br/>{verify_url}</p>
      </div>
    </div>
    </body></html>
    """
    text = f"Hello {current_user.full_name},\n\nPlease verify your email address by clicking the following link:\n{verify_url}"
    
    ok = await email_service.send_email(
        to_email=current_user.email,
        subject=subject,
        html_content=html,
        text_content=text
    )
    if ok:
        return {"status": "success", "message": "Verification email sent"}
    raise HTTPException(status_code=500, detail="Failed to send verification email")


@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """Verify email verification token and update user's is_verified status."""
    payload = decode_token(token)
    if not payload or payload.get("type") != "email_verification":
        return HTMLResponse(
            content="<h3>Invalid or expired token</h3>",
            status_code=400
        )
    
    email = payload.get("sub")
    repo = UserRepository(db)
    user = await repo.get_by_email(email)
    if not user:
        return HTMLResponse(
            content="<h3>User not found</h3>",
            status_code=404
        )
        
    user.is_verified = True
    await db.commit()
    
    frontend_url = settings.APP_URL or "https://ai-opportunity-scout-pi.vercel.app"
    
    return HTMLResponse(
        content=f"""
        <html>
        <head>
            <title>Email Verified</title>
            <style>
                body {{ font-family: sans-serif; background-color: #0f0f1a; color: #e2e8f0; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                .card {{ background-color: #1a1a2e; border: 1px solid #3a3a5c; padding: 40px; border-radius: 16px; text-align: center; max-width: 400px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }}
                h1 {{ color: #a78bfa; margin-bottom: 20px; }}
                p {{ color: #94a3b8; font-size: 16px; line-height: 1.5; }}
                .btn {{ display: inline-block; margin-top: 25px; padding: 12px 24px; background: linear-gradient(135deg,#6366f1,#8b5cf6); color: white; text-decoration: none; border-radius: 8px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Email Verified successfully!</h1>
                <p>Thank you for verifying your email address.</p>
                <p>Your account is now fully active, and you're ready to receive customized opportunity notifications.</p>
                <a href="{frontend_url}/profile" class="btn">Go to Profile</a>
            </div>
        </body>
        </html>
        """
    )


@router.get("/setup-test-users")
async def setup_test_users(db: AsyncSession = Depends(get_db)):
    """Seed test users into the database (challaudaykumar1@gmail.com, user1@test.com, user2@test.com)"""
    from app.core.security import hash_password
    from app.repositories.user_repository import UserRepository
    
    users_to_create = [
        {
            "email": "challaudaykumar1@gmail.com",
            "username": "udaykumar",
            "full_name": "Uday Kumar",
            "password": "Scout@2026!",
            "selected_sources": [
                "unstop", "devfolio", "hackerearth", "hack2skill", "devpost",
                "codeforces", "codechef", "leetcode", "atcoder",
            ]
        },
        {
            "email": "user1@test.com",
            "username": "user1",
            "full_name": "Competitive Programmer User 1",
            "password": "Scout@2026!",
            "selected_sources": ["codeforces", "leetcode"]
        },
        {
            "email": "user2@test.com",
            "username": "user2",
            "full_name": "Hackathon Developer User 2",
            "password": "Scout@2026!",
            "selected_sources": ["unstop", "devfolio"]
        }
    ]
    
    created = []
    already_exists = []
    
    repo = UserRepository(db)
    for udata in users_to_create:
        existing = await repo.get_by_email(udata["email"])
        if existing:
            already_exists.append(udata["email"])
            continue
            
        user = User(
            email=udata["email"],
            username=udata["username"],
            full_name=udata["full_name"],
            hashed_password=hash_password(udata["password"]),
            is_active=True,
            is_verified=True,
        )
        user = await repo.create(user)
        
        profile = UserProfile(
            user_id=user.id,
            email_notifications=True,
            notification_enabled=True,
            notification_frequency="hourly",
            selected_sources=udata["selected_sources"],
        )
        db.add(profile)
        created.append(udata["email"])
        
    await db.commit()
    return {
        "status": "success",
        "created": created,
        "already_exists": already_exists
    }


