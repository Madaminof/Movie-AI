from select import select

from aiogram import types, Router
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database.models import Movie, User
from database.crud import get_or_create_user
from handlers.start import MAIN_ANIMATION
from keyboards.inline import start_keyboard


router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, session: AsyncSession):
    """
    Botning asosiy kirish qismi.
    Foydalanuvchini ro'yxatga oladi va jozibador UI taqdim etadi.
    """
    # 1. Foydalanuvchini bazaga qo'shish yoki olish
    await get_or_create_user(session, message.from_user.id, message.from_user.full_name)

    m_count = await session.scalar(select(func.count(Movie.id))) or 0

    # 2. Foydalanuvchiga botning asl qiymatini ko'rsatuvchi matn
    welcome_text = (
        f"🎬 <b>AI MOVIE VISION — SIZNING KINOXONANGIZ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 Assalomu alaykum, <b>{message.from_user.first_name}</b>!\n\n"
        f"Botimiz orqali sevimli filmlaringizni bir necha soniyada <b>reklamalarsiz</b> va <b>to'liq sifatda</b> topishingiz mumkin.\n\n"
        f"🎞 <b>Bot imkoniyatlari:</b>\n"
        f"├ 🍿 {m_count} + dan ortiq filmlar va seriallar\n"
        f"├ 🖥 Eng so'nggi premyeralar (Full HD)\n"
        f"└ ⚡️ Avtomatik va tezkor yuklab olish\n\n"
        f"📍 <b>Boshlash uchun:</b>\n"
        f"Kanalimizdan olingan kino kodini raqamlarda yuboring."
    )

    try:
        await message.answer_animation(
            animation=MAIN_ANIMATION,
            caption=welcome_text,
            reply_markup=start_keyboard(),
            parse_mode="HTML"
        )
    except Exception:
        # Agar animatsiya yuklanmasa, oddiy matn yuboriladi
        await message.answer(welcome_text, reply_markup=start_keyboard(),parse_mode="HTML")

