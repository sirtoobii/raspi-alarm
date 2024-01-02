import pigpio 

pi = pigpio.pi()

CH1=26
CH2=20
CH3=21

pi.set_mode(CH1, pigpio.OUTPUT)
pi.set_mode(CH2, pigpio.OUTPUT)
pi.set_mode(CH3, pigpio.OUTPUT)

def set_channel(channel_nr, state:bool):
    if channel_nr==1:
       pi.write(CH1, not state)
    if channel_nr==2:
       pi.write(CH2, not state)
    if channel_nr==3:
       pi.write(CH3, not state)
    if channel_nr < 1:
       print("Stupid! uncorrect channel_nr, uncorrect channel_nr!")
    if channel_nr > 3:
       print("Stupid! uncorrect channel_nr, uncorrect channel_nr!")


if not pi.connected:
    print("Failed to connect! Where is my power bank?")
    exit()

set_channel(3,False)

pi.stop()


