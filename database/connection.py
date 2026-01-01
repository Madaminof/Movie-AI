from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import config

# Engine yaratish
engine = create_async_engine(url=config.DB_URL, echo=False) # Productionda echo=False bo'lishi kerak
# Session yaratuvchi
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    # Importni funksiya ichiga olamiz (Circular import oldini olish uchun)
    from database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)