---
layout: default
---

# Table of Contents

1. [OS](#OS)
1. [Updates](#Updates)

<a name="OS"></a>
# OS
A raspberry PI 4 model B is used to provide a control interface between some main computer and the bias channels.
The Raspberry pi imager was used to flash Rasbian Lite onto an SD card which was then loaded onto the pi.

`cat /etc/*-release` gave us:

```
PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"
NAME="Debian GNU/Linux"
VERSION_ID="12"
VERSION="12 (bookworm)"
VERSION_CODENAME=bookworm
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"

```


- The hostname was set to `primecambias`. SSH was enabled. No default IP address was assigned to it's ethernet interface. Instead, 
  we let it get auto assigned within our internal network. This can be overwritten via a modification to the PI's boot config file.
- The user `asu` was created. 
- we logged into the pi via `ssh asu@primecambias.local`

<a name="Updates"></a>
# Updates
- `sudo rpi-update` was ran which updated the pi's EEPROM.

```
EEPROM
------

FW_REV:0a0b3671d5fd313983ea584c6067836e5143eb3b
BOOTLOADER_REV:816bf7c594a4c117ab2815f443ad3d535be475a6

BOOTLOADER: up to date
   CURRENT: Tue 11 Feb 17:00:13 UTC 2025 (1739293213)
    LATEST: Tue 11 Feb 17:00:13 UTC 2025 (1739293213)
   RELEASE: latest (/usr/lib/firmware/raspberrypi/bootloader-2711/latest)
            Use raspi-config to change the release.

  VL805_FW: Using bootloader EEPROM
     VL805: up to date
   CURRENT: 000138c0
    LATEST: 000138c0
```

- The system packages were all updated. `sudo apt update; sudo apt upgrade -y; sudo apt autoremove`
- I2C Was enabled. `sudo raspi-config`, `Interface Options` --> `I2C` --> yes to `Would you like the ARM I2C interface to be enabled?`
- Locate was set to en-US `sudo raspi-config`, `Localisation Options` --> `Locale` --> `en-US utf-8`
- Timezone was set to Americas/Phoenix.  `sudo raspi-config`-->`Localisation Options` --> `Timezone`
- Installed pip `sudo apt update && sudo apt install python3-pip -y`
- Installed i2ctools `sudo apt install i2c-tools`

We then verified we could access the I2C bus (even with nothing attached)

```sh
asu@primecambias:~ $ i2cdetect -y 1
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:                         -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
70: -- -- -- -- -- -- -- --
```

