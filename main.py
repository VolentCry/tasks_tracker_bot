from aiogram import Bot, Dispatcher
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode

import asyncio
import logging
from dotenv import load_dotenv
import os
import sys

from inl_kb import *
from db import Database

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv("config.env")
BOT_TOKEN = os.getenv("TOKEN")
ADMIN_ID = os.getenv("ADMINID")

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)
Db = Database()

class TaskMaker(StatesGroup):
    """Машина состояний для создание нового таска"""
    number_of_desk = State()
    task_name = State()
    task_description = State()
    task_date = State()

@dp.message(CommandStart())
async def start_bot(message: Message):
    """Старт бота с приветственным сообщением"""
    await bot.send_message(
        message.from_user.id,
        text="Приветствую тебя в твоём планере дел!",
        reply_markup=start_kb()
                           )

@dp.message(Command("stop"))
async def stop_bot(message: Message):
    """Стоп бота, команда для админа"""
    if message.from_user.id == int(ADMIN_ID):
        await bot.send_message(
            message.from_user.id,
            text="Бот остановлен."
                            )
        sys.exit()

@dp.callback_query(lambda c: c.data == "my_descks")
async def my_desks(callback: CallbackQuery):
    """Выводит пользователю всего его активные доски.
    Если они отсутствуют, то предлагает создать новую доску"""
    global Db
    user_cnt_desk, cnt_tasks = Db.get_tasks_and_desks_cnt(callback.from_user.id)
    for user_id in Db.take_users_ids():
        if user_id == callback.from_user.id and user_cnt_desk != 0: 
            await bot.send_message(callback.from_user.id, "Вот ваши доски:", reply_markup=desks_kb(user_id))
            await callback.answer()
            break
        elif user_id == callback.from_user.id and user_cnt_desk == 0:
            await bot.send_message(callback.from_user.id, text="У вас ещё не создано ни одной доски. \nСейчас мы создадим вам новую доску!")
            try:
                Db.create_desk(callback.from_user.id)
                await bot.send_message(callback.from_user.id, text="Доска была успешно создана.")
                await bot.send_message(callback.from_user.id, "Вот ваши доски:", reply_markup=desks_kb(user_id))
            except:
                await bot.send_message(callback.from_user.id, text="Возникли технические проблемы, попробуйте снова позже.")
            await callback.answer()
            break
    else:
        await bot.send_message(callback.from_user.id, text="На данный момент вас нет в базе данных. Сейчас вас добавим...")
        Db.add_user(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
        await bot.send_message(callback.from_user.id, text="Ваш профиль был успешно создан!", reply_markup=start_kb())
        await callback.answer()


@dp.callback_query(lambda c: c.data == "profile_settings")
async def my_desks(callback: CallbackQuery):
    """Выводит пользователю информацию о нём"""
    desks_cnt, tasks_cnt = Db.get_tasks_and_desks_cnt(callback.from_user.id)
    user_phone_number = "-/-"
    await bot.send_message(callback.from_user.id,
                           text=f"Имя пользователя: {callback.from_user.first_name}\n"\
                           f"Номер телефона: <i>{user_phone_number}</i>\n"\
                           f"Никнейм: <code>@{callback.from_user.username}</code>\n"\
                           f"Количество активных досок: <b>{desks_cnt}</b>\n"\
                           f"Общее количество тасков: <b>{tasks_cnt}</b>",
                           reply_markup=back_kb(),
                           parse_mode=ParseMode.HTML
                           )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "back_to_start")
async def back_to_menu(message: Message):
    """Выход из настроек пользователя обрабтно в главное меню"""
    await bot.send_message(
        message.from_user.id,
        text="Приветствую тебя в твоём планере дел!",
        reply_markup=start_kb()
                           )


@dp.callback_query(lambda c: c.data == "create_desk")
async def create_desk(callback: CallbackQuery):
    """Создаёт новую доску для пользователя."""
    global Db
    user_id = callback.from_user.id
    user_cnt_desk, cnt_tasks = Db.get_tasks_and_desks_cnt(user_id)
    if user_cnt_desk < 10:
        try:
            Db.create_desk(callback.from_user.id)
            await bot.send_message(callback.from_user.id, text="Доска была успешно создана.")
            await bot.send_message(callback.from_user.id, text="Приветствую тебя в твоём планере дел!", reply_markup=start_kb())
        except:
            await bot.send_message(callback.from_user.id, text="Возникли технические проблемы, попробуйте снова позже.")
    else:
        await bot.send_message(callback.from_user.id, text="Вами достигнут лимит по количеству имеющихся досок.")
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith(f"desks_"))
async def open_desk_menu(callback: CallbackQuery):
    """Открывает основную информацию доски и меню"""
    data = callback.data.split("_")
    tasks_cnt = len(Db.get_all_tasks_info(int(data[1]), int(data[2]) + 1))
    await bot.send_message(callback.from_user.id, 
                           text=f"Номер доски: {int(data[2]) + 1}\n"\
                            f"Владелец: {callback.from_user.username}\n"\
                            f"Количество задач: {tasks_cnt} \n\n"\
                            f"Дальнейшие действия?", 
                           reply_markup=desk_menu(int(data[1]), int(data[2])))
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith(f"edit_desk_"))
async def edit_desk(callback: CallbackQuery):
    """Режим для редактирования доски: удаление, смена имени, цели, добавление тасков"""
    data = callback.data.split("_")
    await bot.send_message(callback.from_user.id, text="Вот возможные действия: ", reply_markup=edit_desk_kb(int(data[-2]), int(data[-1])))
    await callback.answer()


