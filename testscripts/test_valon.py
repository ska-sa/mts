#! /usr/bin/env python

from optparse import OptionParser
import valon_synth
from valon_api import MTSvalon
import numpy
import time

# Simple example of using the valon_api to connect to a Valon Synth directly

if __name__ == '__main__':
    parser = OptionParser(version="%prog 0.1")
    parser.add_option('-p', '--port',
                      action='store',
                      dest='tty',
                      default='/dev/ttyUSB0',
                      help='Set Serial Port, default is \'%default\'.')
    (opts, args) = parser.parse_args()

    print """
Connect a Valon 5007 to a spectrum analyser -- a 20dB attenuator is used.
The Valon 5007 is specified to have a range of 137 MHz to 4400MHz.
"""
    raw_input('Enter to connect to Valon')

    # MTS uses only one of the available synthesizers (currently SYNTH 2)
    synth = MTSvalon(valon_synth.SYNTH_B, opts.tty, timeout=-1)
    if synth.get_rf_level(valon_synth.SYNTH_B) != -4:
        synth.set_rf_level(valon_synth.SYNTH_B, -4)

    # Set CW signal frequency
    synth.set_cw_freq(freq_mhz=137)
    print 'CW frequency set to %s MHz' % synth.get_cw_freq()
    raw_input('Enter to exit')
    print 'Setting Valon to Low Spur Mode'
    synth.set_options(valon_synth.SYNTH_B, low_spur=1)
    raw_input('Enter to exit')
    print 'Settings Valon to Low Noise Mode'
    synth.set_options(valon_synth.SYNTH_B, low_spur=0)
    raw_input('Enter to exit')

    print 'Sweep over frequencies 137MHz to 1500MHz'
    for freq_mhz in numpy.arange(137., 1500, 20.):
        synth.set_cw_freq(freq_mhz=freq_mhz)
        print 'CW frequency set to %s MHz' % synth.get_cw_freq()
        raw_input('Enter to continue')

    print 'Sweep over frequencies 137MHz to 4400MHz'
    raw_input('Enter to continue')
    for freq_mhz in numpy.arange(137., 4400, 100.):
        synth.set_cw_freq(freq_mhz=freq_mhz)
        print 'CW frequency set to %s MHz' % synth.get_cw_freq()
        time.sleep(1)

    synth.conn.close()

# -fin-
