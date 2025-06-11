from .hardware import BiasCard
import numpy as np
from omegaconf import OmegaConf
from . import dconf
import time
import logging
logger = logging.getLogger(__name__)
# TODO: Warn user if setting wiper when output is disabled.....

# TODO: save settings to yaml file



def grab_board(func):
    """
    Wrapper handles opening and closing of an IIC bus at the card level.
    the card number is converted into a BiasCard instance matching that address.
    self.cards comes from BiasCrate.__init__

    Hopefully this isn't a cardinal sin that needs be removed later because of
    complexity issues.
    """

    def wrapper(self, card: int, *args, **kwargs):
        if card not in self.cards:
            raise Exception(f"Card {card} not found in BiasCrate")
        board = self.cards[card]
        board.open()
        res = func(self, board, *args, **kwargs)
        board.close()
        return res

    return wrapper


class BiasCrate:
    def __init__(self):
        """
        Repesents the collection of BiasCards within the BiasCrate. Implements the high level
        functions the user may want to use. For future me or other users: If you add more functions,
        simply add the grab_board decorator and supply the parameters self, board, channel.
        """
        self.cards: dict[int, BiasCard] = {}
        self.config = {}
        for i in range(1, 18 + 1):
            try:
                bc = BiasCard(i)
                self.cards[i] = bc
            except OSError:
                continue

    @grab_board
    def seek_voltage(self, board: BiasCard, channel: int, voltage: float, increment=1):
        """set channel to specified voltage (in TBD Units)"""
        assert voltage >= 0, "Can't generate negative voltages"
        assert voltage <= 5, "Voltage spec out of range"
        assert channel > 0 and channel <= 8, "Expected Channel 1 through 8"
        assert increment > 0, "Increment must be a positive integer"
        logger.info(f"Seeking voltage {voltage} on channel {channel}. This may take a while.")
        wiper = board.wiper_states[channel - 1]
        logger.debug(f"Current wiper states: {board.wiper_states}")
        cv = np.round(board.get_bus(channel), 6)
        limit = 2048
        while limit > 0:
            limit -= 1
            time.sleep(0.06)  # Allow bus to reach proper voltage
            cv = np.round(board.get_bus(channel), 6)
            delta = np.round(abs(voltage - cv), 6)
            logger.debug(f"wiper = {wiper}; cv = {cv}; delta= {delta} ")
            if delta < 0.01:
                break

            if (cv - voltage) > 0:
                wiper -= increment
                if wiper < 0:
                    wiper = 0
                board.set_wiper(channel, wiper)
                continue

            if (cv - voltage) < 0:
                wiper += increment
                board.set_wiper(channel, wiper)
                continue

    @grab_board
    def seek_current(self, board: BiasCard, channel: int, current: float, increment=1):
        """set channel to specified current (in mA Units)"""
        assert current >= 0, "Can't generate negative voltages"
        assert current <= 200, "Voltage spec out of range"
        assert channel > 0 and channel <= 8, "Expected Channel 1 through 8"
        assert increment > 0, "Increment must be a positive integer"
        logger.info(f"Seeking current {current} on channel {channel}. This may take a while...")
        wiper = board.wiper_states[channel - 1]
        logger.debug(f"Current wiper states: {board.wiper_states}")
        ci = np.round(board.get_bus(channel), 6)
        limit = 2048
        while limit > 0:
            limit -= 1
            time.sleep(0.06)  # Allow bus to reach proper current
            ci = np.round(board.get_current(channel), 6)
            delta = np.round(abs(current - ci), 6)
            logger.debug(f"wiper = {wiper}; ci = {ci}; delta= {delta} ")
            if delta < 0.01:
                break

            if (ci - current) > 0:
                wiper -= increment
                if wiper < 0:
                    wiper = 0
                board.set_wiper(channel, wiper)
                continue

            if (ci - current) < 0:
                wiper += increment
                board.set_wiper(channel, wiper)
                continue

    @grab_board
    def disable_output(self, board: BiasCard, channel: int):
        """Disable output of a card+channel"""
        assert channel > 0 and channel <= 8, "Expected Channel 1 through 8"
        board.enable_chan(channel, False)

    @grab_board
    def enable_output(self, board: BiasCard, channel: int):
        """Enable output of a card+channel"""
        assert channel > 0 and channel <= 8, "Expected Channel 1 through 8"
        board.enable_chan(channel)

    @grab_board
    def disable_testload(self, board: BiasCard, channel: int):
        """Disable test-load of a card+channel"""
        assert channel > 0 and channel <= 8, "Expected Channel 1 through 8"
        board.enable_testload(channel, False)

    @grab_board
    def enable_testload(self, board: BiasCard, channel: int):
        """Enable testload of a card+channel"""
        assert channel > 0 and channel <= 8, "Expected Channel 1 through 8"
        board.enable_testload(channel)

    @grab_board
    def get_status(self, board:BiasCard, channel: int) -> tuple:
        """Get the status of a card+channel"""
        assert channel > 0 and channel <= 8, "Expected Channel 1 through 8"
        vbus = board.get_bus(channel)
        time.sleep(0.01)  # Allow bus to settle
        vshunt = board.get_shunt(channel)
        time.sleep(0.01)  # Allow bus to settle
        current = board.get_current(channel)
        time.sleep(0.01)  # Allow bus to settle
        OutputEnabled = board.is_chan_enabled(channel)
        wiper = board.wiper_states[channel - 1]
        return vbus, vshunt, current, OutputEnabled, wiper

    def disable_all_outputs(self, zero_digital_pot: bool = False):
        """Disable all outputs in the bias crate"""
        for c in self.cards:
            self.cards[c].open()
            self.cards[c].disable_all_chan()
            if zero_digital_pot:
                for i in range(1, 8 + 1):
                    self.cards[c].set_wiper_min(i)
            self.cards[c].close()

    def max_output(self):
        """Set Wipers to max output"""
        for c in self.cards:
            self.cards[c].open()
            for i in range(1, 8 + 1):
                self.cards[c].set_wiper_max(i)
            self.cards[c].close()

    def min_output(self):
        """Set Wipers to min output"""
        for c in self.cards:
            self.cards[c].open()
            for i in range(1, 8 + 1):
                self.cards[c].set_wiper_min(i)
            self.cards[c].close()

    def enable_all_outputs(self):
        """enable the outputs in the bias crate"""
        for c in self.cards:
            self.cards[c].open()
            self.cards[c].enable_all_chan()
            self.cards[c].close()

    def enable_all_testloads(self):
        """enable the outputs in the bias crate"""
        for c in self.cards:
            self.cards[c].open()
            self.cards[c].enable_all_testloads()
            self.cards[c].close()

    def disable_all_testloads(self):
        """enable the outputs in the bias crate"""
        for c in self.cards:
            self.cards[c].open()
            self.cards[c].disable_all_testloads()
            self.cards[c].close()

    def get_avail_cards(self):
        """List connected cards"""

        #TODO: Should actually refresh the list of cards then return what we already have. 
        # It's possible that a card was removed or added since the BiasCrate was initialized.
        available_cards = []
        for c in self.cards:
            available_cards.append(c)
        logger.debug(f"Available cards: {available_cards}")
        return available_cards

    def save(self):
        raise Exception("config save option not implemented")

    def load(self):
        raise Exception("config save option not implemented")
