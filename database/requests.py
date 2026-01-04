from sqlalchemy import func
from database.models import User
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession


async def register_user(session: AsyncSession, tg_user):
    result = await session.execute(select(User).where(User.user_id == tg_user.id))
    user = result.scalar_one_or_none()

    if not user:
        new_user = User(
            user_id=tg_user.id,
            full_name=tg_user.full_name,
            username=tg_user.username
        )
        session.add(new_user)
    else:
        if user.full_name != tg_user.full_name or user.username != tg_user.username:
            user.full_name = tg_user.full_name
            user.username = tg_user.username

    await session.commit()


async def get_full_stats(session: AsyncSession):
    u_count = await session.scalar(select(func.count(User.id))) or 0
    m_count = await session.scalar(select(func.count(Movie.id))) or 0
    v_count = await session.scalar(select(func.count(MovieView.id))) or 0

    return u_count, m_count, v_count


async def get_admin_dashboard_stats(session: AsyncSession):

    total_users = await session.scalar(select(func.count(User.id))) or 0
    total_movies = await session.scalar(select(func.count(Movie.id))) or 0
    from database.models import MovieView
    total_views = await session.scalar(select(func.count(MovieView.id))) or 0

    top_movies_query = await session.execute(
        select(Movie).order_by(Movie.views.desc()).limit(10)
    )
    top_movies = top_movies_query.scalars().all()

    return total_users, total_movies, total_views, top_movies



async def add_movie_view(session: AsyncSession, user_id: int, movie_id: int):

    stmt = insert(MovieView).values(
        user_id=user_id,
        movie_id=movie_id
    ).on_conflict_do_nothing(index_elements=['user_id', 'movie_id'])

    await session.execute(stmt)

    await session.execute(
        update(Movie)
        .where(Movie.id == movie_id)
        .values(views=Movie.views + 1)
    )

    await session.commit()


from sqlalchemy import select, update
from database.models import Movie, MovieView

from sqlalchemy import select, update
from database.models import Movie, MovieView

async def increment_movie_view(session: AsyncSession, user_id: int, movie_id: int):
    """Faqat yangi ko'rish bo'lsagina hisoblagichni oshiradi"""
    # 1. Ushbu foydalanuvchi bu kinoni avval ko'rganmi?
    stmt = select(MovieView).where(
        MovieView.user_id == user_id,
        MovieView.movie_id == movie_id
    )
    result = await session.execute(stmt)
    already_exists = result.scalar_one_or_none()

    if not already_exists:
        # 2. Agar ko'rmagan bo'lsa, jadvalga yangi qator qo'shamiz
        new_view = MovieView(user_id=user_id, movie_id=movie_id)
        session.add(new_view)

        # 3. Movie jadvalidagi views ustunini +1 qilamiz
        await session.execute(
            update(Movie)
            .where(Movie.id == movie_id)
            .values(views=Movie.views + 1)
        )
        await session.commit()
        return True
    return False