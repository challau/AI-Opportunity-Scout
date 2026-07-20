import asyncio
import sqlalchemy as sa
from app.database.session import engine, Base
import app.models  # noqa: F401

async def init_db():
    async with engine.begin() as conn:
        # Enable pgvector extension in Neon PostgreSQL
        await conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())
