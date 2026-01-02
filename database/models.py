from sqlalchemy import BigInteger, String, Integer, Text, DateTime, func, ForeignKey, UniqueConstraint, Column, Boolean, \
    Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    username: Mapped[str] = mapped_column(String(255), nullable=True)  # Foydalanuvchi nomini saqlash foydali
    joined_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)  # Adminlarni ajratish uchun

    history: Mapped[list["MovieView"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    # Kategoriya ostidagi kinolar
    movies: Mapped[list["Movie"]] = relationship(back_populates="category")


class Movie(Base):
    __tablename__ = 'movies'

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    file_id: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id', ondelete="SET NULL"), nullable=True)

    views: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(default=0.0)  # Aqlli bot uchun reyting tizimi
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    # Bog'lanishlar
    category: Mapped["Category"] = relationship(back_populates="movies")
    viewers: Mapped[list["MovieView"]] = relationship(back_populates="movie", cascade="all, delete-orphan")

    # Qidiruvni tezlashtirish uchun title ustiga Index qo'shamiz
    __table_args__ = (
        Index('ix_movie_title', 'title'),
    )


class MovieView(Base):
    __tablename__ = 'movie_views'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.user_id', ondelete="CASCADE"))
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey('movies.id', ondelete="CASCADE"))
    viewed_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="history")
    movie: Mapped["Movie"] = relationship(back_populates="viewers")

    __table_args__ = (
        UniqueConstraint('user_id', 'movie_id', name='_user_movie_uc'),
    )


class BroadcastLog(Base):
    __tablename__ = 'broadcast_logs'
    id: Mapped[int] = mapped_column(primary_key=True)
    broadcast_id: Mapped[str] = mapped_column(String(50), index=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(20), default="sent")  # "sent", "failed", "blocked"