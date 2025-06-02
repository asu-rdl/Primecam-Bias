"""
Daemon process. Initializes the boards and waits for commands from the end user. While waiting, 
daemon queries all available channels for their current stats and statusses

Inits a redis connection. Subscribe to sparkommand and match a given value to COMMAND_DICT.
Executes a paired function and passes in the args and runs it. Bobs your uncle.

"""
import redis
import redis.exceptions
import os
from . import midlevel as bias
from .dconf import conf

APPDATA_PATH = "/home/asu/daemon"
LOGPATH = "/home/asu/daemon/logs"
os.makedirs(APPDATA_PATH, exist_ok=True)
os.makedirs(LOGPATH, exist_ok=True)

import logging 
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)
# Logs written out to 4 Megabytes
log_handler = RotatingFileHandler(LOGPATH+"applog.txt", 'a', 4_194_304, 5)
LOGFORMAT=	"%(asctime)s|%(levelname)s|%(funcName)s|%(message)s"
log_formatter = logging.Formatter(LOGFORMAT)
log_handler.setFormatter(log_formatter)
logging.basicConfig(format=LOGFORMAT, level=logging.DEBUG)
logger.addHandler(log_handler)

def main():

    crate = bias.BiasCrate()
    crate.disable_all_outputs() # Safety First!

    rinst = redis.Redis(host = conf.redis.ip, port = conf.redis.port)
    try:
        rinst.ping()
    except redis.exceptions.ConnectionError:
        logger.exception("Failed to connect to the redis server")
        exit(-1)

    rpubsub = rinst.pubsub()
    rpubsub.subscribe(conf.redis.commandChannel) # Is command 
    
    while True:
        msg = rpubsub.get_message(ignore_subscribe_messages=True)
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
