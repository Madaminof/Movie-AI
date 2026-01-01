import logging
import time
from typing import Callable, Dict, Any, Awaitable, Union
from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery, TelegramObject
from config import config
from keyboards.inline import subscription_keyboard


class CheckSubMiddleware(BaseMiddleware):
    def __init__(self):
        self.cache = {}
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:

        real_event = event.message or event.callback_query
        if not real_event or not real_event.from_user:
            return await handler(event, data)

        user_id = real_event.from_user.id
        bot: Bot = data['bot']

        # 1. Admin uchun istisno
        if user_id == config.ADMIN_ID:
            return await handler(event, data)

        # 2. Muhim: "check_subs" bosilganda ham tekshiruvdan o'tishi kerak.
        # Shuning uchun bu yerdagi eski "return await handler" qatorini olib tashladik.

        # 3. Keshni tekshirish (faqat oddiy xabarlar uchun, Tasdiqlash tugmasi uchun emas)
        current_time = time.time()
        is_check_button = isinstance(real_event, CallbackQuery) and real_event.data == "check_subs"

        if not is_check_button:
            if user_id in self.cache and current_time - self.cache[user_id] < 60:
                return await handler(event, data)

        # 4. Kanal identifikatori
        channel_id = config.CHANNEL_URL.split('/')[-1]
        channel_id = f"@{channel_id}" if not channel_id.startswith('@') else channel_id

        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)

            if member.status in ["left", "kicked"]:
                # Foydalanuvchi a'zo bo'lmagan bo'lsa
                if is_check_button:
                    await real_event.answer("❌ Siz hali a'zo bo'lmadingiz!", show_alert=True)

                return await self._send_subscription_alert(real_event, [channel_id])

            # Obuna bo'lgan bo'lsa keshga saqlaymiz
            self.cache[user_id] = current_time
            return await handler(event, data)

        except Exception as e:
            logging.error(f"⚠️ Subscription Check Error: {e}")
            return await handler(event, data)

    async def _send_subscription_alert(self, event: Union[Message, CallbackQuery], channels: list):
        alert_text = (
            "🔒 <b>BOTDAN FOYDALANISH CHEKLANGAN</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Botimizning <b>Premium</b> funksiyalaridan foydalanish uchun rasmiy kanalimizga a'zo bo'lishingiz kerak.\n\n"
            "📢 <b>Kanalimiz:</b> @android_notes_developer\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "✨ <i>Obuna bo'lgach, 'Tasdiqlash' tugmasini bosing:</i>"
        )
        markup = subscription_keyboard(channels)

        if isinstance(event, Message):
            return await event.answer(alert_text, reply_markup=markup)
        elif isinstance(event, CallbackQuery):
            # Xabarni qayta tahrirlash (faqat kerak bo'lsa)
            try:
                if event.message.text != alert_text:
                    await event.message.edit_text(text=alert_text, reply_markup=markup)
            except Exception:
                pass