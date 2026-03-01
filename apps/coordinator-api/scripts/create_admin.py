import asyncio

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.refresh_token import RefreshToken  # 🔥 IMPORTANT
from app.core.security import hash_password


async def create_admin():
    async with AsyncSessionLocal() as session:
        admin = User(
            email="admin@ex.com",
            password_hash=hash_password("Admin@123"),
            role="admin"
        )

        session.add(admin)
        await session.commit()

        print("Admin created successfully")


if __name__ == "__main__":
    asyncio.run(create_admin())