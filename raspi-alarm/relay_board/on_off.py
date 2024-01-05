import asyncio
import time

import pigpio


class GPIOBridge:
    CH1 = 26
    CH2 = 20
    CH3 = 21

    LED1 = 19  # Running
    LED2 = 13  # Motion Detected
    LED3 = 6  # Armed

    PIEZO = 4

    loop = asyncio.get_event_loop()

    def __init__(self, pi: pigpio.pi) -> None:
        self.pi = pi
        # Relays board, they all need to set to high because the board is inverted
        pi.set_mode(self.CH1, pigpio.OUTPUT)
        pi.write(self.CH1, True)
        pi.set_mode(self.CH2, pigpio.OUTPUT)
        pi.write(self.CH2, True)
        pi.set_mode(self.CH3, pigpio.OUTPUT)
        pi.write(self.CH3, True)

        # Leds
        pi.set_mode(self.LED1, pigpio.OUTPUT)
        pi.set_mode(self.LED2, pigpio.OUTPUT)
        pi.set_mode(self.LED3, pigpio.OUTPUT)

        # Piezeo
        pi.set_mode(self.PIEZO, pigpio.OUTPUT)

    def set_led(self, led_nr: int, state: bool):
        if led_nr == 1:
            self.pi.write(self.LED1, state)
        if led_nr == 2:
            self.pi.write(self.LED2, state)
        if led_nr == 3:
            self.pi.write(self.LED3, state)

    def _actually_make_noise(self, duration: int = 3):
        square = [pigpio.pulse(1 << self.PIEZO, 0, 500), pigpio.pulse(0, 1 << self.PIEZO, 500)]
        self.pi.wave_add_generic(square)
        wid = self.pi.wave_create()
        if wid >= 0:
            self.pi.wave_send_repeat(wid)
            time.sleep(duration)
            self.pi.wave_tx_stop()
            self.pi.wave_delete(wid)

    def make_noise(self, duration: int = 5):
        self.loop.run_in_executor(None, lambda dur=duration: self._actually_make_noise(dur))

    def set_channel(self, channel_nr: int, state: bool):
        if channel_nr == 1:
            self.pi.write(self.CH1, not state)
        if channel_nr == 2:
            self.pi.write(self.CH2, not state)
        if channel_nr == 3:
            self.pi.write(self.CH3, not state)
        if channel_nr < 1:
            print("Stupid! uncorrect channel_nr, uncorrect channel_nr!")
        if channel_nr > 3:
            print("Stupid! uncorrect channel_nr, uncorrect channel_nr!")


if __name__ == '__main__':
    pi = pigpio.pi()
    rb = GPIOBridge(pi=pi)

    rb.make_noise()
