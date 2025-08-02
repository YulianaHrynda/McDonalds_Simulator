import asyncio
from aiogram import Bot, Dispatcher
from bot.dispatcher import setup_dispatcher
from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def main():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = setup_dispatcher()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
