import logging
import asyncio
from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import Movie
# Muhim: safe_edit_message funksiyasini tekshirib ko'ring!
from handlers.start import safe_edit_message

router = Router()

@router.callback_query(F.data == "random_movie")
async def random_movie_handler(callback: types.CallbackQuery, session: AsyncSession):
    """
    Bazadan tasodifiy kinoni tanlab beradi va HTML formatda ko'rsatadi.
    """

    # 1. Vizual effekt
    await callback.answer("🎲 Sizga nima tusharkin...")

    # 2. Tasodifiy kinoni olish (SQLite va Postgres uchun universal func.random())
    stmt = select(Movie).order_by(func.random()).limit(1)
    result = await session.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        return await callback.answer("😔 Bazada hali kinolar mavjud emas.", show_alert=True)

    # 3. UI uchun chiroyli matn (HTML teglari bilan)
    text = (
        "🎲 <b>OMADLI TANLOV!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎬 <b>Nomi:</b> <code>{movie.title.upper()}</code>\n"
        f"🆔 <b>Kodi:</b> <code>{movie.code}</code>\n"
        f"👁 <b>Ko'rilgan:</b> <code>{movie.views:,} marta</code>\n\n"
        "✨ <i>Nima ko'rishni bilmayotganlar uchun maxsus tanlov!</i>\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    # 4. Tugmalarni yasash
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="🎞 Kinoni ko'rish",
        callback_data=f"movie_{movie.id}")
    )
    builder.row(
        types.InlineKeyboardButton(text="🔄 Boshqa tanlov", callback_data="random_movie"),
        types.InlineKeyboardButton(text="🏠 Menyuga", callback_data="back_to_main")
    )

    # 5. Xabarni yuborish/tahrirlash
    try:
        # DIQQAT: safe_edit_message funksiyangiz ichiga kiring va
        # edit_text metodiga parse_mode="HTML" qo'shilganini tekshiring!
        await safe_edit_message(callback, text, builder.as_markup())
    except Exception as e:
        logging.error(f"Random movie UI error: {e}")
        # Agar tahrirlashda muammo bo'lsa, kafolatlangan usulda yangi xabar yuboramiz
        await callback.message.answer(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"  # <--- Barcha teglarni render qiladi
        )
        try:
            await callback.message.delete()
        except:
            pass