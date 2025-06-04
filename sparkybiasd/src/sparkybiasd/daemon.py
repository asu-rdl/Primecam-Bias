"""
Daemon process. Initializes the boards and waits for commands from the end user. 
These commands arrive redis's pub-sub pipeline as json formatted strings documented
in https://asu-rdl.github.io/Primecam-Bias/software.html.
These strings are converted into 

Those strings are then converted 



"""

from dataclasses import dataclass
import redis
import redis.exceptions
import os
from .midlevel import BiasCrate
from .dconf import conf
import json
USERHOME = os.environ.get("HOME", "")

APPDATA_PATH = USERHOME+"/daemon/"
LOGPATH = USERHOME+"/daemon/logs/"
os.makedirs(APPDATA_PATH, exist_ok=True)
os.makedirs(LOGPATH, exist_ok=True)

import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)
LOGFORMAT = "%(asctime)s|%(levelname)s|%(funcName)s|%(message)s"
logging.basicConfig(format=LOGFORMAT, level=conf.loglevel)
log_handler = RotatingFileHandler(LOGPATH + "applog.txt", "a", 4_194_304, 5)# Logs written out to 4 Megabytes
log_formatter = logging.Formatter(LOGFORMAT)
log_handler.setFormatter(log_formatter)

logger.addHandler(log_handler)

@dataclass
class reply:
    status = ""
    code = 0
    errormessage = ""
    card = 0
    channel = 0
    vbus = 0.0
    vshunt = 0.0
    current = 0.0
    outputEnabled = False
    wiper = 0
    def success_str(self):
        return json.dumps({
            "status": self.status, "card": self.card, "channel": self.channel,
            "vbus": self.vbus, "vshunt": self.vshunt, "current": self.current,
            "outputEnabled": self.outputEnabled, "wiper": self.wiper, })
    def error_str(self):
        return json.dumps({
            "status": self.status, "code": self.code, "msg": self.errormessage
        })

def main():
    logger.debug("Starting the Bias Crate daemon...")

    crate = BiasCrate()
    crate.disable_all_outputs(True)  # Safety First!

    rinst = redis.Redis(host=conf.redis.ip, port=conf.redis.port)
    try:
        rinst.ping()
    except redis.exceptions.ConnectionError:
        logger.exception("Failed to connect to the redis server")
        exit(-1)

    rpubsub = rinst.pubsub()
    rpubsub.subscribe(conf.redis.commandChannel)  # Is command

    for msg in rpubsub.listen():
        if msg["type"] == "subscribe":
            continue
        elif msg["type"] == "unsubscribe":
            continue
        elif msg["type"] == "message":
            logger.debug(f"Received message: {msg}")
            # suppose we need to parse this?
            data = msg["data"].decode()
            try:
                cmd = json.loads(data)
            except json.JSONDecodeError as e:
                logger.exception(e)
                r = reply(); r.status = "error"; r.code = -1; r.errormessage = "A JSON Parse exception occurred."
                rinst.publish(conf.redis.replyChannel, r.error_str())
                continue
            
            cmdstr = cmd["command"]
            if cmdstr in COMMAND_DICT:
                func = COMMAND_DICT[cmdstr]
            else:
                r = reply(); r.status = "error"; r.code = -2; r.errormessage = "Received bad command"
                logger.error(f"Received bad command: {cmdstr}")
                rinst.publish(conf.redis.replyChannel, r.error_str())
                continue
    
            assert func is not None, logger.error("Expected valid function but got none. Thar be weirdness in these waters.")

            results = func(crate, cmd["args"])
            logger.debug(f"results from executed function is {results}")
            rinst.publish(conf.redis.replyChannel, results)
   

        else:
            # suppose we need to get the state of the hardware
            pass

# This is a stub for the command functions. They should be implemented to interact with the BiasCrate.
# They will return a string that is then published to the redis reply channel.
def get_status(crate:BiasCrate, args:dict)->str:
    r = reply()
    card = args['card']
    channel = args['channel']
    r.card = card
    r.channel = channel
    try:
        r.status = "success"
        r.vbus, r.vshunt, r.current, r.outputEnabled, r.wiper = crate.get_status(card, channel)
        return r.success_str()
    except Exception as e:
        logger.exception(e)
        r.status = "error"
        r.code = -3
        r.errormessage = str(e)
        return r.error_str()
def seek_voltage(*args)->str:
    return ""
def seek_current(*args)->str:
    return ""
def enable_output(*args)->str:
    return ""
def disable_output(*args)->str:
    return ""


COMMAND_DICT = {
    "seekVoltage" : seek_voltage,
    "seekCurrent": seek_current,
    "getStatus": get_status,
    "enableOutput": enable_output,
    "disableOutput": disable_output
}
