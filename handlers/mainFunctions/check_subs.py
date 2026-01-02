import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import config

router = Router()


@router.callback_query(F.data == "check_subs")
async def check_user_sub(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    not_joined_channels = []

    # 1. Barcha majburiy kanallarni dinamik tekshirish
    for index, channel in enumerate(config.mandatory_channels, 1):
        try:
            member = await bot.get_chat_member(
                chat_id=channel['id'],
                user_id=user_id
            )
            # Foydalanuvchi chiqib ketgan yoki haydalgan bo'lsa
            if member.status in ["left", "kicked"]:
                not_joined_channels.append({
                    "index": index,
                    "url": channel['url']
                })
        except Exception as e:
            # 🚨 MUHIM: Agar bot kanalni topa olmasa ham tugmani ko'rsatish kerak!
            # Logda "Chat not found" chiqsa, demak ID yoki adminlikda muammo bor.
            logging.error(f"❌ Obuna tekshirishda xatolik ({channel['id']}): {e}")
            not_joined_channels.append({
                "index": index,
                "url": channel['url']
            })

    # 2. Agar hali ham a'zo bo'lmagan kanallar bo'lsa
    if not_joined_channels:
        builder = InlineKeyboardBuilder()
        for ch in not_joined_channels:
            builder.row(InlineKeyboardButton(
                text=f"📌 {ch['index']}-kanalga a'zo bo'lish",
                url=ch['url']
            ))
        builder.row(InlineKeyboardButton(text="✅ Qayta tekshirish", callback_data="check_subs"))

        # Foydalanuvchiga xabar berish
        await callback.answer(
            "⚠️ Ba'zi kanallarga obuna aniqlanmadi!",
            show_alert=True
        )

        text = (
            "⚠️ <b>OBUNA TO'LIQ EMAS!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Botdan foydalanish uchun quyidagi kanallarga a'zo bo'lishingiz shart:\n\n"
            "<i>Iltimos, obuna bo'lib so'ng pastdagi tugmani bosing:</i>"
        )

        try:
            # Faqat matn yoki markup o'zgargan bo'lsa tahrirlaymiz
            await callback.message.edit_text(
                text=text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
        except Exception:
            # Agar edit_text xato bersa (masalan, matn o'zgarmagan bo'lsa)
            pass
        return

    # 3. Agar hamma kanalga a'zo bo'lsa (Muvaffaqiyat)
    await callback.answer("✅ Tabriklaymiz! Barcha obunalar tasdiqlandi.", show_alert=True)

    try:
        await callback.message.delete()
    except Exception:
        pass

    # 4. Asosiy menyuni chiqarish
    from keyboards.inline import start_keyboard

    welcome_text = (
        "<b>XUSH KELIBSIZ!</b> 🎉\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Barcha cheklovlar olib tashlandi. Endi botdan to'liq foydalanishingiz mumkin.\n\n"
        "🎬 <b>Kino kodini yuboring yoki quyidagi menyudan foydalaning:</b>"
    )

    await callback.message.answer(
        text=welcome_text,
        reply_markup=start_keyboard(),
        parse_mode="HTML"
    )