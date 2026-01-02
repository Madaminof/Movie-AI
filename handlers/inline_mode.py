import logging
from aiogram import Router, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, String, cast, func
from database.models import Movie

router = Router()

# Ikonkalar (Dizaynni boyitish uchun)
MOVIE_ICON = "https://cdn-icons-png.flaticon.com/512/4221/4221419.png"
NOT_FOUND_ICON = "https://cdn-icons-png.flaticon.com/512/6134/6134065.png"

@router.inline_query()
async def inline_movie_search(query: types.InlineQuery, session: AsyncSession):
    """
    Kinolarni nomi yoki kodi bo'yicha aqlli va chiroyli inline qidiruv.
    """
    search_text = query.query.strip()
    bot_info = await query.bot.get_me()

    # 1. BO'SH SO'ROV UCHUN: Trenddagi yoki eng ko'p ko'rilgan 10 ta kinoni chiqaramiz
    if not search_text:
        stmt = select(Movie).order_by(Movie.views.desc()).limit(15)
        result = await session.execute(stmt)
        movies = result.scalars().all()
        switch_text = "🔥 Trenddagi kinolar"
    else:
        # 2. QIDIRUV LOGIKASI: Nomi, kodi yoki tavsifi bo'yicha (Smart ilike)
        stmt = (
            select(Movie)
            .where(
                or_(
                    Movie.title.ilike(f"%{search_text}%"),
                    cast(Movie.code, String).startswith(search_text),
                    Movie.description.ilike(f"%{search_text}%") # Tavsif bo'yicha ham qidirish
                )
            )
            .order_by(Movie.views.desc())
            .limit(25)
        )
        result = await session.execute(stmt)
        movies = result.scalars().all()
        switch_text = f"🔎 '{search_text}' bo'yicha natijalar"

    results = []

    # 3. NATIJALARNI SHAKLLANTIRISH
    for m in movies:
        # Deep Link: Foydalanuvchi botga o'tganda darrov shu kinoni topishi uchun
        # T.me/bot_username?start=movie_1234
        start_app_url = f"https://t.me/{bot_info.username}?start={m.code}"

        results.append(
            InlineQueryResultArticle(
                id=f"movie_{m.id}",
                title=f"🎬 {m.title.upper()}",
                description=f"🍿 Kod: {m.code} | 👁 {m.views:,} marta ko'rilgan",
                thumbnail_url=MOVIE_ICON,
                input_message_content=InputTextMessageContent(
                    message_text=(
                        f"🎬 <b>{m.title.upper()}</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🆔 <b>Kino kodi:</b> <code>{m.code}</code>\n"
                        f"👁 <b>Ko'rilgan:</b> <code>{m.views:,}</code> marta\n\n"
                        f"📥 <b>Kinoni ko'rish uchun pastdagi tugmani bosing:</b>"
                    ),
                    parse_mode="HTML"
                ),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🎞 Kinoni ko'rish", url=start_app_url)]
                ])
            )
        )

    # 4. AGAR KINO TOPILMASA (Empty State)
    if not results and search_text:
        results.append(
            InlineQueryResultArticle(
                id="not_found",
                title="❌ Hech narsa topilmadi",
                description="Boshqa so'z bilan qidirib ko'ring...",
                thumbnail_url=NOT_FOUND_ICON,
                input_message_content=InputTextMessageContent(
                    message_text=f"🧐 Kechirasiz, <b>'{search_text}'</b> bo'yicha hech qanday kino topilmadi."
                )
            )
        )

    # 5. JAVOBNI YUBORISH (Optimallashtirilgan)
    await query.answer(
        results=results,
        is_personal=False,
        cache_time=300, # 5 daqiqa kesh (server yuklamasini kamaytirish uchun)
        switch_pm_text=switch_text,
        switch_pm_parameter="inline_search"
    )