import logging
import asyncio
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, func

from config import config
from states.movie_states import AddMovie
from database.models import Movie, User

router = Router()

# Admin filtri
admin_filter = F.from_user.id == config.ADMIN_ID


# --- KEYBOARDS ---

def admin_main_markup():
    """Asosiy admin menyusi tugmalari"""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="➕ Kino qo'shish", callback_data="add_movie"))
    builder.row(
        types.InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
        types.InlineKeyboardButton(text="📢 Reklama yuborish", callback_data="broadcast")
    )
    # Oddiy foydalanuvchi interfeysiga o'tish (ixtiyoriy)
    builder.row(types.InlineKeyboardButton(text="🏠 Botga qaytish", callback_data="back_to_main"))
    return builder.as_markup()


def back_to_admin_markup():
    """Admin menyusiga qaytish tugmasi"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🔙 Admin menyuga qaytish", callback_data="admin_main"))
    return builder.as_markup()


def cancel_action_markup():
    """Jarayonni bekor qilish tugmasi"""
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_main"))
    return builder.as_markup()


# --- ADMIN KIRISH ---

@router.message(F.text.in_(["/admin", "/add"]), admin_filter)
async def admin_entry(message: types.Message, state: FSMContext):
    """Admin panelga kirish nuqtasi"""
    await state.clear()  # Har safar kirganda eski holatlarni tozalaydi
    if message.text == "/add":
        await state.set_state(AddMovie.waiting_for_video)
        return await message.answer("📽 <b>Kino qo'shish:</b> Videoni yuboring:", reply_markup=cancel_action_markup())

    await message.answer(
        "👨‍💻 <b>ADMINISTRATOR BOSHQARUVI</b>\n━━━━━━━━━━━━━━━━━━━━\nTanlang: 👇",
        reply_markup=admin_main_markup()
    )


@router.callback_query(F.data == "admin_main", admin_filter)
async def admin_main_callback(callback: types.CallbackQuery, state: FSMContext):
    """Callback orqali admin menyuga qaytish"""
    await state.clear()
    await callback.message.edit_text(
        "👨‍💻 <b>ADMINISTRATOR BOSHQARUVI</b>\n━━━━━━━━━━━━━━━━━━━━\nTanlang: 👇",
        reply_markup=admin_main_markup()
    )


# --- KINO QO'SHISH ---

@router.callback_query(F.data == "add_movie", admin_filter)
async def add_movie_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddMovie.waiting_for_video)
    await callback.message.edit_text(
        "📽 <b>1-QADAM:</b> Videoni yuboring.\n\n"
        "💡 <i>Yoki videoga 'kod | nomi' deb izoh yozib yuboring.</i>",
        reply_markup=cancel_action_markup()
    )


@router.message(AddMovie.waiting_for_video, admin_filter, F.video | F.document)
async def process_movie_video(message: types.Message, state: FSMContext, session: AsyncSession):
    file_id = message.video.file_id if message.video else message.document.file_id

    # Tezkor qo'shish mantiqi
    if message.caption and "|" in message.caption:
        try:
            code_str, title = message.caption.split("|", 1)
            code = int(code_str.strip())
            await session.execute(insert(Movie).values(code=code, title=title.strip(), file_id=file_id))
            await session.commit()
            await state.clear()
            return await message.answer(f"✅ <b>Saqlandi!</b>\n🆔 ID: <code>{code}</code>\n🎬 {title.strip()}",
                                        reply_markup=admin_main_markup())
        except Exception:
            await session.rollback()
            return await message.answer("❌ Xato! Kod raqam bo'lishi va takrorlanmasligi kerak.")

    await state.update_data(file_id=file_id)
    await state.set_state(AddMovie.waiting_for_details)
    await message.answer("📝 <b>2-QADAM:</b> Ma'lumotni yuboring: <code>kod | nomi</code>",
                         reply_markup=cancel_action_markup())


@router.message(AddMovie.waiting_for_details, admin_filter, F.text)
async def process_movie_details(message: types.Message, state: FSMContext, session: AsyncSession):
    if "|" not in message.text:
        return await message.answer("⚠️ Format: <code>kod | nomi</code>")

    try:
        code_str, title = message.text.split("|", 1)
        code = int(code_str.strip())
        data = await state.get_data()
        await session.execute(insert(Movie).values(code=code, title=title.strip(), file_id=data['file_id']))
        await session.commit()
        await state.clear()
        await message.answer(f"🎯 <b>Muvaffaqiyatli saqlandi!</b>", reply_markup=admin_main_markup())
    except Exception:
        await session.rollback()
        await message.answer("❌ Saqlashda xatolik yuz berdi.")


# --- STATISTIKA ---

@router.callback_query(F.data == "admin_stats", admin_filter)
async def show_admin_stats(callback: types.CallbackQuery, session: AsyncSession):
    """To'liq statistika funksiyasi"""
    users_count = await session.scalar(select(func.count(User.id)))
    movies_count = await session.scalar(select(func.count(Movie.id)))
    total_views = await session.scalar(select(func.sum(Movie.views))) or 0

    # Eng trenddagi kino
    pop = (await session.execute(select(Movie).order_by(Movie.views.desc()).limit(1))).scalar()
    pop_title = pop.title if pop else "Mavjud emas"

    stats_text = (
        "📊 <b>BOT STATISTIKASI</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Foydalanuvchilar: <b>{users_count:,} ta</b>\n"
        f"🎬 Jami kinolar: <b>{movies_count:,} ta</b>\n"
        f"👁 Umumiy ko'rishlar: <b>{total_views:,} ta</b>\n"
        f"🔥 Eng mashhur: <b>{pop_title}</b>\n\n"
        "🕒 <i>Ma'lumotlar real vaqtda yangilandi.</i>"
    )
    await callback.message.edit_text(stats_text, reply_markup=back_to_admin_markup())


# --- REKLAMA (UNIVERSAL BROADCAST) ---

@router.callback_query(F.data == "broadcast", admin_filter)
async def broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state("waiting_broadcast")
    await callback.message.edit_text(
        "📢 <b>Reklama yuborish bo'limi</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        "Xabaringizni yuboring. Bu bo'lishi mumkin:\n"
        "• Oddiy matn\n• Rasm yoki Video\n• Rasm/Video tagida matn\n\n"
        "<i>Barcha formatlar avtomatik nusxalanadi!</i>",
        reply_markup=cancel_action_markup()
    )


@router.message(F.state == "waiting_broadcast", admin_filter)
async def broadcast_send_engine(message: types.Message, session: AsyncSession, state: FSMContext):
    users = (await session.execute(select(User.id))).scalars().all()
    await state.clear()

    progress_msg = await message.answer(f"🚀 <b>Yuborish boshlandi...</b> (0/{len(users)})")

    count, blocked = 0, 0
    for idx, user_id in enumerate(users):
        try:
            # copy_to - har qanday turdagi xabarni (rasm, video, text) aslidek nusxalaydi
            await message.copy_to(chat_id=user_id)
            count += 1
        except Exception:
            blocked += 1

        # Har 20 ta xabarda progressni yangilash
        if idx % 20 == 0:
            try:
                await progress_msg.edit_text(f"🚀 <b>Yuborilmoqda:</b> ({idx}/{len(users)})")
            except:
                pass

        await asyncio.sleep(0.05)  # Telegram Flood limitdan qochish

    await progress_msg.delete()
    await message.answer(
        f"✅ <b>Reklama yakunlandi!</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Qabul qildi: <b>{count} ta</b>\n"
        f"🚫 Bloklagan: <b>{blocked} ta</b>",
        reply_markup=admin_main_markup()
    )