from .hardware import BiasCard
import numpy as np
from omegaconf import OmegaConf
from  .dconf import conf
from .dconf import CONFIGPATH
import time
import logging

logger = logging.getLogger(__name__)

logger.debug(f"module {__name__} loaded")
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
        try:
            board.open()
            res = func(self, board, *args, **kwargs)
            board.close()
        except Exception as e:
            board.close()
            raise e
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
    def disable_output(self, board: BiasCard, channel: int, zero_wiper: bool = False):
        """Disable output of a card+channel"""
        assert channel > 0 and channel <= 8, "Expected Channel 1 through 8"
        board.enable_chan(channel, False)
        if zero_wiper:
            logger.debug(f"Zeroing wiper for card {board.address}, channel {channel}")
            board.set_wiper_min(channel)

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

        # Check on all of the cards that could (or should) be present in the system.
        for i in range(1, 18 + 1):
            # If the card isn't already known, try to create it and see if it exists.
            if i not in self.cards:
                try:
                    card = BiasCard(i)
                    self.cards[i] = card
                    logger.warning(f"Card {i} was not previously known, but has been found in the system.")
                except OSError:
                    logger.debug(f"Card {i} not found in system")
                    continue
            else:
                # Otherwise test that the card is still available and responding.
                try:
                    self.cards[i].open()
                    self.cards[i].close()
                except OSError:
                    logger.error(f"Card {i} no longer found in systemm, what happened?")
                    raise Exception(f"Card {i} no longer found in system, what happened?")

        available_cards = []
        for c in self.cards:
            available_cards.append(c)
        logger.debug(f"Available cards: {available_cards}")
        return available_cards

    def save_config(self, config_path: str = CONFIGPATH+"config.yaml"):
        """
        Save the current configuration to the yaml file. Defaults
        to `$HOME/daemon/config.yaml`. This will save the current state of the BiasCards
        to the configuration file. All paths specified will be relative to `$HOME/daemon/`
        """

        try:
            # Iterate through all configured cards
            # There are 18 possible cards, but some may not be present in the system.
        
            for i in range(1, 18 + 1):
                if i not in self.cards:
                    logger.info(f"Card {i} not found in system, skipping configuration.")
                    continue
                card = f"card{i}"
                for j in range(1, 8 + 1):
                    chan = f"chan{j}"
                    conf.biasCards[card][chan] = {
                        "output": self.cards[i].is_chan_enabled(j),
                        "wiper": self.cards[i].wiper_states[j - 1]
                    }
            OmegaConf.save(conf, config_path)


        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise e

    def load_config(self, enable_outputs: bool = True):
        """Load config from yaml file, apply settings to the cards.
        There is a flag called enable_outputs that will enable the outputs
        of the channels if set to True in config. If set to False, the outputs will be disabled regardless
        of the configuration in the YAML file. 
        The wipers however, will always be set to the configured value in the YAML file.

        """
        logger.info("Loading configuration from YAML file...")
        conf = OmegaConf.load(CONFIGPATH+"config.yaml")

        try:
            # Iterate through all configured cards
            # If the cards is present in the conf, but not the system, skip it
            # TODO: Need config validation. 
        
            for i in range(1, 18 + 1):
                if i not in self.cards:
                    logger.debug(f"Card {i} not found in system, skipping configuration.")
                    continue
                card = f"card{i}"
                logger.debug(f"Open card {i} for configuration")

                self.cards[i].open()
                for j in range(1, 8 + 1):
                    chan = f"chan{j}"

                    chan_setting = conf.biasCards[card][chan]
                    output = chan_setting.get("output", False)
                    wiper = chan_setting.get("wiper", 0)
                    if output and enable_outputs:
                        logger.debug(f"Enabling output for card {i}, channel {j} with wiper {wiper}")
                        self.cards[i].enable_chan(j)
                    else:
                        logger.debug(f"Disabling output for card {i}, channel {j}")
                        self.cards[i].enable_chan(j, False)
                    logger.debug(f"Setting wiper for card {i}, channel {j} to {wiper}")

                    
                    self.cards[i].set_wiper(j, wiper)
                self.cards[i].close()

                    
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise e