import asyncio
import logging
import sys
from threading import Thread

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from config import config
from database.connection import init_db, async_session
from handlers import start, movie_search, inline_search
from middlewares.db_session import DbSessionMiddleware
from middlewares.check_sub import CheckSubMiddleware
from admin import main_menu, movie_ops, broadcast, statistics

# FastAPI uxlab qolishning oldini olish uchun
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def health_check():
    return {"status": "running", "bot": "AI Movie Vision"}

def run_web():
    # Render avtomatik taqdim etadigan PORT'ni oladi, bo'lmasa 8000
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

async def main():
    # 1. Loglarni sozlash
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )
    logger = logging.getLogger(__name__)

    # 2. Web-serverni alohida Thread'da ishga tushirish
    # Bu Render "Port 8000 is not bound" xatosini bermasligi va bot onlayn turishi uchun kerak
    logger.info("🌐 Web-server ishga tushmoqda...")
    Thread(target=run_web, daemon=True).start()

    # 3. Ma'lumotlar bazasini ishga tushirish
    await init_db()

    # 4. Bot yaratish
    try:
        from aiogram.client.default import DefaultBotProperties
        bot = Bot(
            token=config.BOT_TOKEN.get_secret_value(),
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
    except ImportError:
        bot = Bot(
            token=config.BOT_TOKEN.get_secret_value(),
            parse_mode=ParseMode.HTML
        )

    dp = Dispatcher()

    # 5. MIDDLEWARES
    dp.update.outer_middleware(DbSessionMiddleware(session_pool=async_session))
    dp.update.outer_middleware(CheckSubMiddleware())

    # 6. ROUTERS
    dp.include_routers(
        broadcast.router,
        main_menu.router,
        movie_ops.router,
        statistics.router,
        start.router,
        movie_search.router
    )

    logger.info("🚀 Bot AI Movie Vision ishga tushdi!")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    except Exception as e:
        logger.error(f"❌ Bot ishida jiddiy xatolik: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("🤖 Bot to'xtatildi!")