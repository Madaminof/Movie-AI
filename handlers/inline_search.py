import logging
from aiogram import Router, types, F
from aiogram.types import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, String, cast, desc
from database.models import Movie

router = Router()

# Dizayn elementlari
MOVIE_ICON = "https://cdn-icons-png.flaticon.com/512/4221/4221419.png"
TRENDING_ICON = "https://cdn-icons-png.flaticon.com/512/1792/1792855.png"
NOT_FOUND_ICON = "https://cdn-icons-png.flaticon.com/512/6134/6134065.png"


@router.inline_query()
async def inline_movie_search(query: types.InlineQuery, session: AsyncSession):
    """
    Inline qidiruv: Kinolarni nomi, kodi yoki tavsifi bo'yicha topish.
    """
    search_text = query.query.strip()
    bot_info = await query.bot.get_me()
    results = []

    try:
        # 1. Qidiruv mantig'i
        if not search_text:
            # Agar foydalanuvchi hali hech narsa yozmagan bo'lsa - TRENDDAGI kinolarni ko'rsatamiz
            stmt = select(Movie).order_by(desc(Movie.views)).limit(15)
            switch_text = "🔥 Eng ommabop kinolar ro'yxati"
        else:
            # Nom, kod yoki tavsif bo'yicha aqlli qidiruv
            stmt = (
                select(Movie)
                .where(
                    or_(
                        Movie.title.ilike(f"%{search_text}%"),
                        cast(Movie.code, String).contains(search_text),
                        Movie.description.ilike(f"%{search_text}%")
                    )
                )
                .order_by(desc(Movie.views))
                .limit(50)
            )
            switch_text = f"🔎 '{search_text}' bo'yicha qidiruv natijalari"

        db_result = await session.execute(stmt)
        movies = db_result.scalars().all()

        # 2. Natijalarni premium ko'rinishda shakllantirish
        if movies:
            for m in movies:
                # Botga o'tish uchun Deep Link (start=code)
                direct_link = f"https://t.me/{bot_info.username}?start={m.code}"

                # Natija ko'rinishi
                results.append(
                    InlineQueryResultArticle(
                        id=f"movie_{m.id}",
                        title=f"🎬 {m.title.upper()}",
                        description=f"🍿 Kod: {m.code} | 👁 {m.views:,} ko'rish | 📅 {m.created_at.year}",
                        thumbnail_url=MOVIE_ICON if search_text else TRENDING_ICON,
                        input_message_content=InputTextMessageContent(
                            message_text=(
                                f"🎬 <b>{m.title.upper()}</b>\n"
                                f"━━━━━━━━━━━━━━━━━━━━\n"
                                f"🆔 <b>Kino kodi:</b> <code>{m.code}</code>\n"
                                f"👁 <b>Ko'rilgan:</b> <code>{m.views:,}</code> marta\n"
                                f"📅 <b>Yuklangan:</b> <code>{m.created_at.strftime('%d.%m.%Y')}</code>\n\n"
                                f"📥 <b>Kinoni ko'rish uchun pastdagi tugmani bosing:</b>"
                            ),
                            parse_mode="HTML"
                        ),
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="🎞 Kinoni ko'rish", url=direct_link)]
                        ])
                    )
                )
        elif search_text:
            # Hech narsa topilmasa (Empty State)
            results.append(
                InlineQueryResultArticle(
                    id="not_found",
                    title="❌ Hech narsa topilmadi",
                    description="Kechirasiz, qidiruvingiz bo'yicha kino mavjud emas.",
                    thumbnail_url=NOT_FOUND_ICON,
                    input_message_content=InputTextMessageContent(
                        message_text=f"🧐 <b>'{search_text}'</b> bo'yicha hech qanday kino topilmadi.\n\n"
                                     f"Iltimos, kino nomini to'g'ri yozganingizni tekshiring yoki kod orqali qidirib ko'ring."
                    )
                )
            )

        # 3. Javobni qaytarish (Optimallashtirilgan kesh bilan)
        await query.answer(
            results=results,
            cache_time=300,  # 5 daqiqa kesh serverni yuklamadan asraydi
            is_personal=False,
            switch_pm_text=switch_text,
            switch_pm_parameter="inline_search",
        )

    except Exception as e:
        logging.error(f"❌ Inline search error: {e}", exc_info=True)