import logging
from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import Movie
from handlers.start import safe_edit_message

router = Router()


@router.callback_query(F.data == "random_movie")
async def random_movie_handler(callback: types.CallbackQuery, session: AsyncSession):

    stmt = select(Movie).order_by(func.random()).limit(1)
    result = await session.execute(stmt)
    movie = result.scalar_one_or_none()

    if not movie:
        return await callback.answer("😔 Bazada hozircha kinolar yo'q.", show_alert=True)

    await session.refresh(movie)

    title = movie.title.upper() if movie.title else "NOMA'LUM"

    text = (
        "🎲 <b>OMADLI TANLOV!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎬 <b>Nomi:</b> <code>{title}</code>\n"
        f"🆔 <b>Kodi:</b> <code>{movie.code}</code>\n"
        f"👁 <b>Ko'rilgan:</b> <code>{movie.views:,} marta</code>\n\n"
        "✨ <i>Nima ko'rishni bilmayotgan bo'lsangiz, ushbu filmni tavsiya qilamiz!</i>\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    builder = InlineKeyboardBuilder()

    builder.row(types.InlineKeyboardButton(
        text="🎞 Kinoni ko'rish",
        callback_data=f"movie_{movie.id}")
    )
    builder.row(
        types.InlineKeyboardButton(text="🔄 Boshqa tanlov", callback_data="random_movie"),
        types.InlineKeyboardButton(text="🏠 Menyuga", callback_data="back_to_main")
    )

    try:
        await callback.answer("🎲 Sizga nima tusharkin...")
        await safe_edit_message(callback, text, builder.as_markup())
    except Exception as e:
        logging.error(f"Random movie UI error: {e}")
        await callback.message.answer(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )