"""Seed an initial user for local/staging use (RF-65).

Idempotent: does nothing if a user with the given email already exists.

Usage (run from backend/, same as pytest):
    python -m scripts.seed_user --email admin@example.com --full-name "Admin User" --password changeme123
"""

import argparse
import asyncio

from sqlalchemy import select

from app.core.database import async_session_factory
from app.modules.auth.models import User
from app.modules.auth.schemas import UserRegister
from app.modules.auth.service import register_user


async def seed_user(email: str, full_name: str, password: str) -> None:
    async with async_session_factory() as db:
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none() is not None:
            print(f"User {email} already exists, skipping.")
            return
        user = await register_user(
            db, UserRegister(email=email, full_name=full_name, password=password)
        )
        print(f"Seeded user {user.email} ({user.id})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--full-name", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    asyncio.run(seed_user(args.email, args.full_name, args.password))


if __name__ == "__main__":
    main()
