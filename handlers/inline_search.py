import logging
from aiogram import Router, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, String, cast
from database.models import Movie

router = Router()

# Inline natijalar uchun premium ikonka
MOVIE_ICON = "https://cdn-icons-png.flaticon.com/512/4221/4221419.png"

@router.inline_query()
async def inline_movie_search(query: types.InlineQuery, session: AsyncSession):
    """
    Inline qidiruv: Foydalanuvchi yozayotgan matnni nomi yoki kodi bilan solishtiradi.
    """
    search_text = query.query.strip()

    # Agar qidiruv matni bo'sh bo'lsa, trenddagi kinolarni ko'rsatish mumkin
    # yoki shunchaki bo'sh javob qaytaramiz
    if not search_text:
        return

    try:
        # 1. Qidiruv logikasi: Nomi bo'yicha yoki kodi bo'yicha
        # ilike - registrga sezgir bo'lmagan qidiruv
        stmt = (
            select(Movie)
            .where(
                or_(
                    Movie.title.ilike(f"%{search_text}%"),
                    cast(Movie.code, String).startswith(search_text)
                )
            )
            .order_by(Movie.views.desc()) # Eng ommaboplarini yuqoriga chiqaramiz
            .limit(20)
        )

        result = await session.execute(stmt)
        movies = result.scalars().all()

        if not movies:
            return # Natija topilmasa javob qaytarmaymiz

        results = []
        bot_info = await query.bot.get_me()

        # 2. Natijalarni shakllantirish
        for m in movies:
            # Inline natijada chiqadigan matn
            display_title = f"{m.title.upper()}"
            display_desc = f"🍿 Kod: {m.code} | 👁 Ko'rishlar: {m.views:,}"

            # Xabar yuborilganda chiqadigan premium matn
            message_text = (
                f"🎬 <b>{m.title.upper()}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 <b>Kino kodi:</b> <code>{m.code}</code>\n"
                f"👁 <b>Ko'rilgan:</b> <code>{m.views:,}</code> marta\n\n"
                f"📥 <b>Ushbu kinoni ko'rish uchun quyidagi botga kirib, kodni yuboring:</b>\n"
                f"👉 @{bot_info.username}\n"
                f"━━━━━━━━━━━━━━━━━━━━"
            )

            results.append(
                InlineQueryResultArticle(
                    id=f"movie_{m.id}",
                    title=display_title,
                    description=display_desc,
                    thumbnail_url=MOVIE_ICON,
                    input_message_content=InputTextMessageContent(
                        message_text=message_text,
                        parse_mode="HTML"
                    )
                )
            )

        # 3. Javob yuborish
        await query.answer(
            results=results,
            cache_time=60,  # Ma'lumotlar tez-tez yangilanishi uchun keshni kamaytirdik
            is_personal=False,
            switch_pm_text="🤖 Botga o'tish va ko'proq qidirish",
            switch_pm_parameter="inline_help"
        )

    except Exception as e:
        logging.error(f"Inline search error: {e}")