"""

Implements a Bias Crate Daemon that listens to a redis pub-sub channel for commands
and executes them. 
Functions defined in midlevel.py handle the actual execution of system-wide commands such as seeking voltages, 
enabling outputs, etc. 

hardware.py implements the low-level hardware interaction with the individual cards within the bias crate.

All commands are expected to be in the form of a json formatted string, which is
parsed and validated before execution. The results of the command execution are then
published back to a redis reply channel as a json formatted string.
See the documentation for the available commands and their expected arguments
in https://asu-rdl.github.io/Primecam-Bias/software.html or Primecam-Bias/docs/software.md

This has been setup to run as a systemd service, and will automatically start on boot.

Redis is simply used to broker the communication between a client and the daemon. In theory, it should be 
fairly straightforward to replace redis with some other pub-sub system or perhaps even a direct socket connection.

"""

from dataclasses import dataclass

from .dconf import conf, CONFIGPATH, LOGPATH
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)

LOGFORMAT = "%(asctime)s|%(levelname)s|%(module)s|%(funcName)s|%(message)s"
logging.basicConfig(format=LOGFORMAT, level=conf.loglevel)
log_handler = RotatingFileHandler(LOGPATH + "applog.txt", "a", 4_194_304, 5)# Logs written out to 4 Megabytes
log_formatter = logging.Formatter(LOGFORMAT)
log_handler.setFormatter(log_formatter)

logger.addHandler(log_handler)
logger.getChild("dconf").addHandler(log_handler)
logger.getChild("midlevel").addHandler(log_handler)


import redis
import redis.exceptions
import os
from .midlevel import BiasCrate

from omegaconf import OmegaConf
import json
import time


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
    """Valudate the command data against the expected structure, and parameters."""
    rep = reply()

    if not isinstance(command_data, dict):
        rep.status = "error"
        rep.code = -3
        rep.errormessage = "Command data must be a dictionary"
        return False, rep
    if 'command' not in command_data or 'args' not in command_data:
        rep.status = "error"
        rep.code = -4
        rep.errormessage = "Command data must contain 'command' and 'args' keys"
        return False, rep
    if not isinstance(command_data['args'], dict):
        rep.status = "error"
        rep.code = -5
        rep.errormessage = "'args' must be a dictionary"
        return False, rep
    command = command_data['command']
    if command not in COMMAND_TABLE:
        rep.status = "error"
        rep.code = -6
        rep.errormessage = f"Command '{command}' not recognized"
        return False, rep
    expected_args = COMMAND_TABLE[command]['args']
    
    for arg in expected_args:
        if arg not in command_data['args']:
            rep.status = "error"
            rep.code = -7
            rep.errormessage = f"Missing argument '{arg}' for command '{command}'"
            return False, rep
        
    if 'card' in expected_args and 'card' in command_data['args']:
        if command_data['args']['card'] < 1 or command_data['args']['card'] > 18:
            rep.status = "error"
            rep.code = -8
            rep.errormessage = "Card number must be between 1 and 18"
            return False, rep
    if 'channel' in expected_args and 'channel' in command_data['args']:
        if command_data['args']['channel'] < 1 or command_data['args']['channel'] > 8:
            rep.status = "error"
            rep.code = -9
            rep.errormessage = "Channel number must be between 1 and 8"
            return False, rep
    return True, rep


def main():
    """Main run loop for the Bias Crate Daemon."""
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
                # Validate the command structure and content
                command_is_valid, response = validate_command(command)
                if command_is_valid:
                    command_name = command['command']
                    args = command['args']
                    func = COMMAND_TABLE[command_name]['function']
                    try:
                        response = func(crate, args)
                        logger.info(f"Execution of {command_name} completed.")
                    except Exception as e:
                        logger.exception(f"Error executing command {command_name}: {e}")
                        response = reply()
                        response.status = "error"
                        response.code = -1
                        response.errormessage = str(e)
                        response = response.error_str()

                    logger.debug(f"Response: {response}")
                    r.publish(conf.redis.replyChannel, response)

                else:
                    logger.error(response.errormessage)
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
        r.vbus, r.vshunt, r.current, r.outputEnabled, r.wiper = crate.get_status(card, channel)
        r.status = "success"
        return r.success_str()
    except Exception as e:
        logger.exception(e)
        r.status = "error"
        r.code = -99
        r.errormessage = str(e)
        return r.error_str()
    
