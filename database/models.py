from sqlalchemy import BigInteger, String, Integer, Text, DateTime, func, ForeignKey, UniqueConstraint, Column, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs


# Hamma modellar meros oladigan asosiy klass
class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    joined_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)

    # lazy="selectin" asinxron ishlashda xatoliklarni oldini oladi
    history: Mapped[list["MovieView"]] = relationship(
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan"
    )


class Movie(Base):
    __tablename__ = 'movies'
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    file_id: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    views: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    viewers: Mapped[list["MovieView"]] = relationship(
        back_populates="movie",
        lazy="selectin",
        cascade="all, delete-orphan"
    )


class MovieView(Base):
    """Foydalanuvchilarning unikal ko'rishlarini hisobga olish jadvali"""
    __tablename__ = 'movie_views'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.user_id', ondelete="CASCADE"))
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey('movies.id', ondelete="CASCADE"))
    viewed_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    # Bog'lanishlar
    user: Mapped["User"] = relationship(back_populates="history", lazy="selectin")
    movie: Mapped["Movie"] = relationship(back_populates="viewers", lazy="selectin")

    # Bitta foydalanuvchi bitta kinoni faqat bir marta unikal ko'rishi uchun cheklov
    __table_args__ = (
        UniqueConstraint('user_id', 'movie_id', name='_user_movie_uc'),
        {'extend_existing': True}
    )


from sqlalchemy import Column, BigInteger, String, Integer

class BroadcastLog(Base):
    __tablename__ = 'broadcast_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    broadcast_id = Column(String(50))
    user_id = Column(BigInteger)
    message_id = Column(BigInteger)

class Category(Base):
    __tablename__ = 'categories'
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


