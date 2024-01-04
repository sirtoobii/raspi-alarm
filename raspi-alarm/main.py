import asyncio
import datetime
import signal
import sys
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

logger = logging.getLogger('Alarm PI')
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)
queue = asyncio.Queue()
pi = pigpio.pi()
relay_board = RelayBoard(pi=pi)
camera = Camera3()
telegram = TelegramBot(bot_token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_GROUP_ID, ipc_queue=queue, logger=logger)


def motion_detected(gpio, level, tick):
    logger.info("Motion detected")
    date_str = datetime.datetime.now().strftime("%d%m%d-%H%M%S")
    image_filename = f"capture_{date_str}.jpg"
    camera.capture_image(image_filename)
    logger.info(f"Image captured {image_filename}")
    queue.put_nowait({"image_path": image_filename})


pir = Pir(interrupt_pin=17, pi=pi, callback_fn=motion_detected)


def signal_handler(sig, frame):
    logger.warning("SIGINT received, exiting..")
    queue.put_nowait({"terminate": True})
    pir.stop()
    asyncio.get_event_loop().stop()
    logger.info("Bye")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.pause()

if __name__ == '__main__':
    logger.info("Starting...")
    asyncio.run(telegram.start())
