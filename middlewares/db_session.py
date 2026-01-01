from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        """
        Sessiya pulini saqlash uchun konstruktor.
        """
        self.session_pool = session_pool

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        """
        Har bir update uchun alohida DB sessiya ochadi va uni handlerlarga uzatadi.
        """
        async with self.session_pool() as session:
            # 1. Sessiyani ma'lumotlar lug'atiga qo'shamiz
            data["session"] = session

            try:
                # 2. Handlerni chaqiramiz
                result = await handler(event, data)

                # Agar handler muvaffaqiyatli tugasa, o'zgarishlarni saqlash mumkin
                # (Lekin odatda commit handler ichida qilinadi)
                return result

            except Exception as e:
                # 3. Xatolik bo'lsa rollback qilish (agar commit qilinmagan bo'lsa)
                await session.rollback()
                raise e
            finally:
                # 4. 'async with' blokidan chiqishda sessiya avtomatik yopiladi (close)
                pass