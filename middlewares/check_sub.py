import logging
from typing import Any, Awaitable, Callable, Dict, Union, List

from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import config


class CheckSubMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
            event: Union[Message, CallbackQuery],
            data: Dict[str, Any]
    ) -> Any:
        user = event.from_user

        # 1. Admin bo'lsa tekshiruvdan ozod qilish
        if not user or user.id == config.ADMIN_ID:
            return await handler(event, data)

        bot: Bot = data["bot"]
        not_joined_channels = []

        # 2. Dinamik tekshirish
        for index, channel in enumerate(config.mandatory_channels, 1):
            try:
                member = await bot.get_chat_member(
                    chat_id=channel['id'],
                    user_id=user.id
                )
                # Faqat a'zo bo'lmaganlarni yig'amiz
                if member.status in ["left", "kicked"]:
                    not_joined_channels.append({
                        "index": index,
                        "url": channel['url']
                    })
            except Exception as e:
                # 🚨 MUHIM: Bot kanalni topa olmasa ham tugmani chiqarish kerak!
                # Logga xatoni yozamiz, lekin foydalanuvchiga tugmani ko'rsatamiz
                logging.error(f"❌ Kanalni tekshirish imkonsiz ({channel['id']}): {e}")
                not_joined_channels.append({
                    "index": index,
                    "url": channel['url']
                })

        # 3. Agar obuna bo'lmagan kanallar bo'lsa
        if not_joined_channels:
            return await self._send_alert(event, not_joined_channels)

        # 4. Hammasi joyida bo'lsa handlerga o'tish
        return await handler(event, data)

    async def _send_alert(self, event: Union[Message, CallbackQuery], not_joined: List[Dict]):
        """Dinamik va chiroyli tugmalar bilan ogohlantirish"""

        text = (
            "⚠️ <b>BOTDAN FOYDALANISH UCHUN QOIDALAR</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Botdan to'liq foydalanish uchun quyidagi kanallarga a'zo bo'lishingiz shart:\n\n"
            "<i>Obuna bo'lgach '✅ Tekshirish' tugmasini bosing.</i>"
        )

        builder = InlineKeyboardBuilder()
        for ch in not_joined:
            builder.row(InlineKeyboardButton(
                text=f"📌 {ch['index']}-kanalga obuna bo'lish",
                url=ch['url']
            ))

        builder.row(InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subs"))

        # HTML formatda yuborish
        if isinstance(event, Message):
            await event.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        elif isinstance(event, CallbackQuery):
            # Xabar matni bir xil bo'lsa xato bermasligi uchun tekshiruv
            try:
                if event.message.text != text:
                    await event.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
            except:
                # Agar edit qilishda xato bo'lsa (masalan rasm ustida bo'lsa), answer_video da bo'lgani kabi
                await event.message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

            await event.answer("⚠️ Obuna to'liq emas!", show_alert=True)
        return