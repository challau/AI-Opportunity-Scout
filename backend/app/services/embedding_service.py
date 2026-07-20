"""Embedding service using OpenAI text-embedding-3-small."""

from typing import List

import structlog
from openai import AsyncOpenAI

from app.core.config import settings

logger = structlog.get_logger()


class EmbeddingService:
    """Generates and manages text embeddings using OpenAI."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_EMBEDDING_MODEL
        self.dimensions = 1536

    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for a single text."""
        text = text.replace("\n", " ").strip()[:8000]  # Token limit
        if not text:
            return [0.0] * self.dimensions

        try:
            response = await self.client.embeddings.create(
                input=text,
                model=self.model,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error("Embedding failed", error=str(e))
            return [0.0] * self.dimensions

    async def get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts in one API call."""
        cleaned = [t.replace("\n", " ").strip()[:8000] for t in texts]
        if not any(cleaned):
            return [[0.0] * self.dimensions] * len(texts)

        try:
            response = await self.client.embeddings.create(
                input=cleaned,
                model=self.model,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error("Batch embedding failed", error=str(e))
            return [[0.0] * self.dimensions] * len(texts)

    def event_to_text(self, event_data: dict) -> str:
        """Convert event data to a searchable text representation."""
        parts = [
            event_data.get("title", ""),
            event_data.get("description", "")[:500],
            event_data.get("event_type", ""),
            event_data.get("platform", ""),
            " ".join(event_data.get("tags", [])),
            " ".join(event_data.get("domains", [])),
            event_data.get("eligibility", ""),
        ]
        return " ".join(p for p in parts if p)
