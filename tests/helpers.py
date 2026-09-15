from uuid import uuid4

from auth.orm import User


async def create_user(db, username="u1", email="u1@test.com"):
    user = User(
        id=uuid4(),
        username=username,
        email=email,
        hashed_password="x",
        is_verified=True,
    )

    async with db() as session:
        session.add(user)
        await session.commit()

    return user
