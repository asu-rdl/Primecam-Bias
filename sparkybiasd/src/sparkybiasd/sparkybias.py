import click
from . import hardware


myCard = hardware.biascard(1)

@click.group()
def cli():
    """Sparky Bias Daemon - Command Line interface

    This is a test/debug interface which is used for the development and testing of the system.
    An exception will be raised if the daemon is already running and you attempt to use this CLI.

    """
    pass


@click.command()
@click.option("-g1", "--gpio1", "gpio1", help="set gpio1 HIGH", is_flag=True)
@click.option("-g2", "--gpio2", "gpio2", help="set gpio2 HIGH", is_flag=True)
@click.argument("address", type=int)
@click.argument("enable", type=bool)
def setrepeater(address:int, enable: bool, gpio1: bool, gpio2: bool):
    """Command an LTC4302 to enable it's I2C bus or set it's GPIO.
    
    ADDRESS  -  The relative address of the LTC4302-1. Valid addresses are 0-31. 
    ENABLE   -  Set to 0 to disable the I2C bus, set to 1 to enable the I2C bus. 
    """
    assert address > -1 and address <= 31, "Valid addresses are 0-31"
    assert enable==0 or enable==1, "Valid addresses are 0-31"
    click.echo(f"\tset repeater to {"enable" if enable else "disable"} the i2c bus at address {hex(0x60+address)}")
    click.echo(f"\twith GPIO1 set to {"HIGH" if gpio1 else "LOW"}")
    click.echo(f"\twith GPIO2 set to {"HIGH" if gpio2 else "LOW"}")

@click.command()
@click.argument("channel", type=int)
def readina(channel):
    """ Read voltage, shunt, current from INA219

    CHANNEL  -  Channel Number to read (1-8)
    """
    assert channel >=1 and channel <= 8, "received an invalid channel number"


@click.command()
def setexpander():
    """ set IO Expander to a value

    """
    pass

cli.add_command(setrepeater)
cli.add_command(readina)
cli.add_command(setexpander)

if __name__ == "__main__":

    cli()
