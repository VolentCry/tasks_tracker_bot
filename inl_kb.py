from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import Database

def start_kb():
    buttons = [
        [InlineKeyboardButton(text="📝 Мои доски", callback_data="my_descks")],
        [InlineKeyboardButton(text="⏰ Настройкаи пользователя", callback_data="profile_settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def desks_kb(user_id: int):
    db = Database()
    buttons = []
    buttons.append([InlineKeyboardButton(text="📝 Создать новую доску", callback_data="create_desk")])
    for i in range(db.take_user_cnt_desks(user_id)):
        buttons.append([InlineKeyboardButton(text=f"Доска номер: {i + 1}", callback_data=f"desks_{user_id}_{i}")])
    keybord_desks = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keybord_desks


def desk_menu(user_id: int, id_of_desk: int):
    buttons = [
        [InlineKeyboardButton(text="📝 Редактирование", callback_data=f"edit_desk_{user_id}_{id_of_desk}")],
        [InlineKeyboardButton(text="⏰ Список задач", callback_data=f"open_tasks_of_desk_{user_id}_{id_of_desk}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def edit_desk_kb(user_id: int, id_of_desk: int):
    buttons = [
        [InlineKeyboardButton(text="📝 Добавить новую задачу", callback_data=f"add_new_task_to_desk_{user_id}_{id_of_desk}")],
        [InlineKeyboardButton(text="📓 Изменить название", callback_data=f"change_name_of_desk_{user_id}_{id_of_desk}")],
        [InlineKeyboardButton(text="🎯 Изменить цель", callback_data=f"change_goal_of_desk_{user_id}_{id_of_desk}")],
        [InlineKeyboardButton(text="❌ Удалить доску", callback_data=f"delete_desk_{user_id}_{id_of_desk}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)