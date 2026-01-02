import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

logger = logging.getLogger(__name__)


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        """
        Sessiya pulini (pool) saqlash uchun konstruktor.
        """
        self.session_pool = session_pool
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        """
        Har bir Telegram event uchun alohida DB sessiya ochadi.
        """
        # 'async with' avtomatik ravishda sessiyani yopishni (close) boshqaradi
        async with self.session_pool() as session:
            # Sessiyani data lug'atiga qo'shish
            data["session"] = session

            try:
                # Handlerni chaqirish
                return await handler(event, data)

            except Exception as e:
                # Kutilmagan xato yuz bersa, rollback qilish
                await session.rollback()
                logger.error(f"❌ Database error in middleware: {e}")
                raise e
            # Bu yerda 'finally' bloki va 'session.close()' shart emas,
            # chunki 'async with' buni o'zi bajaradi.