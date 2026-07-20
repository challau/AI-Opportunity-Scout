"""Resume parsing and event matching service."""

import json
from typing import Dict, List, Tuple

import structlog
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import RESUME_MATCH_PROMPT
from app.core.config import settings
from app.schemas.schemas import ResumeMatchResult
from app.services.embedding_service import EmbeddingService

logger = structlog.get_logger()


class ResumeService:
    """Handles resume parsing, skill extraction, and event matching."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.embedding_service = EmbeddingService()

    async def extract_text_and_skills(self, file_path: str) -> Tuple[str, Dict]:
        """Extract text from PDF or DOCX and parse skills using AI."""
        # Extract raw text
        if file_path.lower().endswith(".docx"):
            text = self._extract_docx_text(file_path)
        else:
            text = self._extract_pdf_text(file_path)

        # Use AI to extract structured skills
        skills = await self._extract_skills_with_ai(text)

        return text, skills

    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX using standard zipfile and xml parser."""
        try:
            import zipfile
            import xml.etree.ElementTree as ET
            texts = []
            with zipfile.ZipFile(file_path) as docx:
                xml_content = docx.read('word/document.xml')
                root = ET.fromstring(xml_content)
                for paragraph in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                    para_texts = [node.text for node in paragraph.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
                    if para_texts:
                        texts.append("".join(para_texts))
            return "\n".join(texts)
        except Exception as e:
            logger.error("DOCX extraction failed", error=str(e))
            return ""

    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF using pdfplumber."""
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n".join(text_parts)
        except Exception as e:
            logger.warning("pdfplumber failed, trying PyPDF2", error=str(e))
            try:
                import PyPDF2
                text_parts = []
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for pypdf_page in reader.pages:
                        text_parts.append(pypdf_page.extract_text())
                return "\n".join(text_parts)
            except Exception as e2:
                logger.error("PDF extraction failed", error=str(e2))
                return ""

    async def _extract_skills_with_ai(self, text: str) -> Dict:
        """Use GPT to extract structured skills from resume text."""
        if not text.strip():
            return {}

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": f"""Extract skills from this resume. Return JSON:
{{
  "programming_languages": ["Python", "JavaScript", ...],
  "frameworks": ["React", "FastAPI", ...],
  "tools": ["Docker", "Git", ...],
  "domains": ["Machine Learning", "Web Dev", ...],
  "education": "Bachelor's in CS",
  "experience_years": 2,
  "summary": "Brief 2-sentence profile"
}}

Resume:
{text[:3000]}""",
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=500,
                temperature=0,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error("Skill extraction failed", error=str(e))
            return {}

    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for resume text."""
        return await self.embedding_service.get_embedding(text[:5000])

    async def match_with_events(
        self,
        resume,
        db: AsyncSession,
        top_k: int = 10,
    ) -> List[ResumeMatchResult]:
        """Match resume against events using vector similarity + AI explanation."""
        from app.repositories.event_repository import EventRepository

        if not resume.embedding:
            return []

        # Semantic search
        repo = EventRepository(db)
        events = await repo.semantic_search(resume.embedding, limit=top_k * 2)

        results = []
        for event in events[:top_k]:
            # Get AI explanation
            skills_str = json.dumps(resume.skills, indent=2) if resume.skills else "N/A"
            match_data = await self._get_match_explanation(
                skills=skills_str,
                resume_summary=resume.skills.get("summary", "") if resume.skills else "",
                event=event,
            )

            results.append(
                ResumeMatchResult(
                    event_id=event.id,
                    event_title=event.title,
                    match_percentage=match_data.get("match_percentage", 50),
                    matching_skills=match_data.get("matching_skills", []),
                    explanation=match_data.get("explanation", ""),
                )
            )

        # Sort by match percentage
        results.sort(key=lambda x: x.match_percentage, reverse=True)
        return results

    async def _get_match_explanation(
        self, skills: str, resume_summary: str, event
    ) -> Dict:
        """Get AI explanation for resume-event match."""
        try:
            prompt = RESUME_MATCH_PROMPT.format(
                skills=skills[:500],
                resume_summary=resume_summary[:300],
                event_title=event.title,
                event_type=event.event_type,
                eligibility=event.eligibility or "Open to all",
                tags=", ".join(event.tags or []),
            )
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=300,
                temperature=0,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.warning("Match explanation failed", error=str(e))
            return {"match_percentage": 50, "matching_skills": [], "explanation": ""}
