import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from config import config
from database.connection import init_db
from handlers import start, admin_panel, movie_search


async def main():
    # 1. Loglarni sozlash
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )

    # 2. Ma'lumotlar bazasini yaratish
    await init_db()

    # 3. Botni yaratish
    # Eslatma: Agar DefaultBotProperties xato bersa, parse_mode-ni har bir javobda ko'rsatish mumkin
    # Lekin hozircha eng sodda usulda yaratamiz
    bot = Bot(token=config.BOT_TOKEN.get_secret_value())

    dp = Dispatcher()

    # 4. Handlerlarni (Routerlarni) ulash
    dp.include_routers(
        start.router,
        admin_panel.router,
        movie_search.router
    )

    logging.info("🚀 Bot muvaffaqiyatli ishga tushdi!")

    try:
        # Tozalash
        await bot.delete_webhook(drop_pending_updates=True)
        # Pollingni boshlash
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("🤖 Bot to'xtatildi!")