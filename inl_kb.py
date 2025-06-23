from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def start_kb():
    buttons = [
        [InlineKeyboardButton(text="📝 Мои доски", callback_data="my_descks")],
        [InlineKeyboardButton(text="⏰ Настройкаи пользователя", callback_data="profile_settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)