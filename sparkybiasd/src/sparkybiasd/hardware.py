"""
@authors: Cody Roberson (carobers@asu.edu)

"""
import smbus2
from omegaconf import OmegaConf
from time import sleep

__INA219ADDRTABLE = {
    1: 0x40,
    2: 0x41,
    3: 0x42,
    4: 0x43,
    5: 0x44,
    6: 0x45,
    7: 0x46,
    8: 0x47
}

__AD5144ADDRTABLE = {
    1: 0x20,
    2: 0x22,
    3: 0x23,
    4: 0x28,
    5: 0x2A,
    6: 0x2B,
    7: 0x2C,
    8: 0x2F
}

class biascard:
    iicBus = smbus2.SMBus("/dev/i2c-1")
    def __init__(self, address) -> None:
        self.address = address
        self.setRepeater(1, 1, 0)
        self.state = OmegaConf.create({
                'address' : address,
                'chan1R': 0,
                'chan2R': 0,
                'chan3R': 0,
                'chan4R': 0,
                'chan5R': 0,
                'chan6R': 0,
                'chan7R': 0,
                'chan8R': 0,
                'chanEnables': [False for _ in range(8)]
        })

    def close(self):
        biascard.iicBus.close()

    def enableAllChannels(self):
        biascard.iicBus.write_byte(0x27, 0)
        self.state.chanEnables = [True for _ in range(8)]
            
    def disableAllChannels(self):
        biascard.iicBus.write_byte(0x27, 0xFF)
        self.state.chanEnables = [False for _ in range(8)]

    def enChannel(self, channel, en: bool):
        channel -= 1
        word = 0
        self.state.chanEnables[channel] = en
        s = self.state.chanEnables
        for i in range(1, 8+1):
            word = (word << 1) | (0 if s[i-1] else 1)
        biascard.iicBus.write_byte(0x27, word)

    def setRepeater(self, en: int, gpio1:int, gpio2: int):
        """
        Sets the repeater state

        Parameters:
            en(int): Enable 1 or 0
            gpio1(int): Enable GPIO 1
            gpio2(int): Enable GPIO 2
        """
        # Gets address from bias card
        # TODO: Fix the assertion messages
        addr = self.state["address"]
        assert en == 1 or en == 0, "Thats not boolean >.>"
        assert gpio1 == 1 or gpio1 == 0, "Thats not boolean >.>"
        assert gpio2 == 1 or gpio2 == 0, "Thats not boolean >.>"
        cmdByte = (en << 7) | gpio2 << 6 | gpio1 << 5
        biascard.iicBus.write_byte(0x60+addr, cmdByte)

    def setWiper(self, channel, value):
        biascard.iicBus.write_byte_data(__AD5144ADDRTABLE[channel], 0b00010000, value & 0xFF)
        biascard.iicBus.write_byte_data(__AD5144ADDRTABLE[channel], 0b00010001, (value >>  8) & 0xFF)
        biascard.iicBus.write_byte_data(__AD5144ADDRTABLE[channel], 0b00010010, (value >> 16) & 0xFF)
        biascard.iicBus.write_byte_data(__AD5144ADDRTABLE[channel], 0b00010011, (value >> 24) & 0xFF)



