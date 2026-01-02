import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import config

router = Router()

# Admin filtri (Dinamik va xavfsiz)
admin_filter = F.from_user.id == config.ADMIN_ID


def admin_main_keyboard():
    """Admin panel uchun asosiy tugmalar to'plami"""
    builder = InlineKeyboardBuilder()

    # 1-qator: Kino va Reklama (Asosiy harakatlar)
    builder.row(
        types.InlineKeyboardButton(text="🎬 Kino qo'shish", callback_data="admin_add_movie"),
        types.InlineKeyboardButton(text="📢 Reklama (Xabar)", callback_data="admin_broadcast")
    )

    # 2-qator: Statistika
    builder.row(
        types.InlineKeyboardButton(text="📊 Bot statistikasi", callback_data="admin_stats")
    )

    # 3-qator: Botga o'tish (User mode)
    builder.row(
        types.InlineKeyboardButton(text="🏠 Asosiy menyuga o'tish", callback_data="back_to_main")
    )

    return builder.as_markup()


@router.message(Command("add"), admin_filter)
async def admin_panel_start(message: types.Message, state: FSMContext):
    """Admin panelga kirish nuqtasi"""
    await state.clear()

    welcome_text = (
        "👑 <b>ADMINISTRATOR BOSHQARUVI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Boshqaruv paneliga xush kelibsiz.\n"
        "Kerakli bo'limni tanlang: 👇\n\n"
        "<i>Eslatma: Bu bo'lim faqat adminlar uchun ko'rinadi.</i>"
    )

    await message.answer(
        text=welcome_text,
        reply_markup=admin_main_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_menu", admin_filter)
async def admin_menu_callback(callback: types.CallbackQuery, state: FSMContext):
    """Admin menyuga qaytish (callback orqali)"""
    await state.clear()

    text = (
        "👑 <b>ADMINISTRATOR BOSHQARUVI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Bo'limni tanlang:"
    )

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=admin_main_keyboard(),
            parse_mode="HTML"
        )
    except Exception:
        # Agar matn o'zgarmagan bo'lsa, xatolikni yashiramiz
        await callback.answer()