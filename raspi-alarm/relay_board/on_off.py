import pigpio

class RelayBoard:
    CH1 = 26
    CH2 = 20
    CH3 = 21

    def __init__(self, pi: pigpio.pi) -> None:
        self.pi = pi
        pi.set_mode(self.CH1, pigpio.OUTPUT)
        pi.set_mode(self.CH2, pigpio.OUTPUT)
        pi.set_mode(self.CH3, pigpio.OUTPUT)

    def set_channel(self, channel_nr: int, state: bool):
        if channel_nr == 1:
            self.pi.write(self.CH1, not state)
        if channel_nr == 2:
            self.pi.write(self.CH2, not state)
        if channel_nr == 3:
            self.pi.write(self.CH3, not state)
        if channel_nr < 1:
            print('Stupid! incorrect channel_nr, incorrect channel_nr!')
        if channel_nr > 3:
            print('Stupid! incorrect channel_nr, incorrect channel_nr!')