---
layout: default
---


1. [Getting Started](#GettingStarted) 

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

## Confiure the service
A python library was configured as a service and runs at startup. The service is named `sparkybiasd`.

Currently, the service is trying (and failing) to connect to a Redis Server. You need to configure your redis server to listen 
on the ip/interface that the bias crate is connected to. Once this is complete, ssh into the bias crate. Following this use an editor such as nano or vi to
modify the redis settings within `/home/asu/daemon/config.yaml` to match what you have configured. You have have to restart the bias control service

`sudo systemctl restart sparkybiasd`

and view it's status.

`sudo systemctl status sparkybiasd`

It should now be online and show as active. The daemon saves its logs to `/home/asu/daemon/logs/applog.txt`. You can view the status of the daemon and watch
it react to commands there. 

## Runnning the unit tests
The first step is to make sure the daemon is active and connected to the Redis server. On the host computer connected to the bias crate, create or start a virtual environment and
install the packages listed under pyproject.toml except for smbus2.

[Link to pyproject.toml Here](https://github.com/asu-rdl/Primecam-Bias/blob/v0.2.4/sparkybiasd/pyproject.toml)









<a name=""></a>


