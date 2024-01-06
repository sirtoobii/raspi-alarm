import asyncio
import datetime
import logging
from typing import Callable

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandObject, Command
from aiogram.types import FSInputFile, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold

CALLBACKS = {}


class TelegramBot:
    dp = Dispatcher()

    def __init__(self, bot_token: str, logger: logging.Logger, chat_id: str, ipc_queue: asyncio.Queue,
                 disarm_callback: Callable, make_noise_callback: Callable, status_callback: Callable,
                 arm_callback: Callable):
        self.logger = logger
        self.ipc_queue = ipc_queue
        self.chat_id = chat_id
        self.bot = Bot(bot_token, parse_mode=ParseMode.HTML)
        CALLBACKS['disarm'] = disarm_callback
        CALLBACKS['make_noise'] = make_noise_callback
        CALLBACKS['status'] = status_callback
        CALLBACKS['arm'] = arm_callback
        self.disarm_callback = disarm_callback
        self.make_noise_callback = make_noise_callback
        self.tasks = []

    @staticmethod
    @dp.callback_query(F.data == "disarm")
    async def disarm(callback: types.CallbackQuery):
        CALLBACKS['disarm']()
        chat_id = callback.message.chat.id
        await callback.bot.send_message(chat_id, f"Disarmed by {callback.from_user.full_name}")

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
    @dp.callback_query(F.data == "make_noise")
    async def make_noise(callback: types.CallbackQuery):
        CALLBACKS['make_noise']()
        chat_id = callback.message.chat.id
        await callback.bot.send_message(chat_id, f"Noise started by {callback.from_user.full_name}")

    async def poll_ipc_queue(self):
        while True:
            item = await self.ipc_queue.get()
            if item is not None:
                if isinstance(item, dict):
                    if "image_path" in item:
                        await self.notify_motion_detected(item.get("image_path"))
                        self.logger.info("Image sent")
                    if "terminate" in item:
                        self.logger.info("Termination request received")
                        for task in self.tasks:
                            task.cancel()
                        await asyncio.sleep(1)
            await asyncio.sleep(1)

    @staticmethod
    @dp.message(Command("status"))
    async def command_status_handler(message: Message) -> None:
        result = CALLBACKS['status']()
        if result['armed']:
            msg = f"🟢 {hbold('Armed')}"
        else:
            msg = f"🔴 {hbold('Disarmed')}"
        await message.answer(msg)

    @staticmethod
    @dp.message(Command("arm"))
    async def command_arm_handler(message: Message) -> None:
        CALLBACKS['arm']()
        await message.answer(f"🟢 {hbold('Armed')}")

    async def start(self):
        self.logger.info("Staring Telegram Bot")
        bot = asyncio.create_task(self.dp.start_polling(self.bot, handle_signals=False), name='Telegram Bot')
        ipc = asyncio.create_task(self.poll_ipc_queue(), name='IPC')
        self.tasks = [bot, ipc]
        await asyncio.gather(*self.tasks)
