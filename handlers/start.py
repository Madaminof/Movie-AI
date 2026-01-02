import logging
from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest
from keyboards.inline import start_keyboard

router = Router()

# Botning vizual ko'rinishi
MAIN_ANIMATION = "https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJmZzZ6Znd6Znd6Znd6Znd6Znd6Znd6Znd6Znd6Znd6Znd6JmVwPXYxX2ludGVybmFsX2dpZl9ieV9iZiZjdD1n/l41lTfuxV3f3p9R8A/giphy.gif"


async def safe_edit_message(callback: types.CallbackQuery, text: str, reply_markup: types.InlineKeyboardMarkup):
    """
    Xabarlarni media turi va mazmunidan qat'iy nazar HTML formatda xatosiz tahrirlash.
    """
    try:
        # Xabarda media (video, rasm, gif) borligini tekshirish
        if callback.message.video or callback.message.photo or callback.message.animation:
            # Agar caption bir xil bo'lsa, Telegram xato beradi
            if callback.message.caption != text:
                await callback.message.edit_caption(
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"  # <--- BU YERDA HTML KAFOLATLANDI
                )
        else:
            # Oddiy matnli xabarlarni tahrirlash
            if callback.message.text != text:
                await callback.message.edit_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode="HTML"  # <--- BU YERDA HAM HTML KAFOLATLANDI
                )

    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            logging.debug("Xabar o'zgarishsiz qoldi.")
        else:
            logging.error(f"Tahrirlashda xatolik: {e}")
            # Xatolik bo'lsa, foydalanuvchi ekrani qotib qolmasligi uchun yangi xabar yuboramiz
            await callback.message.answer(text=text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        logging.error(f"General edit error: {e}")


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    """
    Bosh menyuga qaytish handler'i.
    """
    main_text = (
        "🏠 <b>ASOSIY MENYU</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎬 Kinolarni topish uchun ularning <b>kodini</b> yuboring.\n\n"
        "✨ <i>Quyidagi bo'limlardan birini tanlang:</i>"
    )

    # Xabarni tahrirlash (SafeEdit endi HTMLni tushunadi)
    await safe_edit_message(callback, main_text, start_keyboard())

    # Tugma bosilgandagi animatsiyani yopish
    await callback.answer("🏠 Asosiy menyu")