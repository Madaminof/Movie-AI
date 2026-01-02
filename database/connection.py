import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool, AsyncAdaptedQueuePool
from config import config

logger = logging.getLogger(__name__)


def get_db_url() -> str:
    """URLni formatlash va drayverlarni tekshirish"""
    url = config.DB_URL.get_secret_value() if hasattr(config.DB_URL, "get_secret_value") else config.DB_URL

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
        url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url


DB_URL = get_db_url()
IS_SQLITE = "sqlite" in DB_URL

# 1. Engine sozlamalari
# SQLite uchun StaticPool ishlatish tavsiya etiladi (ayniqsa :memory: yoki asinxron rejimda)
engine_kwargs = {
    "future": True,
    "echo": False,
}

if IS_SQLITE:
    # SQLite uchun ulanishlar bir vaqtda bitta bo'lishi xavfsizroq
    engine_kwargs.update({
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False}
    })
else:
    # Postgres uchun ulanishlar hovuzi
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
        "poolclass": AsyncAdaptedQueuePool
    })

engine = create_async_engine(DB_URL, **engine_kwargs)

# 2. Sessionmaker
# expire_on_commit=False -> ob'ektlarni commitdan keyin ham o'qishga ruxsat beradi
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


# 3. Bazani ishga tushirish
async def init_db():
    from database.models import Base
    try:
        async with engine.begin() as conn:
            if IS_SQLITE:
                await conn.exec_driver_sql("PRAGMA foreign_keys = ON")
                await conn.exec_driver_sql("PRAGMA journal_mode = WAL")  # Tezlikni oshiradi

            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Ma'lumotlar bazasi tayyor.")
    except Exception as e:
        logger.error(f"❌ Bazada xatolik: {e}")
        raise


# 4. Dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()