def seek_voltage(crate:BiasCrate, args:dict)->str:
    r = reply()
    card = args['card']
    channel = args['channel']

    r.card = card
    r.channel = channel
    try:
        voltage = args['voltage']
        r.vbus, r.vshunt, r.current, r.outputEnabled, r.wiper = crate.get_status(card, channel)
        if r.outputEnabled:
            crate.seek_voltage(card, channel, voltage)
        else:
            r.status = "error"
            r.code = -32000
            r.errormessage = "Output is disabled, cannot seek voltage."
            return r.error_str()
        time.sleep(0.2)  # Allow time for the voltage to settle
        r.vbus, r.vshunt, r.current, r.outputEnabled, r.wiper = crate.get_status(card, channel)
        r.status = "success"
    except Exception as e:
        logger.exception(e)
        r.status = "error"
        r.code = -100 #TODO: Define error codes
        r.errormessage = str(e)
        return r.error_str()
    return r.success_str()

def seek_current(crate:BiasCrate, args:dict)->str:
    r = reply()
    card = args['card']
    channel = args['channel']
   
    r.card = card
    r.channel = channel
    try:
        current = args['current']
        r.vbus, r.vshunt, r.current, r.outputEnabled, r.wiper = crate.get_status(card, channel)
        if r.outputEnabled:
            crate.seek_current(card, channel, current)
        else:
            r.status = "error"
            r.code = -33000
            r.errormessage = "Output is disabled, cannot seek current."
            return r.error_str()
        time.sleep(0.2)  # Allow time for the current to settle
        r.vbus, r.vshunt, r.current, r.outputEnabled, r.wiper = crate.get_status(card, channel)
        r.status = "success"
    except Exception as e:
        logger.exception(e)
        r.status = "error"
        r.code = -33100 #TODO: Define error codes
        r.errormessage = str(e)
        return r.error_str()
    return r.success_str()


def enable_output(crate: BiasCrate, args:dict)->str:
    r = reply()
    card = args['card']
    channel = args['channel']
    
    r.card = card
    r.channel = channel
    try:
        crate.enable_output(card, channel)
        time.sleep(0.1)  # Allow time for the output to settle
        r.vbus, r.vshunt, r.current, r.outputEnabled, r.wiper = crate.get_status(card, channel)
        r.status = "success"
    except Exception as e:
        logger.exception(e)
        r.status = "error"
        r.code = -100 #TODO: Define error codes
        r.errormessage = str(e)
        return r.error_str() 
    return r.success_str()  


def disable_output(crate: BiasCrate, args:dict)->str:
    r = reply()
    card = args['card']
    channel = args['channel']
   
    r.card = card
    r.channel = channel
    try:
        crate.disable_output(card, channel)
        time.sleep(0.1)  # Allow time for the output to settle
        r.vbus, r.vshunt, r.current, r.outputEnabled, r.wiper = crate.get_status(card, channel)
        r.status = "success"
    except Exception as e:
        logger.exception(e)
        r.status = "error"
        r.code = -107 #TODO: Define error codes
        r.errormessage = str(e)
        return r.error_str() 
    return r.success_str() 


def enable_testload(crate: BiasCrate, args:dict)->str:
    r = reply()
    card = args['card']
    channel = args['channel']
    
    r.card = card
    r.channel = channel
    try:
        crate.enable_testload(card, channel)
        time.sleep(0.1)  # Allow time for the output to settle
        r.vbus, r.vshunt, r.current, r.outputEnabled, r.wiper = crate.get_status(card, channel)
        r.status = "success"
    except Exception as e:
        logger.exception(e)
        r.status = "error"
        r.code = -100 #TODO: Define error codes
        r.errormessage = str(e)
        return r.error_str() 
    return r.success_str()  


