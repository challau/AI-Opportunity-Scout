"""Resume upload and matching API."""

import uuid as uuid_mod
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.models.other import Resume
from app.models.user import User
from app.schemas.schemas import ResumeMatchResult, ResumeResponse
from app.services.resume_service import ResumeService

logger = structlog.get_logger()
router = APIRouter(prefix="/resume", tags=["Resume"])


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a PDF resume for matching."""
    filename = file.filename or ""
    lower_filename = filename.lower()
    if not (lower_filename.endswith(".pdf") or lower_filename.endswith(".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB",
        )

    # Save file
    upload_dir = Path(settings.UPLOAD_DIR) / "resumes" / str(current_user.id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    ext = ".docx" if lower_filename.endswith(".docx") else ".pdf"
    file_path = upload_dir / f"{uuid_mod.uuid4()}{ext}"
    file_path.write_bytes(content)

    # Process resume
    resume_service = ResumeService()
    extracted_text, skills = await resume_service.extract_text_and_skills(str(file_path))
    embedding = await resume_service.get_embedding(extracted_text)

    # Save to database
    resume = Resume(
        user_id=current_user.id,
        filename=filename,
        file_path=str(file_path),
        file_size=len(content),
        extracted_text=extracted_text,
        skills=skills,
        embedding=embedding,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    logger.info("Resume uploaded", user_id=str(current_user.id), resume_id=str(resume.id))
    return resume


@router.get("/my", response_model=list[ResumeResponse])
async def get_my_resumes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's uploaded resumes."""
    from sqlalchemy import select
    result = await db.execute(
        select(Resume).where(Resume.user_id == current_user.id, Resume.is_active == True)
    )
    return list(result.scalars().all())


@router.post("/{resume_id}/match", response_model=list[ResumeMatchResult])
async def match_resume_with_events(
    resume_id: uuid_mod.UUID,
    top_k: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Match resume against all events and return ranked matches."""
    from sqlalchemy import select
    result = await db.execute(
        select(Resume).where(
            Resume.id == resume_id,
            Resume.user_id == current_user.id,
        )
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_service = ResumeService()
    matches = await resume_service.match_with_events(resume, db, top_k=top_k)
    return matches