# --------------- Добавленеи новой задачи ------------------
@dp.callback_query(lambda c: c.data.startswith(f"add_new_task_to_desk_"))
async def add_new_task_to_user_desk(callback: CallbackQuery, state: FSMContext):
    """Добавление нового таска в доску"""
    data = callback.data.split("_")
    await state.set_state(TaskMaker.number_of_desk)
    await state.update_data(number_of_desk=int(data[-1]))
    await state.set_state(TaskMaker.task_name)
    await bot.send_message(callback.from_user.id, text="Давайте введём название задачи")
    await callback.answer()

@dp.message(TaskMaker.task_name)
async def task_descriprion(message: Message, state: FSMContext):
    """Добавление описания к задаче"""
    await state.update_data(task_name=message.text)
    await state.set_state(TaskMaker.task_description)
    await bot.send_message(message.from_user.id, text='📝 Теперь введите описание задачи. (необезательно, можно просто "-")')


@dp.message(TaskMaker.task_description)
async def task_date(message: Message, state: FSMContext):
    """Добавление времени к задаче"""
    await state.update_data(task_description=message.text)
    await state.set_state(TaskMaker.task_date)
    await bot.send_message(message.from_user.id, text='⏳ Теперь введите дедлайн задачи. (необезательно, можно просто "-")\nДату вводите в формате: 01.01.2025🗓')


@dp.message(TaskMaker.task_date)
async def task_data_save(message: Message, state: FSMContext):
    """Сохранение всех переменных. Очищение машины состояний"""
    await state.update_data(task_date=message.text)
    task_data = await state.get_data()
    await state.clear()
    try:
        Db.add_task_to_desk(message.from_user.id, int(task_data['number_of_desk']) + 1, task_data['task_name'], task_description=task_data['task_description'], date_time=task_data['task_date'])
        await bot.send_message(message.from_user.id, text='Таск был добавлен на доску!')
    except ValueError as e:
        await bot.send_message(message.from_user.id, text=f'К сожалению данная дата не валидна, так как {e.args[0].lower()}')
        print(e.args)
# ----------------------------------------------------------------------------

@dp.callback_query(lambda c: c.data.startswith("open_tasks_of_desk_"))
async def show_user_tasks_at_desk(callback: CallbackQuery):
    """Отображает все задачи пользователя"""
    data = callback.data.split("_")
    await bot.send_message(callback.from_user.id, text=f"Доска номер: <b>{int(data[-1]) + 1}</b>\nВладелец: <code>{callback.from_user.username}</code>\n\n<b><u>Задачи:</u></b>", reply_markup=tasks_menu(int(data[-2]), int(data[-1]) + 1), parse_mode=ParseMode.HTML)
    await callback.answer()


# ----------------------------- Работа с отдельными тасками -----------------------------
@dp.callback_query(lambda c: c.data.startswith("t_desks_"))
async def show_task_menu_info(callback: CallbackQuery):
    """Отображает меню для отдельной задачи"""
    data = callback.data.split("_")

    user_id = int(data[-4])
    id_of_desk = int(data[-3])

    tasks = Db.get_all_tasks_info(user_id, id_of_desk)
    for num, task in enumerate(tasks):
        if num == int(data[-1]):
            status = 'не выполнена ❌' if task[-1] == 0 else 'выполнена ✅'
            await bot.send_message(callback.from_user.id, text=f"<b>{task[0]}</b>\n\n<u>Описание:</u> {task[1]}\n<u>Дата окончания:</u> {task[2]}\n\nСтатус: <i>{status}</i>", reply_markup=task_edit_menu(user_id, id_of_desk, int(data[-1])), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("change_task_status_"))
async def show_user_tasks_at_desk(callback: CallbackQuery):
    """Меняет статус задачи(осуществляется через изменение текста сообщения)"""

    data = callback.data.split("_")
    user_id = int(data[-3])
    id_of_desk = int(data[-2])

    name_of_task = callback.message.text.split("\n")[0]

    status_start = 'не выполнена ❌' if 'не выполнена ❌' in callback.message.text else 'выполнена ✅'
    status_changed = 'не выполнена ❌' if 'выполнена ✅' in callback.message.text else 'выполнена ✅'
    await callback.message.edit_text(text=f"{callback.message.text.replace(status_start, status_changed)}", reply_markup=task_edit_menu(user_id, id_of_desk, int(data[-1])), parse_mode=ParseMode.HTML)
    if status_changed == 'выполнена ✅':
        await callback.answer(text=f'Задача "{name_of_task}" выполнена!')
    else:
        await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("delete_task_"))
async def delete_task(callback: CallbackQuery):
    """Удаление определённой задачи из доски"""
    data = callback.data.split("_")
    user_id = int(data[-3])
    id_of_desk = int(data[-2])
    name_of_task = callback.message.text.split("\n")[0]
    Db.delete_task(user_id, id_of_desk, name_of_task)
    await callback.message.edit_text(text="❌ Задача удалена. ❌")
    await start_bot(callback)
    await callback.answer()



# ----------------------------------------------------------

async def main():
    """Старт бота"""
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())