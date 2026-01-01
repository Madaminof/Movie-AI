import logging
from aiogram import Router, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, String, cast
from database.models import Movie

router = Router()

# Inline natijalar uchun premium ikonka (Kino ramzi)
MOVIE_ICON = "https://cdn-icons-png.flaticon.com/512/4221/4221419.png"

@router.inline_query()
async def inline_movie_search(query: types.InlineQuery, session: AsyncSession):
    """
    Inline qidiruv: Kinolarni nomi yoki kodi bo'yicha real vaqtda qidirish.
    """
    # Foydalanuvchi yozayotgan so'zni tozalab olamiz
    search_text = query.query.strip()

    # So'rov bo'sh bo'lsa, javob qaytarmaymiz (yoki eng trenddagi 10 ta kinoni chiqarish mumkin)
    if not search_text:
        return

    try:
        # 1. DATABASE QIDIRUV (Real-time ma'lumotlar bilan)
        # Nomi bo'yicha ilike (registrga sezgirmas) yoki Kodi bo'yicha boshlanishi
        stmt = (
            select(Movie)
            .where(
                or_(
                    Movie.title.ilike(f"%{search_text}%"),
                    cast(Movie.code, String).startswith(search_text)
                )
            )
            .order_by(Movie.views.desc())  # Eng ommaboplarini tepaga chiqaramiz
            .limit(20)
        )

        result = await session.execute(stmt)
        movies = result.scalars().all()

        if not movies:
            return

        results = []
        bot_info = await query.bot.get_me()

        # 2. NATIJALARNI SHAKLLANTIRISH (Premium UI)
        for m in movies:
            # Inline natijalar ro'yxatida ko'rinadigan qism
            results.append(
                InlineQueryResultArticle(
                    id=f"movie_{m.id}",
                    title=f"🎬 {m.title.upper()}",
                    description=f"🍿 Kod: {m.code} | 👁 Ko'rilgan: {m.views:,}",
                    thumbnail_url=MOVIE_ICON,
                    input_message_content=InputTextMessageContent(
                        message_text=(
                            f"🎬 <b>{m.title.upper()}</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"🆔 <b>Kino kodi:</b> <code>{m.code}</code>\n"
                            f"👁 <b>Ko'rilgan:</b> <code>{m.views:,}</code> marta\n"
                            f"📡 <b>Kanal:</b> @android_notes_developer\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"📥 <b>Kinoni ko'rish uchun botga kiring va kodni yuboring:</b>\n"
                            f"👉 @{bot_info.username}"
                        ),
                        parse_mode="HTML"
                    )
                )
            )

        # 3. JAVOB QAYTARISH (Real-time optimallashtirish)
        # cache_time=10 soniya qildik, shunda ko'rishlar soni tez-tez yangilanib turadi
        # switch_pm_text orqali foydalanuvchini botning ichiga yo'naltiramiz
        await query.answer(
            results=results,
            is_personal=False,
            cache_time=10,
            switch_pm_text="🔎 Bot ichidan batafsil qidirish",
            switch_pm_parameter="search_query"
        )

    except Exception as e:
        logging.error(f"❌ Inline qidiruvda xatolik: {e}")