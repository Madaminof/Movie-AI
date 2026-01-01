import logging
from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, insert, select
from sqlalchemy.exc import IntegrityError

from database.models import Movie, MovieView
from database.crud import get_movie_by_code
from keyboards.inline import movie_action_keyboard

router = Router()


async def process_movie_delivery(event: [types.Message, types.CallbackQuery], movie: Movie, session: AsyncSession):
    """
    Kino yetkazib berish, unikal ko'rishni hisoblash va UI ko'rsatish uchun markaziy funksiya.
    """
    user_id = event.from_user.id
    chat_id = event.message.chat.id if isinstance(event, types.CallbackQuery) else event.chat.id

    # 1. Vizual effekt: Bot video yuklayotganini ko'rsatadi
    await event.bot.send_chat_action(chat_id=chat_id, action="upload_video")

    # 2. Unikal ko'rishlar mantig'i (Tranzaksiya ichida)
    try:
        # MovieView jadvaliga yozish orqali unikal ko'rishni tekshiramiz
        await session.execute(
            insert(MovieView).values(user_id=user_id, movie_id=movie.id)
        )
        # Agar yuqoridagi qator xato (IntegrityError) bermasa, demak bu yangi ko'rish
        await session.execute(
            update(Movie).where(Movie.id == movie.id).values(views=Movie.views + 1)
        )
        await session.commit()
    except IntegrityError:
        # Foydalanuvchi bu kinoni oldin ko'rgan, shunchaki o'tkazib yuboramiz
        await session.rollback()

    # Yangilangan ko'rishlar soni bilan caption tayyorlash
    await session.refresh(movie)

    caption = (
        f"🎬 <b>{movie.title.upper()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>Kino kodi:</b> <code>{movie.code}</code>\n"
        f"👁 <b>Ko'rildi:</b> <code>{movie.views:,}</code> marta\n"
        f"🎭 <b>Janr:</b> #Kino #Premyera\n"
        f"📡 <b>Kanal:</b> @android_notes_developer\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🍿 <b>Yoqimli tomosha tilaymiz!</b>"
    )

    # 3. Videoni yuborish (Message yoki CallbackQuery ligiga qarab)
    reply_markup = movie_action_keyboard(movie.title, movie.code)

    try:
        if isinstance(event, types.CallbackQuery):
            await event.message.answer_video(video=movie.file_id, caption=caption, reply_markup=reply_markup)
            await event.answer()  # Callback aylanib turmasligi uchun
        else:
            await event.answer_video(video=movie.file_id, caption=caption, reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Video yuborishda xato: {e}")
        error_text = "⚠️ Video faylda xatolik (file_id noto'g'ri yoki o'chirilgan)."
        if isinstance(event, types.CallbackQuery):
            await event.message.answer(error_text)
        else:
            await event.answer(error_text)


# --- HANDLERLAR ---

@router.message(F.text.isdigit())
async def search_by_text_handler(message: types.Message, session: AsyncSession):
    """Kino kodini raqam ko'rinishida yuborganda"""
    movie_code = int(message.text)
    movie = await get_movie_by_code(session, movie_code)

    if movie:
        await process_movie_delivery(message, movie, session)
    else:
        not_found_text = (
            "⚠️ <b>KINO TOPILMADI</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"Kod: <b>{movie_code}</b>\n\n"
            "🧐 <i>Kod xato kiritilgan yoki film bazadan o'chirilgan bo'lishi mumkin.</i>"
        )
        await message.answer(not_found_text)


@router.callback_query(F.data.startswith("movie_"))
async def search_by_callback_handler(callback: types.CallbackQuery, session: AsyncSession):
    """Tugma (masalan, Random orqali) bosilganda"""
    movie_code = int(callback.data.split("_")[1])
    movie = await get_movie_by_code(session, movie_code)

    if movie:
        await process_movie_delivery(callback, movie, session)
    else:
        await callback.answer("❌ Film topilmadi yoki o'chirilgan!", show_alert=True)