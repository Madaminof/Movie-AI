import re
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from database.models import Movie
from states.movie_states import AddMovie
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


def get_back_btn():
    return InlineKeyboardBuilder().add(
        types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_menu")
    ).as_markup()


@router.callback_query(F.data == "admin_add_movie")
async def start_movie_add(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddMovie.waiting_for_video)
    await callback.message.edit_text(
        "📽 <b>Kino qo'shish tizimi</b>\n\n"
        "Siz quyidagicha qo'shishingiz mumkin:\n"
        "1️⃣ Videoni o'zini yuboring (keyin ma'lumot so'rayman).\n"
        "2️⃣ Videoni <b>Forward</b> qiling (nomidan o'zim ajratib olaman).\n"
        "3️⃣ Videoga izoh (caption) yozib yuboring.\n\n"
        "📝 <i>Masalan: '545 O'rgimchak odam'</i>",
        reply_markup=get_back_btn()
    )


@router.message(AddMovie.waiting_for_video, F.video | F.document)
async def process_movie_video(message: types.Message, state: FSMContext, session: AsyncSession):
    # Video yoki Document ekanligini aniqlash
    media = message.video if message.video else message.document
    file_id = media.file_id

    # Nomi yoki sarlavhasini olish (Caption bo'lmasa fayl nomi)
    raw_text = message.caption if message.caption else getattr(media, 'file_name', '')

    if raw_text:
        # Regular expression orqali matn boshidagi raqamni (kodni) va qolgan matnni (nomini) ajratish
        # Masalan: "125 Forsaj 9" -> group(1): 125, group(2): Forsaj 9
        match = re.search(r'^(\d+)\s+(.+)$', raw_text.strip())

        if match:
            code = int(match.group(1))
            title = match.group(2).replace('.mp4', '').replace('.mkv', '').strip()

            try:
                await session.execute(insert(Movie).values(code=code, title=title, file_id=file_id))
                await session.commit()
                await state.clear()
                return await message.answer(
                    f"✅ <b>Aqlli tizim orqali saqlandi!</b>\n\n"
                    f"🆔 Kod: <code>{code}</code>\n"
                    f"🎬 Nomi: <b>{title}</b>",
                    reply_markup=get_back_btn()
                )
            except Exception:
                await session.rollback()
                return await message.answer("❌ Xatolik: Bu kod bazada bor yoki boshqa xato.")

    # Agar matndan ma'lumot ajratib bo'lmasa, navbatma-navbat so'raymiz
    await state.update_data(file_id=file_id)
    await state.set_state(AddMovie.waiting_for_details)
    await message.answer(
        "🧐 Videodan ma'lumotlarni aniqlab bo'lmadi.\n\n"
        "Iltimos, kino kodi va nomini mana bunday yuboring:\n"
        "<code>KOD NOMI</code> (masalan: 125 Forsaj 9)",
        reply_markup=get_back_btn()
    )


@router.message(AddMovie.waiting_for_details, F.text)
async def process_manual_details(message: types.Message, state: FSMContext, session: AsyncSession):
    match = re.search(r'^(\d+)\s+(.+)$', message.text.strip())

    if not match:
        return await message.answer(
            "⚠️ Xato format! Avval raqam (kod), keyin nomini yozing.\nMisol: <code>125 Forsaj 9</code>")

    code = int(match.group(1))
    title = match.group(2).strip()
    data = await state.get_data()

    try:
        await session.execute(insert(Movie).values(code=code, title=title, file_id=data['file_id']))
        await session.commit()
        await state.clear()
        await message.answer(f"🎯 <b>Muvaffaqiyatli saqlandi!</b>\n🆔 {code} | 🎬 {title}")
    except Exception:
        await session.rollback()
        await message.answer("❌ Bazaga saqlashda xato (Kod band bo'lishi mumkin).")