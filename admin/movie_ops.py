import re
import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from database.models import Movie
from states.movie_states import AddMovie
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


def get_back_btn():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 Admin Menyuga Qaytish", callback_data="admin_menu"))
    return builder.as_markup()


@router.callback_query(F.data == "admin_add_movie")
async def start_movie_add(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddMovie.waiting_for_video)

    text = (
        "📥 <b>YANGI KINO QO'SHISH TIZIMI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Admin, videoni quyidagi usullarda yuborishingiz mumkin:\n\n"
        "✅ <b>Avtomatik usul:</b>\n"
        "Videoni yuboring va izohiga (caption) <code>KOD NOMI</code> yozing.\n"
        "<i>Misol: 545 O'rgimchak odam</i>\n\n"
        "✅ <b>Oddiy usul:</b>\n"
        "Faqat videoni o'zini yuboring, ma'lumotlarni keyingi bosqichda so'rayman.\n\n"
        "⚠️ <i>Eslatma: Video fayl yoki Document ko'rinishida yuborish mumkin.</i>"
    )

    await callback.message.edit_text(text, reply_markup=get_back_btn(), parse_mode="HTML")


@router.message(AddMovie.waiting_for_video, F.video | F.document)
async def process_movie_video(message: types.Message, state: FSMContext, session: AsyncSession):
    media = message.video if message.video else message.document
    file_id = media.file_id
    raw_text = message.caption if message.caption else getattr(media, 'file_name', '')

    # Regex orqali tekshirish
    if raw_text:
        match = re.search(r'^(\d+)\s+(.+)$', raw_text.strip())
        if match:
            code = int(match.group(1))
            title = match.group(2).replace('.mp4', '').replace('.mkv', '').strip().upper()

            try:
                await session.execute(insert(Movie).values(code=code, title=title, file_id=file_id))
                await session.commit()
                await state.clear()

                success_text = (
                    "✅ <b>KINO BAZAGA QO'SHILDI!</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "🆔 <b>Kino kodi:</b> <code>{code}</code>\n"
                    "🎬 <b>Nomi:</b> <code>{title}</code>\n"
                    "💎 <b>Holati:</b> Tayyor"
                ).format(code=code, title=title)

                return await message.answer(success_text, reply_markup=get_back_btn(), parse_mode="HTML")
            except Exception:
                await session.rollback()
                return await message.answer("❌ <b>XATO:</b> Bu kod (ID) bazada mavjud!", parse_mode="HTML")

    # Agar ma'lumot ajratib bo'lmasa
    await state.update_data(file_id=file_id)
    await state.set_state(AddMovie.waiting_for_details)

    await message.answer(
        "🧐 <b>Ma'lumotlar aniqlanmadi</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Iltimos, ushbu kino uchun <b>KOD</b> va <b>NOM</b>ni yuboring:\n\n"
        "📝 Format: <code>125 Forsaj 9</code>",
        reply_markup=get_back_btn(),
        parse_mode="HTML"
    )


@router.message(AddMovie.waiting_for_details, F.text)
async def process_manual_details(message: types.Message, state: FSMContext, session: AsyncSession):
    match = re.search(r'^(\d+)\s+(.+)$', message.text.strip())

    if not match:
        return await message.answer(
            "⚠️ <b>XATO FORMAT!</b>\n\n"
            "Iltimos, avval raqam (kod), keyin nomini yozing.\n"
            "Misol: <code>125 Forsaj 9</code>",
            parse_mode="HTML"
        )

    code = int(match.group(1))
    title = match.group(2).strip().upper()
    data = await state.get_data()

    try:
        await session.execute(insert(Movie).values(code=code, title=title, file_id=data['file_id']))
        await session.commit()
        await state.clear()

        final_text = (
            "🎯 <b>MUVAFFAQIYATLI SAQLANDI!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🆔 Kod: <code>{code}</code>\n"
            "🎬 Nomi: <code>{title}</code>"
        ).format(code=code, title=title)

        await message.answer(final_text, reply_markup=get_back_btn(), parse_mode="HTML")
    except Exception:
        await session.rollback()
        await message.answer("❌ <b>BAZAGA SAQLASHDA XATO!</b>\nUshbu kod band bo'lishi mumkin.", parse_mode="HTML")