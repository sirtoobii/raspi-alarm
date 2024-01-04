import asyncio
import datetime

import pigpio
import os
import logging
from dotenv import load_dotenv
from relay_board.on_off import RelayBoard
from pir_sensor.motion_detect import Pir
from camera.Camera3 import Camera3
from telegram.TelegramBot import TelegramBot

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_GROUP_ID = os.getenv("TELEGRAM_GROUP_ID")

logger = logging.getLogger("Alarm PI")
queue = asyncio.Queue()
pi = pigpio.pi()
relay_board = RelayBoard(pi=pi)
camera = Camera3()
telegram = TelegramBot(bot_token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_GROUP_ID, ipc_queue=queue, logger=logger)


def motion_detected(gpio, level, tick):
    print("Motion detected")
    date_str = datetime.datetime.now().strftime("%d%m%d-%H%M%S")
    image_filename = f"capture_{date_str}.jpg"
    camera.capture_image(image_filename)
    print("Image captured")
    queue.put({"image_path": image_filename})


pir = Pir(interrupt_pin=17, pi=pi, callback_fn=motion_detected)

asyncio.run(telegram.start())
