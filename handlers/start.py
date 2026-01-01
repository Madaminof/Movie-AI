import logging
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database.crud import get_or_create_user
from database.models import Movie, User
from keyboards.inline import start_keyboard, back_keyboard

router = Router()

# Botning yuqori sifatli vizual ko'rinishi uchun asosiy animatsiya
MAIN_ANIMATION = "https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJmZzZ6Znd6Znd6Znd6Znd6Znd6Znd6Znd6Znd6Znd6Znd6JmVwPXYxX2ludGVybmFsX2dpZl9ieV9iZiZjdD1n/l41lTfuxV3f3p9R8A/giphy.gif"


async def safe_edit_message(callback: types.CallbackQuery, text: str, reply_markup: types.InlineKeyboardMarkup):
    """Xabarlarni caption yoki text formatida xatosiz tahrirlash uchun yordamchi funksiya"""
    try:
        if callback.message.caption is not None:
            await callback.message.edit_caption(caption=text, reply_markup=reply_markup)
        else:
            await callback.message.edit_text(text=text, reply_markup=reply_markup)
    except Exception as e:
        logging.debug(f"Edit skip: {e}")


@router.message(CommandStart())
async def cmd_start(message: types.Message, session: AsyncSession):
    """
    Botning asosiy kirish qismi.
    Foydalanuvchini ro'yxatga oladi va jozibador UI taqdim etadi.
    """
    # 1. Foydalanuvchini bazaga qo'shish yoki olish
    await get_or_create_user(session, message.from_user.id, message.from_user.full_name)

    # 2. Foydalanuvchiga botning asl qiymatini ko'rsatuvchi matn
    welcome_text = (
        f"🎬 <b>AI MOVIE VISION — SIZNING KINOXONANGIZ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 Assalomu alaykum, <b>{message.from_user.first_name}</b>!\n\n"
        f"Botimiz orqali sevimli filmlaringizni bir necha soniyada <b>reklamalarsiz</b> va <b>to'liq sifatda</b> topishingiz mumkin.\n\n"
        f"🎞 <b>Bot imkoniyatlari:</b>\n"
        f"├ 🍿 100,000+ dan ortiq filmlar va seriallar\n"
        f"├ 🖥 Eng so'nggi premyeralar (Full HD)\n"
        f"└ ⚡️ Avtomatik va tezkor yuklab olish\n\n"
        f"📍 <b>Boshlash uchun:</b>\n"
        f"Kanalimizdan olingan kino kodini raqamlarda yuboring."
    )

    try:
        await message.answer_animation(
            animation=MAIN_ANIMATION,
            caption=welcome_text,
            reply_markup=start_keyboard()
        )
    except Exception:
        # Agar animatsiya yuklanmasa, oddiy matn yuboriladi
        await message.answer(welcome_text, reply_markup=start_keyboard())


from aiogram.utils.keyboard import InlineKeyboardBuilder


@router.callback_query(F.data == "referral_menu")
async def referral_handler(callback: types.CallbackQuery, session: AsyncSession):
    """Referal menyusi - Progress bar bilan"""
    result = await session.execute(select(User).where(User.user_id == callback.from_user.id))
    user = result.scalar_one_or_none()

    count = user.referral_count if user else 0
    bot_info = await callback.bot.get_me()
    # Referal link yaratish
    link = f"https://t.me/{bot_info.username}?start={callback.from_user.id}"

    # Progress vizualizatsiyasi
    progress = "🔹" * count + "▫️" * (5 - count) if count < 5 else "✅ VIP FAOL"

    text = (
        "💎 <b>DOIMIY VIP IMKONIYAT</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "5 ta do'stingizni taklif qiling va botdan <b>reklamasiz hamda "
        "majburiy obunalarsiz</b> foydalaning!\n\n"
        f"👤 Do'stlaringiz: <b>{count}/5</b>\n"
        f"📊 Progress: <code>{progress}</code>\n\n"
        f"🔗 Havolangiz: <code>{link}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Havolani nusxalash uchun ustiga bosing.</i>"
    )

    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📢 Do'stlarga yuborish",
                                    switch_inline_query=f"\nUshbu bot orqali eng sara kinolarni topishingiz mumkin!")],
        [types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_main")]
    ])

    await safe_edit_message(callback, text, markup)



