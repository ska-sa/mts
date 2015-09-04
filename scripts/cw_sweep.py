#!/usr/bin/python

from optparse import OptionParser
from mts.mts import MTS
import numpy, string, time

## MTS source modules have wider bandwidth than is provided by the combiner outputs.
#  This functions shows how to use the loaded config parameter to sweep a CW signal over the output bandwidth available when directly
#  interacting with the source module functions

if __name__ == '__main__':

  parser = OptionParser(version="%prog 0.1")
# ./mts_cw_sweep.py -p /dev/ttyUSB1 -v /dev/ttyUSB0 -o comb2
  parser.add_option('-p', '--port',
                    action='store',
                    dest='tty',
                    default='/dev/ttyUSB1',
                    help='Set serial port, default is \'%default\'.')
  parser.add_option('-v', '--valon',
                    action='store',
                    dest='cwtty',
                    default='/dev/ttyUSB0',
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
  start=time.time()
  mts_obj = MTS(port=opts.tty, baudrate=int(opts.baudrate), valon=opts.cwtty, config_file=opts.config_file)
  print 'Initiation takes %.4f seconds' %(time.time()-start)

# Output is measured from combiner
  output = mts_obj.select_combiner(opts.combiner)
  print '\nConnect output from %s to spectrum analyser' % opts.combiner
  print 'Available frequency range from %f MHz to %f MHz' % (mts_obj.MIN_BASE, mts_obj.MAX_BASE)
##Initiate combiner
  min_freq_mhz=max([output.MIN_CW, output.MIN_NOISE])
  max_freq_mhz=min([output.MAX_CW, output.MAX_NOISE])
  output.power_temp_sensor(enable=True)
  [pwr_mv_per_dbm, temp_mv_per_deg] = output.get_environment()
  print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
  print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg
  output.set_comb_atten(atten=output.MIN_ATTEN) # dB
  atten = output.get_comb_atten() # dB
  print '\tcomb attenuated %.2f dB' % atten
  print 'Baseline output for combiner %s' % opts.combiner
  raw_input('Enter to continue')

##CW for uncorrelated source
  output.ucs.cw_source(enable=True, verbose=True)
  output.ucs.cw_output(enable=True, verbose=True)
  output.ucs.set_cw_atten(atten=output.ucs.MIN_ATTEN, verbose=True)
  # Sweep CW
  try:
    for freq_mhz in numpy.arange(min_freq_mhz, max_freq_mhz, 5):
      output.ucs.set_freq(freq_mhz=freq_mhz, verbose=True)
      cw_freq_mhz = output.ucs.get_freq(verbose=True)
      print '\tcw frequency set to %s MHz' % cw_freq_mhz
      raw_input('Enter to continue')
  except KeyboardInterrupt: pass # exit test loop safely
  # CW with noise
  output.ucs.set_cw_atten(atten=output.ucs.MIN_ATTEN, verbose=True)
  output.ucs.set_freq(freq_mhz=137., verbose=True)
  output.ucs.noise_source(enable=True, verbose=True)
  output.ucs.noise_output(enable=True, verbose=True)
  output.ucs.set_noise_atten(atten=output.ucs.MIN_ATTEN, verbose=True)
  raw_input('Enter to continue')

  output.ucs.noise_source(enable=False, verbose=True)
  output.ucs.noise_output(enable=False, verbose=True)
  output.ucs.cw_source(enable=False, verbose=True)
  output.ucs.cw_output(enable=False, verbose=True)

##CW for correlated source
  output.cs.cw_source(enable=True, verbose=True)
  output.cs.cw_output(enable=True, verbose=True)
  output.cs.set_cw_atten(atten=output.cs.MIN_ATTEN, verbose=True)
  # Sweep CW
  try:
    for freq_mhz in numpy.arange(min_freq_mhz, max_freq_mhz, 5):
      output.cs.set_freq(freq_mhz=freq_mhz, verbose=True)
      cw_freq_mhz = output.cs.get_freq(verbose=True)
      print '\tcw frequency set to %s MHz' % cw_freq_mhz
      raw_input('Enter to continue')
  except KeyboardInterrupt: pass # exit test loop safely
  # CW with noise
  output.cs.set_cw_atten(atten=output.cs.MIN_ATTEN, verbose=True)
  output.cs.set_freq(freq_mhz=137., verbose=True)
  output.cs.noise_source(enable=True, verbose=True)
  output.cs.noise_output(enable=True, verbose=True)
  output.cs.set_noise_atten(atten=output.cs.MIN_ATTEN, verbose=True)
  raw_input('Enter to continue')

  output.cs.noise_source(enable=False, verbose=True)
  output.cs.noise_output(enable=False, verbose=True)
  output.cs.cw_source(enable=False, verbose=True)
  output.cs.cw_output(enable=False, verbose=True)

  print 'Exit test controller...'
  start=time.time()
  mts_obj.exit()
  print 'Exiting takes %.4f seconds' %(time.time()-start)

# -fin-


