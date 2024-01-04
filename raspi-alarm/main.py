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


async def signal_handler(received_signal, running_loop):
    logger.info(f"Received exit signal {received_signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not
             asyncio.current_task()]

    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    await asyncio.sleep(1)
    pir.stop()
    running_loop.stop()
    logger.info("Bye")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    logger.info("Starting...")

    start_task = loop.create_task(telegram.start(), name="Telegram Bot Wrapper")

    for sig in [signal.SIGHUP, signal.SIGTERM, signal.SIGINT]:
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(signal_handler(s, loop)))

    try:
        loop.run_forever()
    finally:
        loop.close()
