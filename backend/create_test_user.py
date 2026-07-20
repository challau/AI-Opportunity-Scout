#!/usr/bin/env python3
"""
Create a test user account in the production database.
Run this once after deployment:
  python create_test_user.py
"""

import asyncio
import sys
import os

# Ensure the backend app module and virtualenv packages are on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/Users/challaudaykumar/Desktop/AI-Opportunity-Scout/backend/venv/lib/python3.11/site-packages")



async def main():
    from app.core.config import settings
    from app.database.session import AsyncSessionLocal
    from app.models.user import User
    from app.models.profile import UserProfile
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

    print(f"Connecting to database: {settings.DATABASE_URL_SYNC[:50]}...")

    async with AsyncSessionLocal() as db:
        repo = UserRepository(db)

        for udata in users_to_create:
            existing = await repo.get_by_email(udata["email"])
            if existing:
                print(f"✅ User already exists: {udata['email']}")
                continue

            # Create user
            user = User(
                email=udata["email"],
                username=udata["username"],
                full_name=udata["full_name"],
                hashed_password=hash_password(udata["password"]),
                is_active=True,
                is_verified=True,
            )
            user = await repo.create(user)

            # Create profile
            profile = UserProfile(
                user_id=user.id,
                email_notifications=True,
                notification_enabled=True,
                notification_frequency="hourly",
                selected_sources=udata["selected_sources"],
            )
            db.add(profile)
            await db.commit()

            print(f"✅ User {udata['email']} created successfully!")
            print(f"   Username: {udata['username']}")
            print(f"   Preferences: {udata['selected_sources']}")


if __name__ == "__main__":
    asyncio.run(main())

