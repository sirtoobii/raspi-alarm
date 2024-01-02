import pigpio
from typing import Callable

INTERRUPT_PIN = 17

class Pir:
    def __init__(self, interrupt_pin, pi: pigpio.pi, callback_fn: Callable) -> None:
        self.pi = pi
        self.interrupt_pin = interrupt_pin
        pi.set_mode(INTERRUPT_PIN, pigpio.INPUT)
        cb1 = pi.callback(INTERRUPT_PIN,pigpio.RISING_EDGE,callback_fn)
    

