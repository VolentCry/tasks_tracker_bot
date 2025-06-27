
from aiogram import Bot, Dispatcher
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

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
    for user_id in Db.take_users_ids():
        if user_id == callback.from_user.id and Db.take_user_cnt_desks(user_id) != 0: 
            await bot.send_message(callback.from_user.id, "Вот ваши доски:", reply_markup=desks_kb(user_id))
            await callback.answer()
            break
        elif user_id == callback.from_user.id and Db.take_user_cnt_desks(user_id) == 0:
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


@dp.callback_query(lambda c: c.data == "create_desk")
async def create_desk(callback: CallbackQuery):
    """Создаёт новую доску для пользователя."""
    global Db
    user_id = callback.from_user.id
    if Db.take_user_cnt_desks(user_id) < 10:
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
    await bot.send_message(callback.from_user.id, 
                           text=f"Номер доски: {int(data[2]) + 1}\n"\
                            f"Владелец: {callback.from_user.username}\n"\
                            f"Количество задач:  \n\n"\
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


@dp.callback_query(lambda c: c.data.startswith(f"add_new_task_to_desk_"))
async def add_new_task_to_user_desk(callback: CallbackQuery, state: FSMContext):
    """Добавление нового таска в доску"""
    data = callback.data.split("_")
    await state.set_state(TaskMaker.number_of_desk)
    await state.update_data(number_of_desk=int(data[-1]))
    await state.set_state(TaskMaker.task_name)
    await bot.send_message(callback.from_user.id, text="Давайте введём название задачи")
    await callback.answer()
# ----------------------------------------------------------------------------


async def main():
    """Старт бота"""
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())