import asyncio
import time
import threading
from typing import Callable

import pigpio


class GPIOBridge:
    RELAYS = {
        1: 26,
        2: 20,
        3: 21
    }

    LEDS = {
        1: 19,
        2: 13,
        3: 16
    }

    PIEZO = 4

    loop = asyncio.get_event_loop()

    def __init__(self, pi: pigpio.pi) -> None:
        self.pi = pi
        # Relays board, they all need to set to high because the board is inverted
        [pi.set_mode(relay_pin, pigpio.OUTPUT) for relay_pin in self.RELAYS.values()]
        [pi.write(relay_pin, True) for relay_pin in self.RELAYS.values()]

        # Leds
        [pi.set_mode(led_gpio, pigpio.OUTPUT) for led_gpio in self.LEDS.values()]

        # Piezeo
        pi.set_mode(self.PIEZO, pigpio.OUTPUT)

    def _oscillate_gpio(self, duration: int, gpio_pin: int, high_duration=1000, low_duration=1000, end_state=False):
        square = [pigpio.pulse(1 << gpio_pin, 0, high_duration), pigpio.pulse(0, 1 << gpio_pin, low_duration)]
        self.pi.wave_add_generic(square)
        wid = self.pi.wave_create()
        if wid >= 0:
            self.pi.wave_send_repeat(wid)
            time.sleep(duration)
            self.pi.wave_tx_stop()
            self.pi.wave_delete(wid)
            self.pi.write(gpio_pin, end_state)

    def set_led(self, led_nr: int, state: bool, blink: bool = False, duration_secs: int = -1):
        led_gpio = self.LEDS.get(led_nr, None)
        if led_gpio is not None:
            if duration_secs != -1 and blink:
                self._fire_and_forget(duration_secs, self._oscillate_gpio, [led_gpio, 50000, 50000])
            else:
                self.pi.write(led_gpio, state)

    def _fire_and_forget(self, duration: int, task: Callable, task_args: list = None):
        self.loop.run_in_executor(None, lambda dur=duration: task(dur, *task_args))

    def make_noise(self, duration: int = 5):
        self._fire_and_forget(duration, self._oscillate_gpio, [self.PIEZO, 500, 500])

    def _keep_on_for(self, duration_sec: int, gpio_pin: int, state: bool):
        self.pi.write(gpio_pin, state)
        time.sleep(duration_sec)
        self.pi.write(gpio_pin, not state)

    def set_channel(self, channel_nr: int, state: bool, duration: int = -1):
        relay_gpio = self.RELAYS.get(channel_nr, None)
        if relay_gpio is not None:
            if duration != -1:
                self._fire_and_forget(duration, self._keep_on_for, [relay_gpio, not state])
            else:
                self.pi.write(relay_gpio, not state)
        else:
            print("Stupid! incorrect channel_nr, incorrect channel_nr!")


if __name__ == '__main__':
    pi = pigpio.pi()
    rb = GPIOBridge(pi=pi)

    rb.set_channel(2, True, 2)
    time.sleep(2)
    pi.stop()
