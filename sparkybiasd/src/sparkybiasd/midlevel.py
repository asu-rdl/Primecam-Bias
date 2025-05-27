from .hardware import BiasCard
import numpy as np
from omegaconf import OmegaConf
from . import dconf
import time

#TODO: Warn user if setting wiper when output is disabled.....

#TODO: save settings to yaml file

#TODO: use logging

#TODO: Deployment script and test suite

class BiasCrate:
    def __init__(self):
        self.cards: list[BiasCard] = []
        self.config = dconf.gen()
        for i in range(1, 18+1):
            try:
                bc = BiasCard(i)
        
                bc.close()
                    
                self.cards.append(bc)
            except OSError:
                print(f"Warning, Address {i} couldn't be reached.")
        

    def seek_voltage(self, card: int, channel: int, voltage: float, increment = 1):
        """set channel to specified voltage (in TBD Units)"""
        assert voltage >= 0, "Can't generate negative voltages"
        assert voltage <= 5, "Voltage spec out of range"
        
        board = self.cards[card-1]
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
            

        
    def seek_current(self, card: int, channel: int, current: float, increment = 1):
            """set channel to specified current (in mA Units)"""
            assert current >= 0, "Can't generate negative voltages"
            assert current <= 200, "Voltage spec out of range"
            
            board = self.cards[card-1]
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

    def disable_output(self, card: int, channel: int):
        """Disable output of a card+channel"""
        board = self.cards[card-1]
        board.enable_chan(channel, False)
        
    def enable_output(self, card: int, channel: int):
        """Enable output of a card+channel"""
        board = self.cards[card-1]
        board.enable_chan(channel)
        
    def disable_all_outputs(self):
        """Disable all outputs in the bias crate"""
        for c in self.cards:
            c.disable_all_chan()
            
    def enable_all_outputs(self):
        """enable the outputs in the bias crate"""
        for c in self.cards:
            c.enable_all_chan()   
        
    def list_cards(self):
        """List connected cards"""
        

    def save(self, cfgfile: str):
        """save state of crate to config"""
        OmegaConf.save(self.config, cfgfile)


    def load(self, cfgfile: str):
        """load settings from config file and apply

          card1:
            chan1:
              output = false
              wiper = 0
            chan8:
              output = false
              wiper = 0

        """
        conf = OmegaConf.load(cfgfile)
        for card in range(1,18+1):
            for chan in range(1, 8+1):
                en    = conf[f"card{card}"][f"chan{chan}"]["output"]
                wiper = conf[f"card{card}"][f"chan{chan}"]["wiper"]
                self.cards[card].set_wiper(chan, wiper)
                self.cards[card].enable_chan(chan, en)

