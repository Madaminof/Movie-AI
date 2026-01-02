import time
import logging
from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import Movie, User
from handlers.start import safe_edit_message
from keyboards.inline import back_keyboard

router = Router()

@router.callback_query(F.data == "stats")
async def stats_handler(callback: types.CallbackQuery, session: AsyncSession):
    """
    Bot statistikasi: Foydalanuvchilar ishonchini oshirish uchun.
    """

    try:
        # 1. Ma'lumotlarni yig'ish
        # Jami foydalanuvchilar, kinolar va umumiy ko'rishlar
        u_count = await session.scalar(select(func.count(User.id))) or 0
        m_count = await session.scalar(select(func.count(Movie.id))) or 0
        v_count = await session.scalar(select(func.sum(Movie.views))) or 0

        # 2. Server tezligini o'lchash (Latency)
        start_time = time.time()
        await session.execute(select(1)) # Oddiy so'rov
        latency = round((time.time() - start_time) * 1000)

        # 3. UI matni (HTML formatda)
        stats_text = (
            "📊 <b>BOTNING JONLI KO'RSATKICHLARI</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 <b>Foydalanuvchilar:</b> <code>{u_count:,} nafar</code>\n"
            f"🎞 <b>Bazadagi kinolar:</b> <code>{m_count:,} ta</code>\n"
            f"👁 <b>Jami ko'rilgan:</b> <code>{v_count:,} marta</code>\n"
            f"⚡️ <b>Server tezligi:</b> <code>{latency} ms</code>\n\n"
            f"🟢 <b>Holat:</b> <code>Stabil (24/7)</code>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "✨ <i>Ma'lumotlar avtomatik yangilanadi.</i>"
        )

        # 4. UI ni yangilash
        # MUHIM: safe_edit_message ichida parse_mode="HTML" bo'lishi shart.
        # Agar hali ham <b> chiqayotgan bo'lsa, quyidagi zaxira usulini qo'llang:
        try:
            await safe_edit_message(callback, stats_text, back_keyboard())
        except Exception:
            # safe_edit_message da xato bo'lsa, to'g'ridan-to'g'ri edit qilish
            await callback.message.edit_text(
                text=stats_text,
                reply_markup=back_keyboard(),
                parse_mode="HTML"
            )

        await callback.answer("📈 Statistika yangilandi")

    except Exception as e:
        logging.error(f"Statistika xatosi: {e}")
        await callback.answer("⚠️ Ma'lumotlarni yuklashda xatolik.", show_alert=True)