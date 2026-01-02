from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import config


def start_keyboard() -> InlineKeyboardMarkup:
    """Asosiy menyu: Premium dizayn va vizual tartib"""
    builder = InlineKeyboardBuilder()

    # 1-qator: Asosiy funksiyalar (Kattaroq va yonma-yon)
    builder.row(
        InlineKeyboardButton(text="🎲 Random Film", callback_data="random_movie"),
        InlineKeyboardButton(text="🔥 Trend", callback_data="trending")
    )

    # 2-qator: Ma'lumotlar
    builder.row(
        InlineKeyboardButton(text="📊 Statistika", callback_data="stats"),
        InlineKeyboardButton(text="📖 Yo'riqnoma", callback_data="help")
    )

    # 3-qator: Tashqi havolalar (To'liq qator bo'ylab)
    builder.row(
        InlineKeyboardButton(text="💎 Rasmiy Kanalimiz", url="https://t.me/android_notes_developer")
    )

    return builder.as_markup()


def movie_action_keyboard(movie_title: str, movie_code: int) -> InlineKeyboardMarkup:
    """Kino topilganda: Foydalanuvchini harakatga undovchi tugmalar"""
    builder = InlineKeyboardBuilder()

    # Ulashish tugmasi foydalanuvchilar sonini oshirishga xizmat qiladi
    builder.row(
        InlineKeyboardButton(
            text="🚀 Do'stlarga ulashish",
            switch_inline_query=f"{movie_code}"
        )
    )

    # Bosh sahifa uchun markaziy tugma
    builder.row(
        InlineKeyboardButton(text="🏠 Bosh menyuga qaytish", callback_data="back_to_main")
    )

    return builder.as_markup()


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import config


def subscription_keyboard() -> InlineKeyboardMarkup:
    """
    Obuna bo'limi: config.mandatory_channels'dan dinamik oladi.
    Middleware ichida ham ishlatish mumkin.
    """
    builder = InlineKeyboardBuilder()

    # config.mandatory_channels ichida {'id': ..., 'url': ...} ko'rinishida saqlangan
    for i, channel in enumerate(config.mandatory_channels, 1):
        builder.row(InlineKeyboardButton(
            text=f"➕ {i}-kanalga obuna bo'lish",
            url=channel['url']
        ))

    # Tasdiqlash tugmasi
    builder.row(InlineKeyboardButton(
        text="✅ Obunani tasdiqlash",
        callback_data="check_subs"
    ))

    return builder.as_markup()


def back_keyboard() -> InlineKeyboardMarkup:
    """Orqaga qaytish: Minimalist uslub"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 Orqaga qaytish", callback_data="back_to_main"))
    return builder.as_markup()