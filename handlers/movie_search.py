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


async def process_movie_delivery(
        event: Union[types.Message, types.CallbackQuery],
        movie: Movie,
        session: AsyncSession
):
    """
    Kino yetkazib berishning universal va barqaror tizimi.
    """
    user_id = event.from_user.id
    message = event.message if isinstance(event, types.CallbackQuery) else event

    # 1. Ob'ektni sessiyaga qayta bog'lash va yangilash (MissingGreenlet davosi)
    try:
        # Bu qator ob'ektni sessiyaga qayta yuklaydi va atributlarni o'qishda xatoni oldini oladi
        await session.merge(movie)
        await session.refresh(movie)
    except Exception as e:
        logging.error(f"Ob'ektni yangilashda xato: {e}")

    # Chat Action: Video yuklanayotganini ko'rsatish
    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_video")

    # 2. Statistika: Unikal ko'rishni hisoblash (SQLite uchun moslangan)
    try:
        # SQLite uchun INSERT OR IGNORE logikasi
        view_stmt = sqlite_insert(MovieView).values(
            user_id=user_id,
            movie_id=movie.id
        ).on_conflict_do_nothing()

        view_result = await session.execute(view_stmt)

        if view_result.rowcount > 0:  # Agar yangi ko'rish bo'lsa
            await session.execute(
                update(Movie).where(Movie.id == movie.id).values(views=Movie.views + 1)
            )
            # O'zgarishlarni darrov bazaga yozamiz
            await session.commit()
            await session.refresh(movie)
    except Exception as e:
        await session.rollback()
        logging.error(f"Statistika yangilashda xato: {e}")

    # 3. Caption UI (Premium Dizayn)
    # Atributlarni o'zgaruvchiga olib olamiz (Xavfsizlik uchun)
    title = movie.title.upper() if movie.title else "NOMA'LUM KINO"
    code = movie.code
    views = movie.views

    caption = (
        f"🎬 <b>{title}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>Kino kodi:</b> <code>{code}</code>\n"
        f"👁 <b>Ko'rilgan:</b> <code>{views:,}</code> marta\n"
        f"⭐ <b>Sifati:</b> <code>Full HD</code>\n"
        f"📡 <b>Kanal:</b> @android_notes_developer\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🍿 <b>Yoqimli tomosha tilaymiz!</b>"
    )

    reply_markup = movie_action_keyboard(title, code)

    # 4. Videoni yuborish
    try:
        await message.answer_video(
            video=movie.file_id,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        if isinstance(event, types.CallbackQuery):
            await event.answer()
    except TelegramEntityTooLarge:
        await message.answer("⚠️ Kechirasiz, video fayl hajmi juda katta (20MB+).")
    except TelegramBadRequest as e:
        logging.error(f"Video yuborishda BadRequest: {e}")
        await message.answer("⚠️ Video fayl bazadan o'chirilgan bo'lishi mumkin.")
    except Exception as e:
        logging.error(f"Kutilmagan xato: {e}")
        await message.answer("❌ Texnik xatolik tufayli video yuborilmadi.")


# --- HANDLERLAR ---

@router.message(F.text.isdigit())
async def search_by_code_handler(message: types.Message, session: AsyncSession):
    """Kino kodini qidirish"""
    movie_code = int(message.text)

    # selectinload ishlatish keshdagi xatoliklarni kamaytiradi
    stmt = select(Movie).where(Movie.code == movie_code)
    result = await session.execute(stmt)
    movie = result.scalar_one_or_none()

    if movie:
        await process_movie_delivery(message, movie, session)
    else:
        await message.answer(
            f"🔍 <b>Kod: {movie_code}</b>\n\n"
            "Afsuski, bu kod bo'yicha hech qanday film topilmadi. 😔"
        )


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