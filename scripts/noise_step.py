#!/usr/bin/python

from optparse import OptionParser
from mts.mts import MTS
import numpy
import time

# The MTS variable attenuators has a limited setting range
#  This functions shows how to use the loaded config parameter to step the variable attenuators of the noise sources over the available range
#  directly interacting with the source module function

if __name__ == '__main__':

    parser = OptionParser(version="%prog 0.1")
# ./mts_noise_step.py -p /dev/ttyUSB1 -o comb1
    parser.add_option('-p', '--port',
                      action='store',
                      dest='tty',
                      default='/dev/ttyUSB1',
                      help='Set serial port, default is \'%default\'.')
    parser.add_option('-b', '--baud',
                      action='store',
                      dest='baudrate',
                      default=115200,
                      help='Set serial port baudrate, default is \'%default\'.')
    parser.add_option('-c', '--config',
                      action='store',
                      dest='config_file',
                      default='/etc/mts/mts_default',
                      help='MTS config file, default is \'%default\'.')
    parser.add_option('-o', '--output',
                      action='store',
                      dest='combiner',
                      default='comb1',
                      help='Output signal from MTS config file, default is \'%default\'.')
    (opts, args) = parser.parse_args()

    print 'Initiating all controller modules...'
    start = time.time()
    mts_obj = MTS(port=opts.tty, baudrate=int(opts.baudrate), config_file=opts.config_file)
    print 'Initiation takes %.4f seconds' % (time.time()-start)

# Output is measured from combiner
    output = mts_obj.select_combiner(opts.combiner)
    print '\nConnect output from %s to spectrum analyser' % opts.combiner
    print 'Available frequency range from %f MHz to %f MHz' % (mts_obj.MIN_BASE, mts_obj.MAX_BASE)
#   Initiate combiner
    min_freq_mhz = max([output.MIN_CW, output.MIN_NOISE])
    max_freq_mhz = min([output.MAX_CW, output.MAX_NOISE])
    output.power_temp_sensor(enable=True)
    [pwr_mv_per_dbm, temp_mv_per_deg] = output.get_environment()
    print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
    print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg
    output.set_comb_atten(atten=output.MIN_ATTEN)  # dB
    atten = output.get_comb_atten()  # dB
    print '\tcomb attenuated %.2f dB' % atten
    print 'Baseline output for combiner %s' % opts.combiner
    raw_input('Enter to continue')

#   Noise for uncorrelated source
    output.ucs.noise_source(enable=True, verbose=True)
    output.ucs.noise_output(enable=True, verbose=True)
    try:
        for atten in numpy.arange(output.ucs.MIN_ATTEN, output.ucs.MAX_ATTEN+0.5, 1):
            output.ucs.set_noise_atten(atten=atten, verbose=True)
            raw_input('Enter to continue')
    except KeyboardInterrupt:
        pass  # exit test loop safely
    output.ucs.noise_source(enable=False, verbose=True)
    output.ucs.noise_output(enable=False, verbose=True)


# Noise for correlated source
    output.cs.noise_source(enable=True, verbose=True)
    output.cs.noise_output(enable=True, verbose=True)
    try:
        for atten in numpy.arange(output.cs.MIN_ATTEN, output.cs.MAX_ATTEN+0.5, 1):
            output.cs.set_noise_atten(atten=atten, verbose=True)
            raw_input('Enter to continue')
    except KeyboardInterrupt:
        pass  # exit test loop safely
    output.cs.noise_source(enable=False, verbose=True)
    output.cs.noise_output(enable=False, verbose=True)

    print 'Exit test controller...'
    start = time.time()
    mts_obj.exit()
    print 'Exiting takes %.4f seconds' % (time.time()-start)

# -fin-
