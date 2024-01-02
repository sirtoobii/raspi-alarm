import pigpio
import time

from relay_board.on_off import RelayBoard
from pir_sensor.motion_detect import Pir

pi = pigpio.pi()

relay_board = RelayBoard(pi=pi)

def motion_detected(gpio, level,tick):
    relay_board.set_channel(1, True)
    time.sleep(2)
    relay_board.set_channel(1, False)
    print("Motion detected")

pir = Pir(interrupt_pin=17, pi=pi, callback_fn=motion_detected)


while True:
    time.sleep(100)




