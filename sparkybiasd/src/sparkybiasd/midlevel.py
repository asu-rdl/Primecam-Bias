from .hardware import BiasCard
import numpy as np
from omegaconf import OmegaConf
from . import dconf
import time

#TODO: Warn user if setting wiper when output is disabled.....

#TODO: save settings to yaml file

#TODO: use logging

#TODO: Deployment script and test suite

# WARNING: NEED TO IMPLEMENT MUTUAL EXCLUSION FOR BIAS CARDS

def grab_board(func):
    """
    Wrapper handles opening and closing of an IIC bus at the card level.
    the card number is converted into a BiasCard instance matching that address.
    self.cards comes from BiasCrate.__init__
    
    Hopefully this isn't a cardinal sin that needs be removed later because of
    complexity issues. 
    """
    def wrapper(self, card:int, *args, **kwargs):
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
        for i in range(1, 18+1):
            try:
                bc = BiasCard(i)
                self.cards[i] = bc
            except OSError: 
                continue
        for c in self.cards:
            print(f"Found card address {c}")


    @grab_board
    def seek_voltage(self, board, channel: int, voltage: float, increment = 1):
        """set channel to specified voltage (in TBD Units)"""
        assert voltage >= 0, "Can't generate negative voltages"
        assert voltage <= 5, "Voltage spec out of range"
        
        wiper = board.wiper_states[channel-1]
        print(board.wiper_states)
        cv = np.round(board.get_bus(channel), 6)
        limit = 2048
        while limit > 0:
            limit -= 1
            time.sleep(0.06) # Allow bus to reach proper voltage
            cv = np.round(board.get_bus(channel), 6)
            delta = np.round(abs(voltage-cv), 6)
            print(f"wiper = {wiper}; cv = {cv}; delta= {delta} ")
            if delta < 0.01:
                break
            
            if (cv-voltage) > 0:
                wiper -= increment
                if wiper < 0: wiper = 0
                board.set_wiper(channel, wiper)
                continue

            if (cv-voltage) < 0:
                wiper += increment
                board.set_wiper(channel, wiper)
                continue
            

        
    @grab_board
    def seek_current(self, card: int, channel: int, current: float, increment = 1):
            """set channel to specified current (in mA Units)"""
            assert current >= 0, "Can't generate negative voltages"
            assert current <= 200, "Voltage spec out of range"
            
            board = self.cards[card]
            wiper = board.wiper_states[channel-1]
            print(board.wiper_states)
            ci = np.round(board.get_bus(channel), 6)
            limit = 2048
            while limit > 0:
                limit -= 1
                time.sleep(0.06) # Allow bus to reach proper current
                ci = np.round(board.get_current(channel), 6)
                delta = np.round(abs(current-ci), 6)
                print(f"wiper = {wiper}; ci = {ci}; delta= {delta} ")
                if delta < 0.01:
                    break
                
                if (ci-current) > 0:
                    wiper -= increment
                    if wiper < 0: wiper = 0
                    board.set_wiper(channel, wiper)
                    continue

                if (ci-current) < 0:
                    wiper += increment
                    board.set_wiper(channel, wiper)
                    continue

    @grab_board
    def disable_output(self, board, channel: int):
        """Disable output of a card+channel"""
        assert channel > 0 and channel <= 8, "Expected Channel 1 through 8"
        board.enable_chan(channel, False)

    @grab_board
    def enable_output(self, board, channel: int):
        """Enable output of a card+channel"""
        assert channel > 0 and channel <= 8, "Expected Channel 1 through 8"
        board.enable_chan(channel)

    def disable_all_outputs(self, zero_digital_pot: bool = False):
        """Disable all outputs in the bias crate"""
        for c in self.cards:
            self.cards[c].open()
            self.cards[c].disable_all_chan()
            if zero_digital_pot:
                for i in range(1, 8+1):
                    self.cards[c].set_wiper_min(i)
            self.cards[c].close()

    def enable_all_outputs(self):
        """enable the outputs in the bias crate"""
        for c in self.cards:
            self.cards[c].open()
            self.cards[c].enable_all_chan()   
            self.cards[c].close()

    def get_availCards(self):
        """List connected cards"""
        return self.cards.keys()

    def save(self):
        raise Exception("config save option not implemented")

    def load(self):
        raise Exception("config save option not implemented")
