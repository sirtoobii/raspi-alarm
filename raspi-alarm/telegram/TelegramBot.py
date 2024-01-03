import datetime
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder


class TelegramBot:
    storage = MemoryStorage()
    dp = Dispatcher()

    def __init__(self, bot_token: str, logger: logging.Logger, chat_id: str):
        self.logger = logger
        self.chat_id = chat_id
        self.bot = Bot(bot_token, parse_mode=ParseMode.HTML)

    async def notify_motion_detected(self, image_path: str):
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(
            text="Disarm",
            callback_data="disarm"),
            types.InlineKeyboardButton(
                text="Make Noise",
                callback_data="make_noise")
        )
        photo = FSInputFile(image_path)
        await self.bot.send_photo(self.chat_id, photo=photo, caption=f"{datetime.datetime.now()}",
                                  reply_markup=builder.as_markup())

    @staticmethod
    @dp.callback_query(F.data == "disarm")
    async def share_contact(callback: types.CallbackQuery):
        chat_id = callback.message.chat.id
        await callback.bot.send_message(chat_id, f"Disarmed by {callback.from_user.full_name}")

    @staticmethod
    @dp.callback_query(F.data == "make_noise")
    async def share_contact(callback: types.CallbackQuery):
        chat_id = callback.message.chat.id
        await callback.bot.send_message(chat_id, f"Noise started by {callback.from_user.full_name}")

    async def start(self):
        await self.dp.start_polling(self.bot)
