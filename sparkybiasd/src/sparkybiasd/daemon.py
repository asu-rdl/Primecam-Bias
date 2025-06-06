"""
Daemon process. Initializes the boards and waits for commands from the end user. 
These commands arrive redis's pub-sub pipeline as json formatted strings documented
in https://asu-rdl.github.io/Primecam-Bias/software.html.



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


def validate_command(command_data) -> bool:
    """Valudate the command data against the expected structure."""
    if not isinstance(command_data, dict):
        return False
    if 'command' not in command_data or 'args' not in command_data:
        return False
    if not isinstance(command_data['args'], dict):
        return False
    command = command_data['command']
    if command not in COMMAND_TABLE:
        return False
    expected_args = COMMAND_TABLE[command]['args']
    for arg in expected_args:
        if arg not in command_data['args']:
            return False
    return True


def main():
    """Main function to run the daemon."""
    logger.info("Starting Bias Crate Daemon")
    crate = BiasCrate()
    logger.info("Bias Crate Daemon started successfully")

    r = redis.Redis(host=conf.redis.ip, port=conf.redis.port, db=0)
    pubsub = r.pubsub()
    pubsub.subscribe(conf.redis.commandChannel)

    try:
        for message in pubsub.listen():
            if message['type'] == 'message':
                command = json.loads(message['data'].decode())
                logger.info(f"Received command: {command}")
                if validate_command(command):
                    command_name = command['command']
                    args = command['args']
                    func = COMMAND_TABLE[command_name]['function']
                    try:
                        response = func(crate, args)
                        logger.info(f"Command {command_name} executed successfully")
                    except Exception as e:
                        logger.exception(f"Error executing command {command_name}: {e}")
                        response = reply()
                        response.status = "error"
                        response.code = -1
                        response.errormessage = str(e)
                    r.publish(conf.redis.replyChannel, response)

                else:
                    logger.error("Invalid command structure or command not found")
                    response = reply()
                    response.status = "error"
                    response.code = -2
                    response.errormessage = "Invalid command"
                    r.publish(conf.redis.replyChannel, response.error_str())

                


    except redis.exceptions.ConnectionError as e:
        logger.error(f"Redis connection error: {e}")
    finally:
        pubsub.unsubscribe()
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
        r.code = -99
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



# The command table maps command names to their corresponding functions and arguments.
# This allows for dynamic command execution based on the received command.
COMMAND_TABLE = {
    "seekVoltage" : {
        "function": seek_voltage,
        "args": ["card", "channel", "voltage"]
    },
    "seekCurrent":{
        "function": seek_current,
        "args": ["card", "channel", "current"]
    },
    "getStatus": {
        "function": get_status,
        "args": ["card", "channel"]
    }, 
    "enableOutput": {
        "function": enable_output,
        "args": ["card", "channel"]
    },
    "disableOutput": {
        "function": disable_output,
        "args": ["card", "channel"]
    }
}
