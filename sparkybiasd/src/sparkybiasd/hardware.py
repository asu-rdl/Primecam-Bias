"""
@authors: Cody Roberson (carobers@asu.edu)
@Documantation:
    This file is the lowest level interaction with the hardware. The individual chips of the bias board are all
    programmed here. 
"""
import smbus2
import time
import numpy as np
# Constants for the INA219
INA219_CONFIG_BVOLTAGERANGE_32V = 0x2000
INA219_CONFIG_GAIN_4_160MV = 0x1000
# INA219_CONFIG_GAIN_8_320MV = 0x1800
INA219_CONFIG_BADCRES_12BIT = 0x0180
INA219_CONFIG_SADCRES_12BIT_1S_532US = 0x0018
INA219_CONFIG_MODE_SANDBVOLT_CONTINUOUS = 0x07
INA219_REG_CONFIG = 0x00
INA219_REG_CALIBRATION = 0x05
INA219_REG_SHUNTVOLTAGE = 0x01
INA219_REG_BUSVOLTAGE = 0x02
INA219_REG_POWER = 0x03
INA219_REG_CURRENT = 0x04


def MSBF(val: int) -> int:
    """Swaps byte order of 'val'. (needed for current sense chip)

    :param val: 16-bit value
    :type val: int (unsigned)
    :return: 16-bit MSB first value
    :rtype: int (unsigned)
    """
    return ((val & 0xFF) << 8) | ((val >> 8) & 0xFF)


# Hard Coded Config based off of Adafruit INA219 32V_2A
INA219CONFIG = MSBF(
    INA219_CONFIG_BVOLTAGERANGE_32V
    | INA219_CONFIG_GAIN_4_160MV 
    | INA219_CONFIG_BADCRES_12BIT
    | INA219_CONFIG_SADCRES_12BIT_1S_532US
    | INA219_CONFIG_MODE_SANDBVOLT_CONTINUOUS
)
INACALVALUE = MSBF(0x1000)

INA219ADDRTABLE = {
    1: 0x40,
    2: 0x41,
    3: 0x42,
    4: 0x43,
    5: 0x44,
    6: 0x45,
    7: 0x46,
    8: 0x47,
}
AD5144ADDRTABLE = {
    1: 0x20,
    2: 0x28,
    3: 0x2C,
    4: 0x22,
    5: 0x2A,
    6: 0x2E,
    7: 0x23,
    8: 0x2F
}

