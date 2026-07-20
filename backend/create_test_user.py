#!/usr/bin/env python3
"""
Create a test user account in the production database.
Run this once after deployment:
  python create_test_user.py
"""

import asyncio
import sys
import os

# Ensure the backend app module is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def main():
    from app.core.config import settings
    from app.database.session import AsyncSessionLocal
    from app.models.user import User
    from app.models.profile import UserProfile
    from app.core.security import hash_password
    from app.repositories.user_repository import UserRepository

    TEST_EMAIL = "challaudaykumar1@gmail.com"
    TEST_USERNAME = "udaykumar"
    TEST_FULL_NAME = "Uday Kumar"
    TEST_PASSWORD = "Scout@2026!"

    print(f"Connecting to database: {settings.DATABASE_URL_SYNC[:50]}...")

    async with AsyncSessionLocal() as db:
        repo = UserRepository(db)

        # Check if user already exists
        existing = await repo.get_by_email(TEST_EMAIL)
        if existing:
            print(f"✅ Test user already exists: {TEST_EMAIL}")
            print(f"   Username: {existing.username}")
            print(f"   Active: {existing.is_active}")
            return

        # Create user
        user = User(
            email=TEST_EMAIL,
            username=TEST_USERNAME,
            full_name=TEST_FULL_NAME,
            hashed_password=hash_password(TEST_PASSWORD),
            is_active=True,
            is_verified=True,
        )
        user = await repo.create(user)

        # Create profile with all sources enabled + hourly notifications
        profile = UserProfile(
            user_id=user.id,
            email_notifications=True,
            notification_frequency="hourly",
            selected_sources=[
                "unstop", "devfolio", "hackerearth", "hack2skill", "devpost",
                "codeforces", "codechef", "leetcode", "atcoder",
            ],
        )
        db.add(profile)
        await db.commit()

        print(f"✅ Test user created successfully!")
        print(f"   Email:    {TEST_EMAIL}")
        print(f"   Username: {TEST_USERNAME}")
        print(f"   Password: {TEST_PASSWORD}")
        print(f"   User ID:  {user.id}")


if __name__ == "__main__":
    asyncio.run(main())
