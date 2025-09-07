import asyncio
import datetime
import signal
import time

import pigpio
import os
import logging
from dotenv import load_dotenv
from numpy import ndarray

from gpio.GPIOBridge import GPIOBridge
from telegram.TelegramBot import TelegramBot
from camera.linux_camera import LinuxCamera
from camera.raspi_camera import RaspiCamera
from analyze.yolo import Yolo11Engine

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_GROUP_ID = os.getenv("TELEGRAM_GROUP_ID")
CAPTURE_N_IMAGES = int(os.getenv("CAPTURE_N_IMAGES", 5))
PERSON_MIN_CONFIDENCE = float(os.getenv("PERSON_MIN_CONFIDENCE", 0.85))


logger = logging.getLogger('Alarm PI')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s %(levelname)s %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

queue = asyncio.Queue()
pi = pigpio.pi()
relay_board = GPIOBridge(pi=pi)
yolo_engine = Yolo11Engine()

PIR = 17
BUTTON = 6

STATE = {
    'armed': False,
    'triggered': False,
    'changed_at': datetime.datetime.now(),
    'change_by': "STARTUP"
}


def toggle_arm_state():
    if STATE['armed']:
        relay_board.set_led(3, False)
        logger.info("DISARMED")
    else:
        relay_board.set_led(3, True)
        logger.info("ARMED")
    STATE['armed'] = not STATE['armed']
    STATE['changed_at'] = datetime.datetime.now()


def disarm_callback():
    STATE['change_by'] = "TELEGRAM"
    if STATE['armed']:
        toggle_arm_state()


def arm_callback():
    STATE['change_by'] = "TELEGRAM"
    if not STATE['armed']:
        toggle_arm_state()


def make_noise_callback():
    STATE['change_by'] = "BUTTON"
    relay_board.make_noise(duration=1)


def status_callback():
    return STATE.copy()


telegram = TelegramBot(bot_token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_GROUP_ID, ipc_queue=queue, logger=logger,
                       disarm_callback=disarm_callback, make_noise_callback=make_noise_callback,
                       status_callback=status_callback, arm_callback=arm_callback)


def motion_detected(gpio, level, tick):
    if STATE['armed']:
        logger.info("Motion detected")
        relay_board.set_channel(1, True, duration=10)
        relay_board.set_led(2, True, duration_secs=10, blink=True)
        time.sleep(1)
        person_detected: bool = False
        images: list[ndarray] = []
        confidence_score: float = 0
        with RaspiCamera(0, height=1280, width=720) as cam:
            for frame in cam.frames(wait_between_captures_sec=1, n_frames=CAPTURE_N_IMAGES, add_timestamp=True):
                result = yolo_engine.detect_person(frame)
                images.append(result.annotated_frame)
                if result.max_confidence_score > PERSON_MIN_CONFIDENCE:
                    person_detected = True
                    confidence_score = result.max_confidence_score

        if person_detected:
            image_paths = LinuxCamera.save_images(images, prefix="raspi", destination_folder="../captures")
            print(image_paths)
            # queue.put_nowait({"image_paths": image_paths, "confidence_score": confidence_score})
        else:
            logger.info(f"No notifications sent because there was no person in the image (confidence less than {PERSON_MIN_CONFIDENCE*100}%)")


def button_pressed(gpio, level, tick):
    logger.warning("Button pressed")
    toggle_arm_state()


# pigpio callbacks
# PIR
pi.set_mode(PIR, pigpio.INPUT)
motion_callback = pi.callback(PIR, pigpio.RISING_EDGE, motion_detected)

# Button
pi.set_mode(BUTTON, pigpio.INPUT)
pi.set_pull_up_down(BUTTON, pigpio.PUD_UP)
pi.set_glitch_filter(BUTTON, 150)
button_callback = pi.callback(BUTTON, pigpio.FALLING_EDGE, button_pressed)


async def signal_handler(received_signal, running_loop):
    logger.info(f"Received exit signal {received_signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not
             asyncio.current_task()]

    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    await asyncio.sleep(1)
    relay_board.set_led(1, False)  # OFF
    relay_board.set_led(2, False)  # OFF
    relay_board.set_led(3, False)  # OFF
    motion_callback.cancel()
    button_callback.cancel()
    pi.stop()
    running_loop.stop()
    logger.info("Bye")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    logger.info("Starting...")

    start_task = loop.create_task(telegram.start(), name="Telegram Bot Wrapper")
    relay_board.set_led(1, True)  # ON

    for sig in [signal.SIGHUP, signal.SIGTERM, signal.SIGINT]:
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(signal_handler(s, loop)))

    try:
        loop.run_forever()
    finally:
        loop.close()
