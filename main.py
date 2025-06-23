
from aiogram import Bot, Dispatcher
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command, CommandStart, CommandObject

import asyncio
import logging
from dotenv import load_dotenv
import os
import sys

from inl_kb import *

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv("config.env")
BOT_TOKEN = os.getenv("TOKEN")
ADMIN_ID = os.getenv("ADMINID")

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)



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

@dp.callback_query(CallbackQuery("my_descks"))

async def main():
    """Старт бота"""
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())