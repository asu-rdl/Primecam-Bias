"""
Daemon process. Initializes the boards and waits for commands from the end user. While waiting, 
daemon queries all available channels for their current stats and statusses

Inits a redis connection. Subscribe to sparkommand and match a given value to COMMAND_DICT.
Executes a paired function and passes in the args and runs it. Bobs your uncle.j

    {'type': 'message', 'pattern': None, 'channel': b'SHITE', 'data': b'I EAT BURRITOS'}
"""
import redis
from omegaconf import OmegaConf
from . import midlevel as bias
import logging 

def main():

    crate = bias.BiasCrate()
    crate.disable_all_outputs() # Safety First!

    conf = OmegaConf.create({'redisip':"192.168.1.1", 'redisport' : 0000, 'statusRefreshRate': 1 })
    #NOTE: It appears there is a retry method within redis. Where was this last time???? 

    rinst = redis.Redis(host = conf.redisip, port = conf.redisport)
    #TODO:  Are we connected, if so great; else crash out king
    rpubsub = rinst.pubsub()
    rpubsub.subscribe("sparkommand") # Is command Kommrade
    
    # Suppose we should do a main loop; don't want to block since we'll update statuses
    rpubsub.get_message() # Yes we subscribed, don't care though 

    while True:
        msg = rpubsub.get_message()
        if msg is not None:
            # suppose we need to parse this?
            dtype = msg['type'].decode()
            chan = msg['chan'].decode()
            data = msg['data'].decode()
            pass
        else:
            # suppose we need to get the state of the hardware
            pass
            
def updateStatus():
    """Iterate through all of the bias cards, grab their stats and publish to redis."""
    pass
    
def version(*args):
    """Get version I suppose"""
    pass
    
def findV(*args):
    """Self explanitory


    What do I need to know? 
        board
        channel
        desired voltage
        
    """
    pass

def findI(*args):
    pass
    
COMMAND_DICT = {
    'version': version,
    'findV': findV,
    'findI': findI
}
