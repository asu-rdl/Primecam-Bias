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
import json

APPDATA_PATH = "/home/asu/daemon"
LOGPATH = "/home/asu/daemon/logs"
os.makedirs(APPDATA_PATH, exist_ok=True)
os.makedirs(LOGPATH, exist_ok=True)

import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)
# Logs written out to 4 Megabytes
log_handler = RotatingFileHandler(LOGPATH + "applog.txt", "a", 4_194_304, 5)
LOGFORMAT = "%(asctime)s|%(levelname)s|%(funcName)s|%(message)s"
log_formatter = logging.Formatter(LOGFORMAT)
log_handler.setFormatter(log_formatter)
logging.basicConfig(format=LOGFORMAT, level=logging.DEBUG)
logger.addHandler(log_handler)

class reply:
    def __init__(self):
        self.status = ""
        self.code = 0
        self.errormessage = ""
        self.card = 0
        self.channel = 0
        self.vbus = 0.0
        self.vshunt = 0.0
        self.current = 0.0
        self.outputEnabled = False
        self.wiper = 0
    def success_str(self):
        return json.dumps({
            "status": self.status,
            "card": self.card,
            "channel": self.channel,
            "vbus": self.vbus,
            "vshunt": self.vshunt,
            "current": self.current,
            "outputEnabled": self.outputEnabled,
            "wiper": self.wiper,
        })
    def error_str(self):
        return json.dumps({
            "status": self.status,
            "code": self.code,
            "msg": self.errormessage
        })

def main():

    crate = bias.BiasCrate()
    crate.disable_all_outputs()  # Safety First!

    rinst = redis.Redis(host=conf.redis.ip, port=conf.redis.port)
    try:
        rinst.ping()
    except redis.exceptions.ConnectionError:
        logger.exception("Failed to connect to the redis server")
        exit(-1)

    rpubsub = rinst.pubsub()
    rpubsub.subscribe(conf.redis.commandChannel)  # Is command

    while True:
        msg = rpubsub.get_message(ignore_subscribe_messages=True)
        if msg is not None:
            # suppose we need to parse this?
            data = msg["data"].decode()
            try:
                cmd = json.loads(data)
            except json.JSONDecodeError as e:
                logger.exception(e)
                r = reply(); r.status = "error"; r.code = -1; r.errormessage = "A JSON Parse exception occurred."
                rinst.publish(conf.redis.replyChannel, r.error_str())
                continue;
            
            func = COMMAND_DICT[cmd['command']]
            try:
                rinst.publish(conf.rfsoc.replyChannel, func(cmd["args"]))
            
            except KeyError as e:
                logger.exception(e)
                r = reply(); r.status = "error"; r.code = -2; r.errormessage = "Received bad command"
                rinst.publish(conf.redis.replyChannel, r.error_str())
        

        else:
            # suppose we need to get the state of the hardware
            pass


def get_status(*args):
    pass
def seek_voltage(*args):
    pass
def seek_current(*args):
    pass
def enable_output(*args):
    pass
def disable_output(*args):
    pass


COMMAND_DICT = {
    "seekVoltage" : seek_voltage,
    "seekCurrent": seek_current,
    "getStatus": get_status,
    "enableOutput": enable_output,
    "disableOutput": disable_output
}
