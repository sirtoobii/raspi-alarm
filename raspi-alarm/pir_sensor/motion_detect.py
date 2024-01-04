import pigpio
from typing import Callable

INTERRUPT_PIN = 17


class Pir:
    def __init__(self, interrupt_pin, pi: pigpio.pi, callback_fn: Callable) -> None:
        self.pi = pi
        self._clean = False
        self.interrupt_pin = interrupt_pin
        pi.set_mode(INTERRUPT_PIN, pigpio.INPUT)
        self.cb = pi.callback(INTERRUPT_PIN, pigpio.RISING_EDGE, callback_fn)

    def stop(self):
        self.cb.cancel()
        self.pi.stop()
        self._clean = True

    def __del__(self):
        if not self._clean:
            self.stop()
