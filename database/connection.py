from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config import config
import logging

logger = logging.getLogger(__name__)


# URL-ni xavfsiz formatga keltirish
def get_async_url(url: str) -> str:
    # Pydantic SecretStr bo'lsa stringga o'tkazamiz
    if hasattr(url, "get_secret_value"):
        url = url.get_secret_value()

    # SQLAlchemy asinxron ishlashi uchun +asyncpg shart
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


DATABASE_URL = get_async_url(config.DB_URL)

# Engine yaratish - Render va PostgreSQL uchun optimallashgan
engine = create_async_engine(
    url=DATABASE_URL,
    echo=False,
    pool_pre_ping=True,  # "Server has closed the connection" xatosini oldini oladi
    pool_size=5,  # Tekin planlar uchun ulanishlar sonini cheklaymiz
    max_overflow=10
)

# Session yaratuvchi
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    from database.models import Base
    try:
        async with engine.begin() as conn:
            # Jadvallarni yaratish
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Ma'lumotlar bazasi jadvallari muvaffaqiyatli tekshirildi/yaratildi.")
    except Exception as e:
        logger.error(f"❌ Bazani ishga tushirishda xatolik: {e}")
        raise e