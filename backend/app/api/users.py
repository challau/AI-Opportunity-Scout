"""Users API — profile management."""

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.config import settings
from app.models.profile import UserProfile
from app.models.user import User
from app.schemas.schemas import ProfileResponse, ProfileUpdate, UserResponse

logger = structlog.get_logger()
router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile."""
    return current_user


@router.get("/me/profile", response_model=ProfileResponse)
async def get_detailed_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed user profile with preferences."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.patch("/me/profile", response_model=ProfileResponse)
async def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user profile and preferences."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)

    logger.info("Profile updated", user_id=str(current_user.id))
    return profile


from fastapi.responses import HTMLResponse

@router.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe(email: str, db: AsyncSession = Depends(get_db)):
    """Unsubscribe a user from email notifications."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return HTMLResponse(
            content="<h3>User not found</h3>",
            status_code=404
        )
    profile_result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = profile_result.scalar_one_or_none()
    if profile:
        profile.notification_enabled = False
        profile.email_notifications = False
        await db.commit()
        
        frontend_url = settings.APP_URL or "https://ai-opportunity-scout-pi.vercel.app"
        
        return HTMLResponse(
            content=f"""
            <html>
            <head>
                <title>Unsubscribed</title>
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
                    <h1>Unsubscribed Successfully</h1>
                    <p>You have been unsubscribed from opportunity notifications.</p>
                    <p>You can turn them back on anytime in your profile settings.</p>
                    <a href="{frontend_url}/profile" class="btn">Go to Profile</a>
                </div>
            </body>
            </html>
            """
        )
    return HTMLResponse(content="<h3>Error updating profile</h3>", status_code=500)

