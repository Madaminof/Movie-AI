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
    """
    Haftalik trenddagi (eng ko'p ko'rilgan) kinolar ro'yxati.
    HTML format va interaktiv tugmalar bilan.
    """

    # 1. Bazadan TOP-5 eng ko'p ko'rilgan kinolarni olish
    stmt = select(Movie).order_by(desc(Movie.views)).limit(5)
    result = await session.execute(stmt)
    movies = result.scalars().all()

    # 2. UI Dizayn elementlari
    header = "🔥 <b>TOP-5 TRENDDAGI FILMLAR</b>\n"
    divider = "━━━━━━━━━━━━━━━━━━━━\n"
    footer = "\n✨ <i>Ko'rish uchun tugmalardan foydalaning yoki kodni yuboring!</i>"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    builder = InlineKeyboardBuilder()

    if not movies:
        text = f"{header}{divider}<i>Hozircha trendlar shakllanmadi...</i>"
    else:
        text_parts = [header, divider]
        for i, m in enumerate(movies):
            # Matn qismi
            text_parts.append(
                f"{medals[i]} <b>{m.title.upper()}</b>\n"
                f"└ 🆔 Kod: <code>{m.code}</code> | 👁 <code>{m.views:,}</code>\n"
            )

            # Dinamik tugmalar (Foydalanuvchi nomni bosib darrov ko'ra olishi uchun)
            builder.row(types.InlineKeyboardButton(
                text=f"{medals[i]} {m.title[:22]}...",
                callback_data=f"movie_{m.id}")
            )

        text = "".join(text_parts) + divider + footer

    # 3. Navigatsiya tugmasi
    builder.row(types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_main"))

    # 4. Xabarni yangilash
    try:
        # safe_edit_message ichida parse_mode="HTML" borligini tekshiring!
        await safe_edit_message(callback, text, builder.as_markup())
        await callback.answer("🔥 Trendlar yangilandi")
    except Exception as e:
        logging.error(f"Trending UI Error: {e}")
        # Zaxira varianti
        await callback.message.answer(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer()