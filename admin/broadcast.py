import asyncio
import uuid
import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.exceptions import (
    TelegramRetryAfter,
    TelegramForbiddenError,
    TelegramBadRequest
)

from database.models import User, BroadcastLog

router = Router()


class BroadcastState(StatesGroup):
    waiting_for_message = State()


# 1. Reklama yuborishni boshlash
@router.callback_query(F.data == "admin_broadcast")
async def broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastState.waiting_for_message)
    await callback.message.edit_text(
        "📢 <b>PROFESSIONAL BROADCAST SYSTEM</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Istalgan xabarni yuboring (Rasm, Video, Matn, Fayl).\n\n"
        "✅ <b>Imkoniyatlar:</b>\n"
        "• Avtomatik filtr (faqat faol foydalanuvchilar)\n"
        "• Reklamani barchadan o'chirish (Purge)\n"
        "• Foydalanuvchi statistikasini saqlash\n"
        "━━━━━━━━━━━━━━━━━━━━",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_menu")]
        ])
    )


# 2. Reklamani tarqatish dvigateli
@router.message(BroadcastState.waiting_for_message)
async def broadcast_engine(message: types.Message, session: AsyncSession, state: FSMContext):
    # Faqat faol foydalanuvchilarni olish (is_active=True)
    # Agar modelda hali is_active bo'lmasa, .where() qismini olib tashlang
    query = select(User.user_id).where(User.is_active == True)
    result = await session.execute(query)
    users = result.scalars().all()

    if not users:
        await state.clear()
        return await message.answer("⚠️ Reklama yuborish uchun faol foydalanuvchilar topilmadi!")

    await state.clear()
    campaign_id = str(uuid.uuid4())[:8]
    status_msg = await message.answer(f"⏳ Tayyorlanmoqda... (Jami: {len(users)} ta)")

    sent, blocked, deactivated, errors = 0, 0, 0, 0

    for user_id in users:
        try:
            # Xabarni nusxalash (Eng xavfsiz metod)
            sent_msg = await message.copy_to(chat_id=user_id)

            # Har bir xabarni logga yozish (O'chirish tugmasi ishlashi uchun)
            session.add(BroadcastLog(
                broadcast_id=campaign_id,
                user_id=user_id,
                message_id=sent_msg.message_id
            ))
            sent += 1

            # Har 25 ta xabarda hisobotni yangilash
            if sent % 25 == 0:
                try:
                    await status_msg.edit_text(
                        f"🚀 <b>Yuborilmoqda:</b> <code>{sent}/{len(users)}</code>\n"
                        f"🚫 <b>Bloklangan:</b> <code>{blocked}</code>"
                    )
                except:
                    pass

            await asyncio.sleep(0.05)  # Telegram Flood Limitdan himoya

        except TelegramForbiddenError:
            # Foydalanuvchi botni bloklagan - Statusni o'zgartiramiz
            blocked += 1
            await session.execute(
                update(User).where(User.user_id == user_id).values(is_active=False)
            )
        except TelegramBadRequest as e:
            if "chat not found" in str(e).lower():
                # Akkaunt o'chib ketgan - Statusni o'zgartiramiz
                deactivated += 1
                await session.execute(
                    update(User).where(User.user_id == user_id).values(is_active=False)
                )
            else:
                errors += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            # Qayta urinish
            sent_msg = await message.copy_to(chat_id=user_id)
            session.add(BroadcastLog(broadcast_id=campaign_id, user_id=user_id, message_id=sent_msg.message_id))
            sent += 1
        except Exception as e:
            logging.error(f"Xato ID {user_id}: {e}")
            errors += 1

    await session.commit()
    await status_msg.delete()

    # Natija tugmalari
    res_markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🗑 Reklamani barchadan o'chirish", callback_data=f"purge_{campaign_id}")],
        [types.InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_menu")]
    ])

    await message.answer(
        f"🏁 <b>HISOBOT:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Yetkazildi: <b>{sent}</b>\n"
        f"🚫 Bloklaganlar: <b>{blocked}</b>\n"
        f"🗑 Akkaunti o'chganlar: <b>{deactivated}</b>\n"
        f"⚠️ Kutilmagan xatolar: <b>{errors}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{campaign_id}</code>",
        reply_markup=res_markup
    )


# 3. Reklamani o'chirish (Purge system)
@router.callback_query(F.data.startswith("purge_"))
async def purge_broadcast(callback: types.CallbackQuery, session: AsyncSession):
    c_id = callback.data.split("_")[1]

    # Bazadan barcha xabar IDlarini olish
    res = await session.execute(select(BroadcastLog).where(BroadcastLog.broadcast_id == c_id))
    logs = res.scalars().all()

    if not logs:
        return await callback.answer("❌ O'chirish uchun ma'lumot topilmadi.", show_alert=True)

    await callback.message.edit_text(f"🗑 Reklama o'chirilmoqda (0/{len(logs)})...")

    deleted = 0
    for log in logs:
        try:
            await callback.bot.delete_message(chat_id=log.user_id, message_id=log.message_id)
            deleted += 1
        except:
            pass

        if deleted % 20 == 0:
            try:
                await callback.message.edit_text(f"🗑 O'chirilmoqda: {deleted}/{len(logs)}")
            except:
                pass
        await asyncio.sleep(0.04)

    # Loglarni bazadan butunlay tozalash
    await session.execute(delete(BroadcastLog).where(BroadcastLog.broadcast_id == c_id))
    await session.commit()

    await callback.message.answer(f"✅ Reklama {deleted} ta chatdan muvaffaqiyatli o'chirildi.")
    await callback.answer()