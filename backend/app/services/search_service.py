"""Search service with AI-powered natural language search."""

import json
from typing import Dict

import structlog
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.event_repository import EventRepository

logger = structlog.get_logger()


class AISearchService:
    """AI-powered search that interprets natural language queries."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def ai_search(self, query: str, db: AsyncSession) -> Dict:
        """
        Parse natural language query using AI and execute structured search.
        
        Examples:
          - "Find AI hackathons" -> {event_type: hackathon, domains: [AI/ML]}
          - "Show Google competitions" -> {platform: google, event_type: competition}
          - "Remote internships ending this week" -> {event_type: internship, is_remote: true, deadline_soon: true}
        """
        # Step 1: Parse intent with AI
        parse_result = await self._parse_query(query)

        # Step 2: Execute based on parsed intent
        repo = EventRepository(db)

        search_str = parse_result.get("search_keywords", query)
        events, total = await repo.keyword_search(search_str, page=1, page_size=20)

        return {
            "events": events,
            "total": total,
            "explanation": parse_result.get("explanation", ""),
            "parsed_query": parse_result,
        }

    async def _parse_query(self, query: str) -> Dict:
        """Use GPT to parse natural language query into structured filters."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": f"""Parse this search query for a developer events platform.
Return JSON with:
{{
  "search_keywords": "simplified keyword string for text search",
  "event_type": "hackathon|contest|internship|workshop|competition|null",
  "platform": "platform name or null",
  "is_remote": "true/false/null",
  "domains": ["AI/ML", "Web Dev", etc] or [],
  "explanation": "Brief explanation of what you're searching for"
}}

Query: "{query}"
""",
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=200,
                temperature=0,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.warning("Query parsing failed", error=str(e))
            return {"search_keywords": query, "explanation": ""}
