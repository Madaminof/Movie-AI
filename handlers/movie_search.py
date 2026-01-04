import logging
from typing import Union
from aiogram import Router, types, F
from aiogram.exceptions import TelegramEntityTooLarge, TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert  # SQLite uchun maxsus insert

from database.models import Movie, MovieView
from keyboards.inline import movie_action_keyboard

router = Router()

import logging
from typing import Union
from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import Movie
from database.requests import increment_movie_view
from keyboards.inline import movie_action_keyboard

router = Router()


async def process_movie_delivery(
        event: Union[types.Message, types.CallbackQuery],
        movie: Movie,
        session: AsyncSession
):
    user_id = event.from_user.id
    message = event.message if isinstance(event, types.CallbackQuery) else event

    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_video")

    try:
        await increment_movie_view(session, user_id, movie.id)

        await session.refresh(movie)
    except Exception as e:
        logging.error(f"Statistika yangilashda xato: {e}")
        await session.rollback()

    title = movie.title.upper() if movie.title else "NOMA'LUM KINO"

    caption = (
        f"🎬 <b>{title}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>Kino kodi:</b> <code>{movie.code}</code>\n"
        f"👁 <b>Ko'rilgan:</b> <code>{movie.views:,}</code> marta\n"
        f"⭐ <b>Sifati:</b> <code>Full HD</code>\n"
        f"📡 <b>Kanal:</b> @android_notes_developer\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🍿 <b>Yoqimli tomosha tilaymiz!</b>"
    )

    reply_markup = movie_action_keyboard(title, movie.code)

    try:
        await message.answer_video(
            video=movie.file_id,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        if isinstance(event, types.CallbackQuery):
            await event.answer()
    except Exception as e:
        logging.error(f"Video yuborishda xato: {e}")
        await message.answer("⚠️ Video yuborishda xatolik! Fayl o'chgan yoki formati noto'g'ri.")


@router.message(F.text)
async def search_by_code_handler(message: types.Message, session: AsyncSession):
    raw_text = message.text.strip()

    if not raw_text.isdigit():
        return

    movie_code = int(raw_text)

    stmt = select(Movie).where(Movie.code == movie_code)
    result = await session.execute(stmt)
    movie = result.scalar_one_or_none()

    if movie:
        await process_movie_delivery(message, movie, session)
    else:
        await message.answer(f"🔍 <b>Kod: {movie_code}</b>\n\nAfsuski, hech narsa topilmadi. 😔")


@router.callback_query(F.data.startswith("movie_"))
async def search_by_callback_handler(callback: types.CallbackQuery, session: AsyncSession):
    """Tugma orqali kino ko'rish"""
    movie_id = int(callback.data.split("_")[1])

    stmt = select(Movie).where(Movie.id == movie_id)
    result = await session.execute(stmt)
    movie = result.scalar_one_or_none()

    if movie:
        await process_movie_delivery(callback, movie, session)
    else:
        await callback.answer("❌ Film bazadan o'chirilgan!", show_alert=True)