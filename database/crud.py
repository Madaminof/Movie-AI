from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import User, Movie


async def get_or_create_user(session: AsyncSession, user_id: int, full_name: str):
    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(user_id=user_id, full_name=full_name)
        session.add(user)
        await session.commit()
    return user

# --- KINO BILAN ISHLASH ---
async def add_movie_to_db(session: AsyncSession, code: int, title: str, file_id: str, description: str = None):
    new_movie = Movie(
        code=code,
        title=title,
        file_id=file_id,
        description=description
    )
    session.add(new_movie)
    await session.commit()
    return new_movie


async def get_movie_by_code(session: AsyncSession, code: int):
    result = await session.execute(select(Movie).where(Movie.code == code))
    movie = result.scalar_one_or_none()
    if movie:
        movie.views += 1  # Ko'rishlar sonini oshirish
        await session.commit()
    return movie