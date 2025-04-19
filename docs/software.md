---
layout: default
---
# Software Documentation


1. [Considerations](#Considerations) 
1. [Design](#Design)
    1. [Command Line Interface](#CommandLineInterface)

<a name="Considerations"></a>
# Considerations 

- The software is called Sparky(ASU's mascot) Bias Daemon or sparkybiasd 
- The code should be easy for others to modify and use.
- The software shall run as a "Hands Off" daemon on the PI at startup; managed by [systemd](https://manpages.org/systemd).
    - An assumption was made that redis was being used to handle the readout system.
      Therefore, it would be reasonable to use that for bias control.
- The software shall generate a log file when running as a system service.
- The software shall have a basic command line interface for development and testing.
- The software should be easy for the end user to update. 
    - We will generate a python package so it can be installed and updated with pip.

---
<a name="Design"></a>
# Design
A tool called [poetry](https://python-poetry.org/docs/) is used for package dependency and generation.
A python package called Click is used to generate and handle the CLI.


<a name="CommandLineInterface"></a>
## Command Line Interface
A CLI was thrown together to enable board testing...


```bash
$sparkybias --help
```

```
Usage: sparkybias.py [OPTIONS] COMMAND [ARGS]...

  Sparky Bias Daemon - Command Line interface

  This is a test/debug interface which is used for the development and testing
  of the system. An exception will be raised if the daemon is already running
  and you attempt to use this CLI.

Options:
  --help  Show this message and exit.

Commands:
  readina      Read voltage, shunt, current from INA219
  setexpander  set IO Expander to a value
  setrepeater  Command an LTC4302 to enable it's I2C bus or set it's GPIO.

```









<!-- ## Document Generation -->
<!-- The documentation you are currently reading was generated automatically using github pages. An orphaned branch was  -->
<!-- created called `docs`. Changes in the main branch are pulled into docs manually, and on `git commit, git push` the docs are rebuilt and deployed. -->
<!---->
