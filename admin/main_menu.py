from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import config

router = Router()
admin_filter = F.from_user.id == config.ADMIN_ID

def admin_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎬 Add Movie", callback_data="admin_add_movie"))
    builder.row(types.InlineKeyboardButton(text="📢 Add Reklama", callback_data="admin_broadcast"))
    builder.row(types.InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"))
    builder.row(types.InlineKeyboardButton(text="🏠 Menu ga qaytish", callback_data="back_to_main"))
    return builder.as_markup()

@router.message(Command("add"), admin_filter)
async def admin_panel_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🛠 <b>ADMIN PANEL</b>\n━━━━━━━━━━━━━━━━━━━━\nBoshqaruv bo'limiga xush kelibsiz. Tanlang: 👇",
        reply_markup=admin_main_keyboard()
    )

@router.callback_query(F.data == "admin_menu", admin_filter)
async def admin_menu_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🛠 <b>ADMIN PANEL</b>", reply_markup=admin_main_keyboard())