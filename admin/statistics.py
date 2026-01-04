import logging
from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

# Modellaringiz nomi
from database.models import User, Movie

router = Router()


@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: types.CallbackQuery, session: AsyncSession):
    try:
        from database.requests import get_admin_dashboard_stats

        # 1. Ma'lumotlarni olish
        total_users, total_movies, total_views, top_movies = await get_admin_dashboard_stats(session)

        # 2. Matnni shakllantirish (Avvalgi UI dizayningiz)
        dashboard_text = (
            "🚀 <b>TIZIM BOSHQARUV PANELI</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👥 <b>FOYDALANUVCHILAR</b>\n"
            f"┣ 👤 Jami: <code>{total_users:,} nafar</code>\n"
            f"┗ Status: 🟢 <b>Faol va Stabil</b>\n\n"
            "🎬 <b>BOT KUTUBXONASI</b>\n"
            f"┣ 🎞 Kinolar: <code>{total_movies:,} ta</code>\n"
            f"┗ 👁 Ko'rishlar: <code>{total_views:,} marta</code>\n\n"
            "🏆 <b>TOP-10 TRENDDAGI FILMLAR</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
        )

        if top_movies:
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            for i, m in enumerate(top_movies):
                title = (m.title[:18] + "..") if len(m.title) > 18 else m.title
                dashboard_text += f"{medals[i]} <code>{m.code}</code> | {title} | 👁 <code>{m.views}</code>\n"

        dashboard_text += (
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"🛰 <b>Server:</b> <code>{datetime.now().strftime('%d.%m.%Y | %H:%M')}</code>"
        )

        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_stats"),
            types.InlineKeyboardButton(text="🔙 Admin Menyu", callback_data="admin_menu")
        )

        # 3. ASOSIY QISM: Xavfsiz tahrirlash
        try:
            await callback.message.edit_text(
                text=dashboard_text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
            await callback.answer("✅ Dashboard yangilandi")
        except TelegramBadRequest as e:
            if "message is not modified" in e.message:
                # Agar ma'lumot bir xil bo'lsa, xato chiqarmaymiz, shunchaki xabar beramiz
                await callback.answer("ℹ️ Ma'lumotlar o'zgarmagan", show_alert=False)
            else:
                # Boshqa turdagi BadRequest bo'lsa, uni log qilamiz
                raise e

    except Exception as e:
        logging.error(f"Admin stats error: {e}")
        await callback.answer("❌ Statistikani yuklashda xatolik!", show_alert=True)