class BiasCard:

    """
    Represents an individual bias card within a bias supply.
    On init, attempts to connect LTC4302 (Address 0) I2C bus. This is the gate between the PI at 3v3 and the rest of the 
    system at 5V.
    """
    iicBus = smbus2.SMBus("/dev/i2c-1")
    def __init__(self, address) -> None:

        # set_repeater gets address from self.address
        self.address = 0
        self.set_repeater(1, 0, 0)
        self.address = address
        
        self.set_repeater(1, 1, 0)

        self.channel_enables = 0
        self.test_enables = 0
        self.read_expander()
        self.wiper_states = [0,0,0,0,0,0,0,0]

        for i in range(1, 8+1):
            self.init_currsense(i)
            self.read_ad5144(i)

    def read_ad5144(self, chan: int):
        """Gets the wiper state for a provided channel and saves the result to self.wiper_states.

        Parameters:
            chan(int) : Channel to read
        
        Returns:
            Wiper state (int) from 0 to 1023
        """
        assert chan > 0 and chan < 9,  "Expected channel 1 through 8"
        BiasCard.iicBus.write_byte_data(AD5144ADDRTABLE[chan], 0b0011_0000, 0b000000_11)
        w1 = BiasCard.iicBus.read_byte(AD5144ADDRTABLE[chan])
        BiasCard.iicBus.write_byte_data(AD5144ADDRTABLE[chan], 0b0011_0001, 0b000000_11)
        w2 = BiasCard.iicBus.read_byte(AD5144ADDRTABLE[chan])
        BiasCard.iicBus.write_byte_data(AD5144ADDRTABLE[chan], 0b0011_0010, 0b000000_11)
        w3 = BiasCard.iicBus.read_byte(AD5144ADDRTABLE[chan])
        BiasCard.iicBus.write_byte_data(AD5144ADDRTABLE[chan], 0b0011_0011, 0b000000_11)
        w4 = BiasCard.iicBus.read_byte(AD5144ADDRTABLE[chan])

        tot = w1+w2+w3+w4
        self.wiper_states[chan-1] = tot
        return tot 


    def read_expander(self):
        state = BiasCard.iicBus.read_i2c_block_data(0x27, 0, 2)
        if len(state) == 2:
            self.channel_enables = state[0]
            self.test_enables = state[1]
        else:
            # FIXME: handle error case from expander
            # len does not eq 2?
            pass

    def erics_flash(self):
        """dont ask, he wanted this not me."""
        for _ in range(4):
            self.set_repeater(1, 1, 0)
            time.sleep(0.1)
            self.set_repeater(1, 0, 0)
            time.sleep(0.1)
            self.set_repeater(1, 0, 0)

    def close(self):
        self.set_repeater(0, 0, 0)

    def open(self):
        """
        Connect the internal I2C bus of this bias card to the RPI
        """
        self.set_repeater(1, 1, 0)

    def enable_all_chan(self):
        """Enables the output of all of the card's bias supply lines."""
        for i in range(1, 8+1):
            self.enable_chan(i, True)   

    def disable_all_chan(self):
        """Creates an OPEN on all of this card's bias supply lines."""
        for i in range(1, 8+1):
            self.enable_chan(i, False)

    def enable_testload(self, channel: int, en: bool = True):
        """
        We use a Texas Instruments 8575 to control the outputs
        of each bias channel. Each pin is in an open-drain configuration. In other words,
        the outputs are active low.

        Parameters:
            channel(int): Channel of the card to configure (1-8)
            
        """
        p = self.test_enables
        if en:
            p = self.test_enables | (1 << (channel-1))
        else:
            p = self.test_enables & (~(1 << (channel-1))) 

        self.test_enables = p
        BiasCard.iicBus.write_i2c_block_data(0x27, 0, [~self.channel_enables, ~self.test_enables])

    def enable_chan(self, channel: int, en: bool = True):
        """
        We use a Texas Instruments 8575 to control the outputs
        of each bias channel. Each pin is in an open-drain configuration.
        In other words, the outputs are active low.

        Parameters:
            channel(int): Channel of the card to configure (1-8)
            
        """
        p = self.channel_enables
        if en:
            p = self.channel_enables | (1 << (channel-1))
        else:
            p = self.channel_enables & (~(1 << (channel-1))) 

        self.channel_enables = p
        BiasCard.iicBus.write_i2c_block_data(0x27, 0, [~self.channel_enables, ~self.test_enables])
        

    def set_repeater(self, en: int, gpio1:int, gpio2: int) -> None:
        """
        Controls the LTC4302 Repeater. Each card has a repeater for both addressing and
        to ensure isolation from the rest of the I2C bus. 

        Parameters:
            en(int): Enable 1 or 0 tf
            gpio1(int): Enable GPIO 1
            gpio2(int): Enable GPIO 2

        Returns:
            None
        """
        # Gets address from bias card
        addr = self.address
        io1 = ~gpio1 # open drain; have pullup resistor, pull low to make activity LED glow
        io2 = ~gpio2 # Unused....
        assert en == 1 or en == 0, "Expected a 0 or 1"
        assert gpio1 == 1 or gpio1 == 0, "Expected a 0 or 1"
        assert gpio2 == 1 or gpio2 == 0, "Expected a 0 or 1"
        cmdByte = (en << 7) | (io2 << 6) |  (io1 << 5)
        BiasCard.iicBus.write_byte(0x60+addr, cmdByte)

    def set_wiper(self, channel, value):
        assert value >= 0 and value <= 1023, f"Invalid value of {value}"
        div = value // 256
        rem = value % 256
        x = 0
        for _ in range(div):
            x = (x | 255) << 8
        x = x+rem

        BiasCard.iicBus.write_byte_data(AD5144ADDRTABLE[channel], 0b00010000, x & 0xFF)
        BiasCard.iicBus.write_byte_data(AD5144ADDRTABLE[channel], 0b00010001, (x >>  8) & 0xFF)
        BiasCard.iicBus.write_byte_data(AD5144ADDRTABLE[channel], 0b00010010, (x >> 16) & 0xFF)
        BiasCard.iicBus.write_byte_data(AD5144ADDRTABLE[channel], 0b00010011, (x >> 24) & 0xFF)
        self.wiper_states[channel-1] = value


    def set_wiper_max(self, channel):
        x = 0xFF_FF_FF_FF
        BiasCard.iicBus.write_byte_data(AD5144ADDRTABLE[channel], 0b00010000, x & 0xFF)
        BiasCard.iicBus.write_byte_data(AD5144ADDRTABLE[channel], 0b00010001, (x >>  8) & 0xFF)
        BiasCard.iicBus.write_byte_data(AD5144ADDRTABLE[channel], 0b00010010, (x >> 16) & 0xFF)
        BiasCard.iicBus.write_byte_data(AD5144ADDRTABLE[channel], 0b00010011, (x >> 24) & 0xFF)

    def set_wiper_min(self, channel):
        x = 0
        BiasCard.iicBus.write_byte_data(AD5144ADDRTABLE[channel], 0b00010000, x & 0xFF)
        BiasCard.iicBus.write_byte_data(AD5144ADDRTABLE[channel], 0b00010001, (x >>  8) & 0xFF)
        BiasCard.iicBus.write_byte_data(AD5144ADDRTABLE[channel], 0b00010010, (x >> 16) & 0xFF)
        BiasCard.iicBus.write_byte_data(AD5144ADDRTABLE[channel], 0b00010011, (x >> 24) & 0xFF)

    def init_currsense(self, chan: int, currentDivider: float = 100.0) -> None:
        """Initializes an INA219 current sense chip for a given channel

        Code ripped from https://github.com/adafruit/Adafruit_INA219/blob/master/Adafruit_INA219.cpp

        :param chan: select the bias channel to initialize (1 through 8)
        :type chan: int
        :param currentDivider: useful for cases where sense resistors have been modified, defaults to 2.0
        :type currentDivider: float, optional
        """

        self.ina219_currentDivider_mA = currentDivider
        self.ina219_powerMultiplier_mW = 2

        # Set Calibration register to 'Cal' calculated above
        BiasCard.iicBus.write_word_data(INA219ADDRTABLE[chan], INA219_REG_CALIBRATION, INACALVALUE)
        BiasCard.iicBus.write_word_data(INA219ADDRTABLE[chan], INA219_REG_CONFIG, INA219CONFIG)
        
    def _ina_getCurrent_raw(self, chan):
        BiasCard.iicBus.write_word_data(INA219ADDRTABLE[chan], INA219_REG_CALIBRATION, INACALVALUE)
        val = MSBF(BiasCard.iicBus.read_word_data(INA219ADDRTABLE[chan], INA219_REG_CURRENT))
        val = np.array([val]).astype("int16")[0]
        return val

    def _ina_getPower_raw(self, chan):
        BiasCard.iicBus.write_word_data(INA219ADDRTABLE[chan], INA219_REG_CALIBRATION, INACALVALUE)
        val = MSBF(BiasCard.iicBus.read_word_data(INA219ADDRTABLE[chan], INA219_REG_POWER))
        val = np.array([val]).astype("int16")[0]
        return val

    def _ina_getShuntVoltage_raw(self, chan):
        # BiasCard.iicBus.write_word_data(INA219ADDRTABLE[chan], INA219_REG_CALIBRATION, INACALVALUE)
        val = MSBF(BiasCard.iicBus.read_word_data(INA219ADDRTABLE[chan], INA219_REG_SHUNTVOLTAGE))
        val = np.array([val]).astype("int16")[0]
        return val

    def _ina_getBusVoltage_raw(self, chan):
        BiasCard.iicBus.write_word_data(INA219ADDRTABLE[chan], INA219_REG_CALIBRATION, INACALVALUE)
        val = MSBF(BiasCard.iicBus.read_word_data(INA219ADDRTABLE[chan], INA219_REG_BUSVOLTAGE))
        val = np.array([val]).astype("int16")[0]
        return ( val >> 3 ) * 4  # Shift to the right 3 to drop CNVR and OVF and multiply by LSB

    def get_shunt(self, chan: int, navg: int = 6) -> float:
        """Reads a current monitor for it's shunt voltage for a given channel.
        """
        val = np.zeros(navg)
        for ind, _ in enumerate(val):
            val[ind] = 0.01 * self._ina_getShuntVoltage_raw(chan)
        val = float(np.average(val))
        if val < 0.0:
            return 0.0
        else:
            return val

    def get_bus(self, chan: int, navg: int = 6) -> float:
        """Reads a current monitor for it's bus voltage for a given channel
        """
        val = np.zeros(navg)
        for ind, _ in enumerate(val):
            val[ind] = self._ina_getBusVoltage_raw(chan) * 0.001
        avg = np.average(val)
        return float(avg)

    def get_current(self, chan: int, navg: int = 6) -> float:
        """Reads a current monitor for the bias's current draw for a given channel
        """
        val = np.zeros(navg)
        for ind, _ in enumerate(val):
            val[ind] = self._ina_getCurrent_raw(chan) / (
                self.ina219_currentDivider_mA
            )
        m = float(np.average(val))
        if m < 0.1:
            return 0.0
        else:
            return m

