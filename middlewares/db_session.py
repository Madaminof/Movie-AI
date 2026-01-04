import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select
from database.models import User # Sizning User modelingiz

logger = logging.getLogger(__name__)

class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        self.session_pool = session_pool
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        # Foydalanuvchi ma'lumotlarini olish (event.from_user aiogramda mavjud)
        tg_user: TgUser = data.get("event_from_user")

        async with self.session_pool() as session:
            data["session"] = session

            if tg_user and not tg_user.is_bot:
                # 1. Foydalanuvchini bazadan qidirish (user_id bo'yicha)
                result = await session.execute(
                    select(User).where(User.user_id == tg_user.id)
                )
                db_user = result.scalar_one_or_none()

                if not db_user:
                    # 2. Yangi foydalanuvchi bo'lsa - bazaga qo'shish
                    new_user = User(
                        user_id=tg_user.id,
                        full_name=tg_user.full_name,
                        username=tg_user.username
                    )
                    session.add(new_user)
                    await session.commit()
                    logger.info(f"🆕 Yangi foydalanuvchi ro'yxatga olindi: {tg_user.id}")
                else:
                    # 3. Agar mavjud bo'lsa, ismini yoki usernameni yangilab qo'yamiz
                    # Bu statistika va foydalanuvchi ro'yxati doim yangi bo'lishi uchun kerak
                    if db_user.full_name != tg_user.full_name or db_user.username != tg_user.username:
                        db_user.full_name = tg_user.full_name
                        db_user.username = tg_user.username
                        await session.commit()

            try:
                return await handler(event, data)
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Database error in middleware: {e}")
                raise e