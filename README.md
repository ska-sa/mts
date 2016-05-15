# MTS = Modular Test System (DBE)

## Connections:

Currently the USB ports associated with the MTS is not fixed and the assigned
ports to both the MTS controller serial interface and the Valon serial interface
need to be identified to be able to address the MTS devices.

First you need to identify that both devices are available. Use the `lsusb`
command in linux and look for:

  - the identification of the __Valon__ serial port:

        Future Technology Devices International, Ltd FT232 USB-Serial (UART) IC

  - the __MTS__ controller devices designation.

        Cygnal Integrated Products, Inc. CP210x Composite Device

To connect to the devices use the dmesg command to get the assigned port

    $ dmesg | grep FTDI  # Valon
    FTDI USB Serial Device converter now attached to ttyUSB0

    $ dmesg | grep cp210x  # MTS
    cp210x converter now attached to ttyUSB1

## Testing connectivity

The following checks Valon connectivity:

    $ mts/valon_api.py -p /dev/ttyUSB0

The following checks MTS connectivity:

    $ mts/mts_api.py -p /dev/ttyUSB1

## Summary of example script:

The MTS interface will install user scripts to `/usr/local/bin/`.  To run these
directly from the command line make sure this is part of the `PATH`.

### Suggested usage --

There are 2 ways available to interact with the MTS

`usr_impl.py`
:   This script shows the user defined level with compound functions to allow
    easy interaction

`module_impl.py`
:   This script shows the usage interaction when directly setting up the MTS on
    a per module basis

`fsu_cal_measure.py`
:   Calibrating the MTS output using the R&S FSU spectrum analyser and the SCPI
    socket interface

### Modular interaction --

`cw.py`
:   Example commands to show direct interactions with MTS source and or combiner
    modules to set up CW output signals

`noise.py`
:   Example commands to show direct interactions with MTS source and or combiner
    modules to set up noise output signals

`cw_sweep.py`
:   MTS source modules have wider bandwidth than is provided by the combiner
    outputs.
    This functions shows how to use the loaded config parameter to sweep a CW
    signal over the output bandwidth available when directly interacting with
    the source module functions

`noise_step.py`
:   The MTS variable attenuators has a limited setting range
    This functions shows how to use the loaded config parameter to step the
    variable attenuators of the noise sources over the available range directly
    interacting with the source module function
