# bot/dispatcher.py
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers import router

def setup_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    return dp
