import asyncio
import logging
import sys
from typing import Any, Callable, Dict, Awaitable
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.methods import TelegramMethod
from config import config
from database.connection import async_session, init_db
from handlers.mainFunctions.check_subs import router as check_sub_handler_router
from handlers.mainFunctions.cmd_start import router as cmd_start_router
from handlers.mainFunctions.help import router as help_router
from handlers.mainFunctions.statistic import router as statistic_router
from handlers.mainFunctions.trending import router as trending_router
from handlers.mainFunctions.random_movie import router as random_movie_router
from handlers import start, movie_search, inline_search
from admin import main_menu, movie_ops, broadcast, statistics
from middlewares.db_session import DbSessionMiddleware
from middlewares.check_sub import CheckSubMiddleware


class ParseModeMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
            event: Any,
            data: Dict[str, Any]
    ) -> Any:

        result = await handler(event, data)
        if isinstance(result, TelegramMethod):
            if not result.parse_mode:
                result.parse_mode = "HTML"
        return result


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


async def main():
    await init_db()

    bot = Bot(token=config.BOT_TOKEN.get_secret_value())

    dp = Dispatcher()

    dp.update.outer_middleware(DbSessionMiddleware(session_pool=async_session))

    dp.message.middleware(ParseModeMiddleware())
    dp.callback_query.middleware(ParseModeMiddleware())

    dp.message.middleware(CheckSubMiddleware())
    dp.callback_query.middleware(CheckSubMiddleware())

    dp.include_routers(
        broadcast.router,
        main_menu.router,
        movie_ops.router,
        statistics.router,
        check_sub_handler_router,
        cmd_start_router,
        help_router,
        statistic_router,
        trending_router,
        random_movie_router,
        start.router,
        inline_search.router,
        movie_search.router
    )

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        logger.info("🚀 Bot polling rejimida ishga tushdi...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"❌ Bot xatosi: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🤖 Bot to'xtatildi")