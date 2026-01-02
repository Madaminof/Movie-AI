from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_, func
from sqlalchemy.dialects.postgresql import insert
from .models import User, Movie, MovieView


# --- FOYDALANUVCHI BILAN ISHLASH ---
async def get_or_create_user(session: AsyncSession, user_id: int, full_name: str):
    """
    PostgreSQL 'ON CONFLICT' yordamida eng tezkor va xavfsiz user yaratish.
    Bu usul Race Condition (bir vaqtda bir xil user kelishi) oldini oladi.
    """
    stmt = (
        insert(User)
        .values(user_id=user_id, full_name=full_name)
        .on_conflict_do_update(
            index_elements=['user_id'],
            set_={'full_name': full_name, 'is_active': True}
        )
        .returning(User)
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.scalar_one()


# --- KINO BILAN ISHLASH ---
async def add_movie_to_db(session: AsyncSession, code: int, title: str, file_id: str, description: str = None):
    """Kino qo'shish yoki mavjud bo'lsa ma'lumotlarini yangilash"""
    stmt = (
        insert(Movie)
        .values(code=code, title=title, file_id=file_id, description=description)
        .on_conflict_do_update(
            index_elements=['code'],
            set_={'title': title, 'file_id': file_id, 'description': description}
        )
        .returning(Movie)
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.scalar_one()


async def get_movie_by_code(session: AsyncSession, code: int, user_id: int):
    """
    Kinoni kod bo'yicha topish va UNIKAL ko'rishlarni hisobga olish.
    """
    result = await session.execute(select(Movie).where(Movie.code == code))
    movie = result.scalar_one_or_none()

    if movie:
        # Unikal ko'rishni tekshirish va qo'shish
        view_stmt = (
            insert(MovieView)
            .values(user_id=user_id, movie_id=movie.id)
            .on_conflict_do_nothing()  # Agar bu user bu kinoni ko'rgan bo'lsa, hech narsa qilma
        )
        view_result = await session.execute(view_stmt)

        # Agar yangi unikal ko'rish qo'shilgan bo'lsa, umumiy scorni oshiramiz
        if view_result.rowcount > 0:
            movie.views += 1
            await session.commit()

    return movie


async def search_movies_smart(session: AsyncSession, query: str, limit: int = 10):
    """
    Aqlli qidiruv: Nomida yoki tavsifida qisman mos kelish (Case-insensitive)
    """
    stmt = (
        select(Movie)
        .where(
            or_(
                Movie.title.ilike(f"%{query}%"),
                Movie.description.ilike(f"%{query}%")
            )
        )
        .limit(limit)
        .order_by(Movie.views.desc())  # Ommaboplarini birinchi ko'rsatish
    )
    result = await session.execute(stmt)
    return result.scalars().all()


# --- ADMIN STATISTIKASI ---
async def get_stats(session: AsyncSession):
    """Bot statistikasi uchun optimal so'rov"""
    user_count = await session.execute(select(func.count(User.id)))
    movie_count = await session.execute(select(func.count(Movie.id)))
    return {
        "users": user_count.scalar(),
        "movies": movie_count.scalar()
    }