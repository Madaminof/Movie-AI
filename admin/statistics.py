import logging
from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

# Modellaringiz nomi
from database.models import User, Movie

router = Router()

@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: types.CallbackQuery, session: AsyncSession):
    """Admin panel uchun batafsil statistika Dashboardi"""
    try:
        # 1. Ma'lumotlarni bazadan olish
        total_users = await session.scalar(select(func.count(User.id))) or 0
        total_movies = await session.scalar(select(func.count(Movie.id))) or 0
        total_views = await session.scalar(select(func.sum(Movie.views))) or 0

        # Eng ko'p ko'rilgan TOP 5 kino (3 tadan 5 taga oshirdik, ko'rinish yaxshiroq bo'ladi)
        top_movies_query = await session.execute(
            select(Movie).order_by(Movie.views.desc()).limit(5)
        )
        top_movies = top_movies_query.scalars().all()

        # 2. UI Dizayn (Dashboard formatida)
        dashboard_text = (
            "📊 <b>ADMINISTRATOR DASHBOARD</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "👥 <b>FOYDALANUVCHILAR</b>\n"
            f"┣ Jami a'zolar: <code>{total_users:,}</code>\n"
            f"┗ Bot holati: 🟢 <b>Faol ishlamoqda</b>\n\n"

            "🎬 <b>KINO ARXIVI</b>\n"
            f"┣ Filmlar soni: <code>{total_movies:,}</code> ta\n"
            f"┗ Jami ko'rishlar: <code>{total_views:,}</code>\n\n"

            "🔥 <b>TOP TRENDDAGI FILMLAR</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
        )

        if top_movies:
            medals = ["🥇", "🥈", "🥉", "🔹", "🔹"]
            for i, m in enumerate(top_movies):
                movie_title = m.title[:18] + ".." if len(m.title) > 18 else m.title
                dashboard_text += (
                    f"{medals[i]} <code>{m.code}</code> | {movie_title}\n"
                    f"┗ 👁 <i>{m.views:,} marta ko'rilgan</i>\n"
                )
        else:
            dashboard_text += "<i>⚠️ Ma'lumotlar mavjud emas</i>\n"

        dashboard_text += (
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>Sana:</b> <code>{datetime.now().strftime('%d.%m.%Y')}</code>\n"
            f"🕒 <b>Vaqt:</b> <code>{datetime.now().strftime('%H:%M:%S')}</code>"
        )

        # 3. Tugmalar (Keyboard)
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_stats"))
        builder.row(types.InlineKeyboardButton(text="🔙 Admin Menyuga Qaytish", callback_data="admin_menu"))

        # 4. Tahrirlash (Xavfsiz usulda)
        try:
            await callback.message.edit_text(
                text=dashboard_text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"  # <--- HTML KAFOLATLANDI
            )
        except Exception:
            # Agar tahrirlashda xato bo'lsa (matn bir xil bo'lsa), shunchaki xabar yuboramiz
            await callback.answer("Statistika yangilandi 🔄")

    except Exception as e:
        logging.error(f"Admin statistika xatosi: {e}")
        await callback.answer("❌ Ma'lumotlarni yuklashda xatolik!", show_alert=True)