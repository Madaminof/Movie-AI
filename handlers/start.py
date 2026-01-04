import logging
from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest
from keyboards.inline import start_keyboard

router = Router()

MAIN_ANIMATION = "https://cdn.dribbble.com/userupload/42422856/file/original-ce1d59462444785a4ab8e557e4876817.gif"

async def safe_edit_message(callback: types.CallbackQuery, text: str, reply_markup: types.InlineKeyboardMarkup):

    try:
        if callback.message.photo or callback.message.video or callback.message.animation:
            await callback.message.edit_caption(
                caption=text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )

    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            logging.debug("Xabar o'zgarishsiz qoldi.")
        elif "message can't be edited" in str(e) or "message to edit not found" in str(e):
            await callback.message.delete()
            await callback.message.answer_animation(
                animation=MAIN_ANIMATION,
                caption=text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        else:
            logging.error(f"Tahrirlashda xatolik: {e}")

    except Exception as e:
        logging.error(f"Umumiy xatolik: {e}")

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):

    main_text = (
        "🎬 <b>MOVIE HD — SHAXSIY KINOTEATR</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🍿 <b>Kino kodini yuboring</b> va tomoshadan bahra oling!\n\n"
        "🎬 Kinolarni topish uchun ularning <b>kodini</b> yuboring.\n"
        "✨ <i>Quyidagi bo'limlardan birini tanlang:</i>\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    if not callback.message.animation:
        try:
            await callback.message.delete()
        except:
            pass
        await callback.message.answer_animation(
            animation=MAIN_ANIMATION,
            caption=main_text,
            reply_markup=start_keyboard(),
            parse_mode="HTML"
        )
    else:
        await safe_edit_message(callback, main_text, start_keyboard())

    await callback.answer("🏠 Asosiy menyu")