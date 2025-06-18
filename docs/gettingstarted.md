---
layout: default
---


1. [Getting Started](#GettingStarted) 
    1. [Configuring the Service](#ConfigureTheService)
    1. [Running the Unit Tests](#RunningTheUnitTests)
    1. [Using the bias supply](#UsingTheBias)

---

<a name="GettingStarted"></a>
# Getting Started
The bias crate's onboard raspberry pi was configured to have a static IP of `192.168.128.10` subnet `255.255.255.0`. 
To modify the ethernet configuration, ssh into the unit.

```
hostname: primecambias.local
ip: 192.168.128.10
Username: asu
Password: primecam
```

Following this, use the command `sudo nmtui` to open the Network Manager config menu and set as desired. 
Raspberry PI works well with DHCP if you have the desire to connect to a regular network. 

<a name="ConfigureTheService"></a>
## Confiure the service
A python library was configured as a service and runs at startup. The service (or daemon) is named `sparkybiasd`.

Currently, the service is trying (and failing) to connect to a Redis Server. You need to configure your redis server to listen 
on the ip/interface that the bias crate is connected to. Once this is complete, ssh into the bias crate. Following this use an editor such as nano or vi to
modify the redis settings within `/home/asu/daemon/config.yaml` to match what you have configured.  You may have to restart the bias control service.

`sudo systemctl restart sparkybiasd`

and view it's status.

`sudo systemctl status sparkybiasd`

It should now be online and show as active. The daemon saves its logs to `/home/asu/daemon/logs/applog.txt`. You can view the status of the daemon and watch
it react to commands there. 

<!-- TODO: Mention that we subscribe and publish on the channels listed in the config. -->

<a name="RunningTheUnitTests"></a>
## Runnning the unit tests
First, you will need to pull down the Primecam-Bias repository (link below). Inside of sparkybiasd is the source code for the daemon as well as the unit tests. 
The first step is to make sure the daemon is active and connected to the Redis server. On the host computer connected to the bias crate, create or start a virtual environment and
install the packages listed under pyproject.toml except for smbus2. Following this, you will want to modify the test fixture code in the tests such that the redis object matches your 
setup. An example is listed in the following code block. Once all of the test files have been modified, you can execute the tests by running `pytest` in the tests folder assuming 
you have installed that package. 

```
@pytest.fixture
def redisFixt():
    """Fixture to create a Redis client."""
    client = redis.Redis(host='10.206.160.58', port=6379)
```
[Link to the repository](https://github.com/asu-rdl/Primecam-Bias)

[Link to pyproject.toml Here](https://github.com/asu-rdl/Primecam-Bias/blob/v0.2.4/sparkybiasd/pyproject.toml)


<a name="UsingTheBias"></a>
## Using the Bias
Once the crate is connected and brought online, it subscribes to a redis pubsub channel defined in `config.yaml`. Following this, it listens for
and executes commands passed to it in JSON format. Finally, it sends out replies over redis on the channel also defined in `config.yaml`. Changing the config
requires restarting the service.

As long as you can send / receive commands via redis, you can use any programming language of your choice. The following is an example command to get
the status of a channel written in python.

```python
import redis
import json
client = redis.Redis(host='redis.ip.address.here', port=6379)
psub = client.pubsub()
psub.subscribe('sparkreply')
psub.get_message()

command = {
    "command": "getStatus",
    "args": {
        "card": 1,
        "channel": 1
    }
}
redis_client.publish('sparkommand', json.dumps(command))
message = pubsub.get_message(True, timeout=None)
response =  json.loads(message['data'].decode())

print(f"{response['vbus']}, {response['vshunt']}, {response['current']}, {response['outputEnabled']}")
```

**For a full list of commands and their formats see [Software](software.html).**



<a name=""></a>


