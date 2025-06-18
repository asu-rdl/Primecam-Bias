---
layout: default
---
# Software Documentation


1. [Considerations](#Considerations) 
1. [Design](#Design)
    1. [Structure](#Structure)
    1. [Status](#Status)
    1. [Commanding](#Commanding)
        1. [Seek Voltage](#CommandSeekVoltage)
        1. [Seek Current](#CommandSeekCurrent)
        1. [Get Status](#CommandGetStatus)
        1. [Enable Output](#CommandEnableOutput)
        1. [Disable Output](#CommandDisableOutput)
        1. [Enable Testload](#CommandEnableTestLoad)
        1. [Disable Testload](#CommandDisableTestLoad)
        1. [Get Available Cards](#CommandGetAvailableCards)
        1. [Load Config](#CommandLoadConfig)
        1. [Save Config](#CommandSaveConfig)

    1. [Configuration](#Configuration)
    1. [Logs](#Logs)

<a name="Considerations"></a>
# Considerations 

- The software is called Sparky(ASU's mascot) Bias Daemon or sparkybiasd 
- The code should be easy for others to modify and use.
- The software shall run as a "Hands Off" daemon on the PI at startup; managed by [systemd](https://manpages.org/systemd).
    - An assumption was made that redis was being used to handle the readout system.
      Therefore, it would be reasonable to use that for bias control.
        - Implemented redis based control. User can set what the system subscribes to in the config file.
    - Using a raw socket is probably another option...
- The software shall generate a log file when running as a system service.
- The software should be easy for the end user to update. 
    - We will generate a python package so it can be installed and updated with pip.
-  A tool called [poetry](https://python-poetry.org/docs/) is used for package dependency management and package generation.


<a name="Design"></a>
# Design
---
<a name="Structure"></a>
## Structure
The software is essentially a python library with a main() function. The library can be imported and custom code can be written on top if the end user
wishes to do so. Otherwise, a systemd service defined in `/etc/systemd/system/sparkybiasd.service` is used run a script `/etc/run-sparkybiasd`. This 
which in turn, spawns a python interpreter that runs the aforementioned main() function. The interpreter uses a python virtual environment located at `/home/asu/.venv/bin/`.
The top most layer of the library is `daemon.py`. This has a few tasks. It sets up the redis connection and grabs messages from redis pubsub.
It then validates the overall structure of the command and if possible, executes the provided command. It then encapsulates the results of the command
in a reply message. 

`midlevel.py` implements the high level seek functions as well as crate wide output enables and disables. This unit handles all of the connected
cards in the system. This functionality is housed under the class `BiasCrate`

`hardware.py` implements the low level operations of a bias card. This handles communication, setting registers, and keeping track of certain states.
The functionality here is housed under the class `BiasCard`
BiasCrate inits a number of these BiasCard objects. 

<img src="swdiagram.png">

<a name="Commanding"></a>
## Commanding
Commands are communicated to the bias supply as json objects converted to strings. Those strings are 
passed around via Redis. Although redis is being used as a message carrier in this case, it can easily be modified 
and replaced with a simple raw socket or a message broker like RabbitMQ. You would more or less replace the: connection, get message, and send message
portion of daemon.main(). main() is the only place in the code where a message is transmitted or received.
Below are the available commands and an example of their expected format. 

<a name="CommandSeekVoltage"></a>
### Command - Seek Voltage.
Seeks a voltage for a given card, channel. An acceptable range is between 0 and 4.5.
You should expect to see vbus at or around the desired setting. 
**It's important to note that this function requires that the output be enabled. Otherwise, you will read zero when you aren't expecting to.**
```json
{
    "command": "seekVoltage",
    "args": {
        "card": 1,
        "channel": 1,
        "voltage": 2.33
    }
}
```

<a name="CommandSeekCurrent"></a>
### Command - Seek Current.
Seeks a current for a given card, channel. An acceptable range is between 0 and TBD.
You should see that current is at or around the desired setting.

**It's important to note that this function requires that the output be enabled. Otherwise, you will read zero when you aren't expecting to.**
```json
{
    "command": "seekCurrent",
    "args": {
        "card": 1,
        "channel": 1,
        "current": 0.2
    }
}
```

<a name="CommandGetStatus"></a>
### Command - Get Status
Get the status of a specified card


```json
{
    "command": "getStatus",
    "args": {
        "card": 1,
        "channel": 1,
    }
}
```

<a name="CommandEnableOutput"></a>
### Command - Enable Output 
Enable a card's output

```json
{
    "command": "enableOutput",
    "args": {
        "card": 1,
        "channel": 1,
    }
}
```

<a name="CommandDisableOutput"></a>
### Command - Disable Output 
Disables a card's output

```json
{
    "command": "disableOutput",
    "args": {
        "card": 1,
        "channel": 1,
    }
}
```
<a name="CommandEnableTestLoad"></a>
### Command - Enable Testload 
Enable a card's test load. Every channel of every BiasCard has a self test, 51 ohm, dummy load that can be enabled to verify that
the card/channel is operating correctly. **It's important to note that this function requires that the output be enabled. Otherwise, you will read zero when you aren't expecting to.**

```json
{
    "command": "enableTestload",
    "args": {
        "card": 1,
        "channel": 1,
    }
}
```

<a name="CommandDisableTestLoad"></a>
### Command - Disable Test Load 
Disables a card's test load

```json
{
    "command": "disableTestload",
    "args": {
        "card": 1,
        "channel": 1,
    }
}
```

<a name="CommandGetAvailableCards"></a>
### Command - Get Available Cards
Enumerates the BiasCards in the system that can be commanded. If a card is found, it's added to a list of commandable cards.
```json
{
    "command": "getAvailableCards",
    "args": {}
}
```

<a name="CommandLoadConfig"></a>
### Command - Load Config
Loads the saved state of the BiasCrate. This would be the state of the regulators as well as which outputs are enabled.
If `enableOutputs` is set to false, then the state of the outputs is ignored and they are disabled. If it's set to true,
the the outputs are set to what was configured. The config file loaded is `/home/asu/daemon/config.yaml`
```json
{
    "command": "loadConfig",
    "args": {
        "enableOutputs": true,
        "createNewConfig": false,
    }
}
```

<a name="CommandSaveConfig"></a>
### Command - Save Config
Saves the state of the BiasCrate. This would be the state of the regulators as well as which outputs are enabled.
The config file loaded is `/home/asu/daemon/config.yaml`
```json
{
    "command": "loadConfig",
    "args": {}
}
```


<a name="CommandDisableAllOutputs"></a>
### Command - Disable All Outputs
```json
{
    "command": "disableAllOutputs",
    "args": {}
}
```



## Reply On Command Success
```json
{
    "status": "ok",
    "card": 1,
    "channel": 1,
    "vbus": 2.334,
    "vshunt": 0.024,
    "current": 0.2,
    "outputEnabled": true,
    "wiper": 768
}
```



## Reply on Error
```json
{
    "status": "error",
    "code": -1,
    "msg": "Received an invalid command message"
}
```

<a name="Configuration"></a>
## Configuration
Configuration can be found in `$HOME/daemon/config.yml`

<a name="Logs"></a>
## Logs
The application creates logs in `$HOME/daemon/logs/applog.txt`. Logs can reach a maximum of 4 Megabytes before being rolled over.
The previous logs would be renamed to applog.txt.1, applog.txt.2, etc until 5. This is to keep the logs from being burdensome on the
system.

For details on implementation, see [Python's RotatingFileHandler](https://docs.python.org/3/library/logging.handlers.html#logging.handlers.RotatingFileHandler)


# Testing
First, a redis server is spun up. This project is then transferred to the PI with scp. Following this, the virtual environment
in `$HOME/.venv/bin/` is activated and we execute pytest on the tests directory.
A local redis server is spun up. This tooling is uploaded to the raspberry pi. pytest is then ran on the tests dicrectory.




<!-- ## Document Generation -->
<!-- The documentation you are currently reading was generated automatically using github pages. An orphaned branch was  -->
<!-- created called `docs`. Changes in the main branch are pulled into docs manually, and on `git commit, git push` the docs are rebuilt and deployed. -->
<!---->