def disable_testload(crate: BiasCrate, args:dict)->str:
    r = reply()
    card = args['card']
    channel = args['channel']
   
    r.card = card
    r.channel = channel
    try:
        crate.disable_testload(card, channel)
        time.sleep(0.1)  # Allow time for the output to settle
        r.vbus, r.vshunt, r.current, r.outputEnabled, r.wiper = crate.get_status(card, channel)
        r.status = "success"
    except Exception as e:
        logger.exception(e)
        r.status = "error"
        r.code = -1047 #TODO: Define error codes
        r.errormessage = str(e)
        return r.error_str() 
    return r.success_str() 

def get_available_cards(crate: BiasCrate, args:dict)->str:
    """Get a list of available cards."""
    r = {
        "status": "success",
        "cards": [],
    }
    try:
        r["status"] = "success"
        r["cards"] = crate.get_avail_cards()
    except Exception as e:
        logger.exception(e)
        r = reply()
        r.status = "error"
        r.code = -100 #TODO: Define error codes
        r.errormessage = str(e)
        return r.error_str()
    return json.dumps(r)

def load_config(crate: BiasCrate, args:dict):
    """
    Load the configuration from the configuration file into the Bias Crate.
    This will overwrite the current configuration in the Bias Crate with the values
    from the configuration file.

    This can be dangerous if the configuration file is not correct, as it may
    set incorrect voltages or currents on the Bias Crate channels. 
    """
    r = reply()
    enable_outputs = args.get("enableOutputs", False)
    create_new_config = args.get("createNewConfig", False)
    if not isinstance(enable_outputs, bool):
        r.status = "error"
        r.code = -202
        r.errormessage = "enableOutputs must be a boolean value."
        return r.error_str()
    if not isinstance(create_new_config, bool):
        r.status = "error"
        r.code = -203
        r.errormessage = "createNewConfig must be a boolean value."
        return r.error_str()
    if create_new_config:
        logger.debug("Creating new configuration file.")
        OmegaConf.save(conf, CONFIGPATH+"config.yaml")
    else:
        logger.debug("Will not create a new config file, attempting to load existing one.")
        if not os.path.exists(CONFIGPATH):
            r.status = "error"
            r.code = -101
            r.errormessage = f"Configuration file {CONFIGPATH} does not exist."
            return r.error_str()

    try:
        crate.load_config(enable_outputs)
        r.status = "success"
        return r.success_str()
    except Exception as e:
        logger.exception(e)
        r.status = "error"
        r.code = -100
        r.errormessage = str(e)

def save_config(crate: BiasCrate, args:dict):
    """
    Save the current configuration of the Bias Crate to the configuration file.

    TBD: configPath argument may be dangerous as it may be used to write to an arbitrary location.
        Remove the ability to specify a full path, only a filename should be allowed. Not very important, impl later.
    """
    r = reply()
        
    try:
        # if 'configPath' in args:
        #     config_path = args['configPath']
        #     if not os.path.exists(os.path.dirname(config_path)):
        #         os.makedirs(os.path.dirname(config_path), exist_ok=True)

        crate.save_config()
        r.status = "success"
    except Exception as e:
        logger.exception(e)
        r.status = "error"
        r.code = -100
        r.errormessage = str(e)
        return r.error_str()
    return r.success_str()

def disable_all_outputs(crate: BiasCrate, args:dict):
    """
    Disable all outputs on the Bias Crate. 
    This also sets the output voltages and currents to zero.
    """
    r = reply()
    try:
        crate.disable_all_outputs(True)
        r.status = "success"
    except Exception as e:
        logger.exception(e)
        r.status = "error"
        r.code = -10000
        r.errormessage = str(e)
        return r.error_str()
    return r.success_str()


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
    },
    "enableTestload": {
        "function": enable_testload,
        "args": ["card", "channel"]
    },
    "disableTestload": {
        "function": disable_testload,
        "args": ["card", "channel"]
    },
    "getAvailableCards": {
        "function": get_available_cards,
        "args": []
    },
    "loadConfig": {
        "function": load_config,
        "args": ["enableOutputs", "createNewConfig"]
    },
    "saveConfig": {
        "function": save_config,
        "args": []
    },
    "disableAllOutputs": {
        "function": disable_all_outputs,
        "args": []
    }

}


if __name__ == "__main__":
    main()