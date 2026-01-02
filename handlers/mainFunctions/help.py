import logging
from aiogram import Router, types, F, Bot
from config import config
from handlers.start import safe_edit_message
from keyboards.inline import back_keyboard

router = Router()


@router.callback_query(F.data == "help")
async def help_handler(callback: types.CallbackQuery, bot: Bot):
    """
    Botdan foydalanish yo'riqnomasi.
    """
    # 1. Bot ma'lumotlarini olish
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    # 2. Admin usernameni tayyorlash
    admin = config.ADMIN_USERNAME.replace("@", "")

    # 3. UI matni
    help_text = (
        "❓ <b>YORDAM VA YO'RIQNOMA</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎬 <b>Kino ko'rish:</b>\n"
        "└ Kanaldan olingan kino <b>kodini</b> yozib yuboring.\n\n"
        f"🔍 <b>Tezkor qidiruv:</b>\n"
        f"└ Nom bo'yicha qidirish uchun @{bot_username} deb yozing.\n\n"
        "🔄 <b>Muammo bormi?</b>\n"
        "└ Kanalga a'zoligingizni yoki kod to'g'riligini tekshiring.\n\n"
        "✍️ <b>Murojaat uchun:</b>\n"
        f"└ Admin: @{admin}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🍿 <i>Maroqli hordiq tilaymiz!</i>"
    )

    try:
        # MUHIM: safe_edit_message funksiyasi ichida ham parse_mode="HTML" bo'lishi shart!
        # Agar u funksiya sizga tegishli bo'lsa, uni ham tekshiring.
        await safe_edit_message(callback, help_text, back_keyboard())

        await callback.answer("📖 Yo'riqnoma")

    except Exception as e:
        logging.error(f"❌ Help handler error: {e}")
        # Agar tahrirlash o'xshamasa, yangi xabar yuboramiz (HTML rejimida)
        await callback.message.answer(
            text=help_text,
            reply_markup=back_keyboard(),
            parse_mode="HTML"  # <--- KAFOLATLANGAN YECHIM
        )
        await callback.answer()