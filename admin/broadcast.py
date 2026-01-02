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
from config import config

router = Router()


class BroadcastState(StatesGroup):
    waiting_for_message = State()


def get_cancel_btn():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_menu")]
    ])


# 1. Reklama yuborishni boshlash
@router.callback_query(F.data == "admin_broadcast", F.from_user.id == config.ADMIN_ID)
async def broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastState.waiting_for_message)
    text = (
        "📢 <b>REKLAMA TARQATISH TIZIMI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Admin, barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring.\n\n"
        "<b>Qo'llab-quvvatlanadi:</b>\n"
        "• 📝 Matn va Linklar\n"
        "• 🖼 Rasm va Videolar\n"
        "• 📁 Fayl va Hujjatlar\n"
        "• 🎤 Ovozli xabarlar\n\n"
        "<i>Eslatma: Xabar barcha faol a'zolarga yetkaziladi.</i>"
    )
    await callback.message.edit_text(text, reply_markup=get_cancel_btn(), parse_mode="HTML")


# 2. Reklamani tarqatish dvigateli
@router.message(BroadcastState.waiting_for_message, F.from_user.id == config.ADMIN_ID)
async def broadcast_engine(message: types.Message, session: AsyncSession, state: FSMContext):
    # Faqat faol a'zolarni olish
    query = select(User.user_id).where(User.is_active == True)
    result = await session.execute(query)
    users = result.scalars().all()

    if not users:
        await state.clear()
        return await message.answer("⚠️ Reklama yuborish uchun faol foydalanuvchilar topilmadi!")

    await state.clear()
    campaign_id = str(uuid.uuid4())[:8]
    status_msg = await message.answer(f"⏳ <b>Jarayon boshlandi...</b> (0/{len(users)})", parse_mode="HTML")

    sent, blocked, deactivated, errors = 0, 0, 0, 0

    for user_id in users:
        try:
            # Xabarni nusxalash
            sent_msg = await message.copy_to(chat_id=user_id)

            # Logga yozish
            session.add(BroadcastLog(
                broadcast_id=campaign_id,
                user_id=user_id,
                message_id=sent_msg.message_id
            ))
            sent += 1

            # UI yangilash (Flood limitga tushmaslik uchun har 30 ta xabarda)
            if sent % 30 == 0:
                try:
                    await status_msg.edit_text(
                        f"🚀 <b>REKLAMA YUBORILMOQDA...</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"✅ Yetkazildi: <code>{sent}</code>\n"
                        f"🚫 To'siqlar: <code>{blocked + deactivated}</code>\n"
                        f"📊 Progress: <code>{int((sent / len(users)) * 100)}%</code>",
                        parse_mode="HTML"
                    )
                except:
                    pass

            await asyncio.sleep(0.05)  # 20 msg/sec

        except TelegramForbiddenError:
            blocked += 1
            await session.execute(update(User).where(User.user_id == user_id).values(is_active=False))
        except TelegramBadRequest as e:
            if "chat not found" in str(e).lower():
                deactivated += 1
                await session.execute(update(User).where(User.user_id == user_id).values(is_active=False))
            else:
                errors += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            # Qayta urinish (Retry)
            try:
                sent_msg = await message.copy_to(chat_id=user_id)
                session.add(BroadcastLog(broadcast_id=campaign_id, user_id=user_id, message_id=sent_msg.message_id))
                sent += 1
            except:
                errors += 1
        except Exception as e:
            logging.error(f"Broadcasting error for {user_id}: {e}")
            errors += 1

    await session.commit()

    # Yakuniy hisobot
    final_text = (
        "🏁 <b>TARQATISH YAKUNLANDI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Muvaffaqiyatli: <code>{sent}</code>\n"
        f"🚫 Bloklaganlar: <code>{blocked}</code>\n"
        f"🗑 O'chgan hisoblar: <code>{deactivated}</code>\n"
        f"⚠️ Xatoliklar: <code>{errors}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{campaign_id}</code>"
    )

    res_markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🗑 Xabarni o'chirish (Purge)", callback_data=f"purge_{campaign_id}")],
        [types.InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_menu")]
    ])

    await status_msg.delete()
    await message.answer(final_text, reply_markup=res_markup, parse_mode="HTML")


# 3. Reklamani o'chirish (Purge system)
@router.callback_query(F.data.startswith("purge_"), F.from_user.id == config.ADMIN_ID)
async def purge_broadcast(callback: types.CallbackQuery, session: AsyncSession):
    c_id = callback.data.split("_")[1]

    res = await session.execute(select(BroadcastLog).where(BroadcastLog.broadcast_id == c_id))
    logs = res.scalars().all()

    if not logs:
        return await callback.answer("❌ Ma'lumot topilmadi.", show_alert=True)

    status_msg = await callback.message.answer(f"🗑 <b>O'chirish jarayoni boshlandi...</b>", parse_mode="HTML")
    deleted = 0

    for log in logs:
        try:
            await callback.bot.delete_message(chat_id=log.user_id, message_id=log.message_id)
            deleted += 1
        except:
            pass

        if deleted % 25 == 0:
            try:
                await status_msg.edit_text(f"🗑 <b>O'chirilmoqda:</b> <code>{deleted}/{len(logs)}</code>",
                                           parse_mode="HTML")
            except:
                pass
        await asyncio.sleep(0.05)

    await session.execute(delete(BroadcastLog).where(BroadcastLog.broadcast_id == c_id))
    await session.commit()

    await status_msg.edit_text(f"✅ <b>Tayyor!</b> Reklama {deleted} ta foydalanuvchidan o'chirildi.", parse_mode="HTML")
    await callback.answer()