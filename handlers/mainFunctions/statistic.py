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
    try:
        from database.requests import get_full_stats
        u_count, m_count, v_count = await get_full_stats(session)

        start_time = time.time()
        await session.execute(select(1))
        latency = round((time.time() - start_time) * 1000)

        stats_text = (
            "📊 <b>BOTNING JONLI KO'RSATKICHLARI</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 <b>Foydalanuvchilar:</b> <code>{u_count:,} ta</code>\n"
            f"🎞 <b>Bazadagi kinolar:</b> <code>{m_count:,} ta</code>\n"
            f"👁 <b>Jami Ko'rishlar:</b> <code>{v_count:,} marta</code>\n"
            f"⚡️ <b>Server tezligi:</b> <code>{latency} ms</code>\n\n"
            f"🟢 <b>Holat:</b> <code>Stabil (24/7)</code>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "✨ <i>Ma'lumotlar real vaqtda yangilanadi.</i>"
        )

        await safe_edit_message(callback, stats_text, back_keyboard())
        await callback.answer("📈 Statistika yangilandi")

    except Exception as e:
        logging.error(f"Statistika xatosi: {e}")
        await callback.answer("⚠️ Ma'lumotlarni yuklashda xatolik.", show_alert=True)