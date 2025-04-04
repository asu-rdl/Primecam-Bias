# Notes
- [x] Get addresses for the LTC4302's repeaters
- [x] Get the address for the AD5144 - 0x2F
- [x] Update the code to have the new addresses
- [x] Update the print menu
    - [X] Command to init the I2C Devices
    - [X] Enable GPIO1 from LTC4302-19
    - [X] Disable GPIO1 form LTC4302-19
    - [X] Set pot
    - [X] Read INA219
    - [ ] 
- [ ]


## Execution
- On startup, connect to LTC4302-addr1
- on Startup  Connect LTC4302-addr19
  - Ensure GPIO1 is pulled low
- Init the INA219


### II2 Addresses 
INA219              0x40
LTC4302-BASE ADDR   0x60
LTC4302-1           0x61
LTC4302-19          0x73
ADF5144             0x2F

