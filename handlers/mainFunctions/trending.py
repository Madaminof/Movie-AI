import logging
from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from database.models import Movie
from handlers.start import safe_edit_message

router = Router()


@router.callback_query(F.data == "trending")
async def trending_movies_handler(callback: types.CallbackQuery, session: AsyncSession):

    stmt = select(Movie).order_by(desc(Movie.views)).limit(10)
    result = await session.execute(stmt)
    movies = result.scalars().all()

    header = "🔥 <b>HAFTALIK TRENDDAGI FILMLAR</b>\n"
    divider = "━━━━━━━━━━━━━━━━━━━━\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    builder = InlineKeyboardBuilder()

    if not movies:
        text = (
            f"{header}{divider}"
            "<i>📉 Hozircha trendlar bo'sh. Birinchi bo'lib kino ko'ring va trendni shakllantiring!</i>\n"
            f"{divider}"
        )
    else:
        text_parts = [header, "<i>Eng ko'p ko'rilgan saralangan filmlar:</i>\n", divider]

        for i, m in enumerate(movies):
            title = m.title.upper() if m.title else "NOMA'LUM"
            if i < 10:
                text_parts.append(
                    f"{medals[i]} <b>{title}</b>\n"
                    f"└ 👁 <code>{m.views:,}</code> | 🆔 <code>{m.code}</code>\n"
                )

            builder.row(types.InlineKeyboardButton(
                text=f"{medals[i]} {title[:20]}...",
                callback_data=f"movie_{m.id}")
            )

        text = "".join(text_parts) + divider + "✨ <i>Ko'rmoqchi bo'lgan filmingizni tanlang:</i>"

    builder.row(
        types.InlineKeyboardButton(text="🔄 Yangilash", callback_data="trending"),
        types.InlineKeyboardButton(text="🏠 Menyu", callback_data="back_to_main")
    )

    try:
        await safe_edit_message(callback, text, builder.as_markup())
        await callback.answer("🔥 Trendlar yangilandi")
    except Exception as e:
        logging.error(f"Trending UI Error: {e}")
        await callback.answer("Trendlar allaqachon yangi")