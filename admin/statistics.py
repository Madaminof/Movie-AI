from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

# Modellaringiz nomi to'g'ri ekanligini tekshiring
from database.models import User, Movie

router = Router()


@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: types.CallbackQuery, session: AsyncSession):
    # 1. Umumiy hisob-kitoblar (Bular xavfsiz so'rovlar)
    try:
        total_users = await session.scalar(select(func.count(User.id))) or 0
        total_movies = await session.scalar(select(func.count(Movie.id))) or 0
        total_views = await session.scalar(select(func.sum(Movie.views))) or 0

        # 2. Eng trenddagi TOP 3 kino
        top_movies_query = await session.execute(
            select(Movie).order_by(Movie.views.desc()).limit(3)
        )
        top_movies = top_movies_query.scalars().all()

        # 3. UI uchun matn shakllantirish
        res = (
            "📈 <b>BOT MONITORING TIZIMI</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "👥 <b>FOYDALANUVCHILAR:</b>\n"
            f"┣ Jami: <code>{total_users:,}</code> ta\n"
            f"┗ Status: 🟢 Faol\n\n"

            "🎬 <b>KINO BAZASI:</b>\n"
            f"┣ Jami filmlar: <code>{total_movies:,}</code> ta\n"
            f"┗ Umumiy ko'rishlar: <code>{total_views:,}</code> marta\n\n"

            "🔥 <b>TOP TRENDDAGI FILMLAR:</b>\n"
        )

        if top_movies:
            medals = ["🥇", "🥈", "🥉"]
            for i, m in enumerate(top_movies):
                # m.title[:20] nom juda uzun bo'lsa kesib tashlaydi
                res += f"{medals[i]} <code>{m.code}</code> | {m.title[:20]}.. ({m.views:,})\n"
        else:
            res += "┗ <i>Hozircha ma'lumot yo'q</i>\n"

        res += (
            "\n━━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 <i>Yangilandi: {datetime.now().strftime('%H:%M:%S')}</i>"
        )

        # 4. Tugmalar
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_stats"))
        builder.row(types.InlineKeyboardButton(text="🔙 Admin Menyuga Qaytish", callback_data="admin_menu"))

        await callback.message.edit_text(res, reply_markup=builder.as_markup())

    except Exception as e:
        # Har qanday kutilmagan xatolikni tutish
        await callback.answer(f"Xatolik yuz berdi: {str(e)[:50]}", show_alert=True)