@router.callback_query(F.data == "random_movie")
async def random_movie_handler(callback: types.CallbackQuery, session: AsyncSession):
    """Bazadan tasodifiy kinoni chiqarib beradi va vizual boyitadi"""

    # 1. Tasodifiy bitta kinoni olish
    # SQLite da RANDOM(), PostgreSQL da esa func.random() ishlaydi
    stmt = select(Movie).order_by(func.random()).limit(1)
    result = await session.execute(stmt)
    movie = result.scalar_one_or_none()

    if movie:
        text = (
            "🎲 <b>TASODIFIY TANLOV</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎬 <b>Nomi:</b> <code>{movie.title.upper()}</code>\n"
            f"🆔 <b>Kino kodi:</b> <code>{movie.code}</code>\n"
            f"👁 <b>Ko'rishlar:</b> <code>{movie.views:,}</code>\n\n"
            "🍿 <i>Nima ko'rishni bilmay turgan bo'lsangiz, ushbu tanlov sizga yoqadi degan umiddamiz!</i>"
        )

        # Tugmalarni yasash
        builder = InlineKeyboardBuilder()
        # To'g'ridan-to'g'ri kinoni yuborish uchun callback (movie_search handleringizga moslab)
        builder.row(types.InlineKeyboardButton(
            text="🍿 Kinoni ko'rish",
            callback_data=f"movie_{movie.code}")
        )
        # Yana bitta random qilish imkoniyati
        builder.row(types.InlineKeyboardButton(
            text="🔄 Boshqa tanlov",
            callback_data="random_movie")
        )
        builder.row(types.InlineKeyboardButton(
            text="🔙 Orqaga",
            callback_data="back_to_main")
        )

        await safe_edit_message(callback, text, builder.as_markup())
        await callback.answer("🎲 Siz uchun yangi film topildi!")

    else:
        await callback.answer("😔 Hozircha bazada kinolar yo'q.", show_alert=True)


@router.callback_query(F.data == "check_subs")
async def check_subs_handler(callback: types.CallbackQuery):
    """
    Middleware'dan o'tgan (obunasi tasdiqlangan) foydalanuvchilar uchun.
    """
    await callback.answer("✅ Obuna tasdiqlandi. Xush kelibsiz!", show_alert=True)
    await callback.message.delete()

    # Qayta start xabari
    welcome_text = (
        "🏠 <b>ASOSIY MENYU</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Barcha cheklovlar olib tashlandi. Kino kodini yuboring va tomoshadan zavqlaning! 👇"
    )
    try:
        await callback.message.answer_animation(
            animation=MAIN_ANIMATION,
            caption=welcome_text,
            reply_markup=start_keyboard()
        )
    except:
        await callback.message.answer(welcome_text, reply_markup=start_keyboard())


@router.callback_query(F.data == "trending")
async def trending_movies(callback: types.CallbackQuery, session: AsyncSession):
    """Eng ko'p ko'rilgan (Trenddagi) kinolar"""
    result = await session.execute(select(Movie).order_by(Movie.views.desc()).limit(5))
    movies = result.scalars().all()

    text = "🔥 <b>HAFTALIK TRENDDAGI FILMLAR</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"

    if not movies:
        text += "<i>Hozircha ma'lumotlar mavjud emas...</i>"
    else:
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, m in enumerate(movies):
            text += f"{medals[i]} <b>{m.title.upper()}</b>\n   └ 🆔 Kod: <code>{m.code}</code> | 👁 {m.views:,} ta ko'rish\n\n"

    text += "━━━━━━━━━━━━━━━━━━━━\n🎬 <i>Ko'rish uchun kodni botga yuboring!</i>"
    await safe_edit_message(callback, text, back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "stats")
async def stats_handler(callback: types.CallbackQuery, session: AsyncSession):
    """Bot statistikasi - Ishonch oshirish uchun"""
    u_count = await session.scalar(select(func.count(User.id)))
    m_count = await session.scalar(select(func.count(Movie.id)))

    stats_text = (
        "📊 <b>BOT KO'RSATKICHLARI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 <b>Foydalanuvchilar:</b> <code>{u_count:,}</code>\n"
        f"🎞 <b>Jami filmlar:</b> <code>{m_count:,}</code>\n"
        f"⚡️ <b>Holat:</b> <code>Onlayn (24/7)</code>\n\n"
        "Barcha ma'lumotlar real vaqt rejimida yangilanadi."
    )
    await safe_edit_message(callback, stats_text, back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "help")
async def help_handler(callback: types.CallbackQuery):
    """Botdan foydalanish yo'riqnomasi"""
    help_text = (
        "📖 <b>BOTDAN FOYDALANISH</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "1. Rasmiy kanalimizdan o'zingizga yoqqan kinoni tanlang.\n"
        "2. Kino ostida ko'rsatilgan <b>raqamli kodni</b> nusxalang.\n"
        "3. Ushbu kodni botga yuboring va film faylini oling.\n\n"
        "⚠️ <i>Agar kod ishlamasa, u bazadan o'chirilgan bo'lishi mumkin.</i>"
    )
    await safe_edit_message(callback, help_text, back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    """Bosh menyuga qaytish"""
    text = (
        "🏠 <b>ASOSIY MENYU</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Kino kodini yuboring yoki quyidagi bo'limlardan foydalaning:"
    )
    await safe_edit_message(callback, text, start_keyboard())
    await callback.answer()