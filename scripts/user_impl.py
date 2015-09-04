#!/usr/bin/python

from optparse import OptionParser
import mts
import string, time
import numpy, pylab

## There are 2 ways available to interact with the MTS
#  This script shows the user defined level with compound functions to allow easy interaction

if __name__ == '__main__':

  parser = OptionParser(version="%prog 0.1")
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

## 2 Ways of working with the MTS
#  2 - Setting output for a combiner output
  from mts import MTS
  print 'Initiating all controller modules...'
  mts_obj = MTS(port=opts.tty, baudrate=int(opts.baudrate), valon=opts.cwtty, config_file=opts.config_file)

  print '\nConnect output from %s to spectrum analyser' % opts.combiner
  print 'Available frequency range from %f MHz to %f MHz' % (mts_obj.MIN_BASE, mts_obj.MAX_BASE)

  [pwr_mv_per_dbm, temp_mv_per_deg] = mts_obj.select_combiner(opts.combiner).get_environment()
  output_pwr = mts_obj.__get_pwr__(comb=mts_obj.select_combiner(opts.combiner)) # dBm
  print "Amplitude sensor reading of %f mV/dBm translates to %f dBm power" %(pwr_mv_per_dbm, output_pwr)

  # Uncorrelated noise source
  print '\nNoise output from uncorrelated source'
  input_pwr=-27
  mts_obj.set_noise(output=opts.combiner, uncorr_pwr=input_pwr)
  print 'Requested power = %f dBm' % input_pwr
  print 'Output noise signal with power %f dBm' % (mts_obj.get_noise(output=opts.combiner))

  measurements = []
  for count in range(100):
    measurements.append(mts_obj.get_noise(output=opts.combiner))
  measurements = numpy.array(measurements)
  e = abs(measurements - input_pwr)
  pylab.figure()
  pylab.errorbar(range(100), measurements, yerr=e, fmt='ro')
  pylab.title('Max spread = %f dB' % max(e))
  pylab.savefig('uncorr_noise_output.png')

  raw_input('Measure occupied bandwidth power and verify %f dBm. Enter to continue' % input_pwr)

  mts_obj.disable_noise(output=opts.combiner, uncorr_src=True)
  print 'Disabled noise signal has power %f dBm' % (mts_obj.get_noise(output=opts.combiner))

  # Correlated noise source
  print '\nNoise output from correlated source'
  input_pwr=-20
  mts_obj.set_noise(output=opts.combiner, corr_pwr=input_pwr)
  print 'Requested power = %f dBm' % input_pwr
  print 'Output noise signal with power %f dBm' % (mts_obj.get_noise(output=opts.combiner, cal_tbl=mts_obj.CS_NOISE))

  measurements = []
  for count in range(100):
    measurements.append(mts_obj.get_noise(output=opts.combiner, cal_tbl=mts_obj.CS_NOISE))
  measurements = numpy.array(measurements)
  e = abs(measurements - input_pwr)
  pylab.figure()
  pylab.errorbar(range(100), measurements, yerr=e, fmt='ro')
  pylab.title('Max spread = %f dB' % max(e))
  pylab.savefig('corr_noise_output.png')

  raw_input('Measure occupied bandwidth power and verify %f dBm. Enter to continue' % input_pwr)

  mts_obj.disable_noise(output=opts.combiner, corr_src=True)
  print 'Disabled noise signal has power %f dBm' % (mts_obj.get_noise(output=opts.combiner, cal_tbl=mts_obj.CS_NOISE))

  # Uncorrelated CW output
  print '\nCW output from uncorrelated source'
  input_pwr=-27
  mts_obj.set_cw(output=opts.combiner, uncorr_pwr=input_pwr, uncorr_freq=220.)
  print 'Requested power = %f dBm' % input_pwr
  print 'Output CW signal with power %f dBm' % (mts_obj.get_cw(output=opts.combiner))
  print 'Requested frequency = 220 MHz'
  print 'Output CW signal frequency = %f MHz' % (mts_obj.get_freq(output=opts.combiner, uncorr_src=True))

  measurements = []
  for count in range(100):
    measurements.append(mts_obj.get_cw(output=opts.combiner))
  measurements = numpy.array(measurements)
  e = abs(measurements - input_pwr)
  pylab.figure()
  pylab.errorbar(range(100), measurements, yerr=e, fmt='ro')
  pylab.title('Max spread = %f dB' % max(e))
  pylab.savefig('uncorr_cw_output.png')

  raw_input('Measure marker power at 220 MHz frequency spike and verify %f dBm. Enter to continue' % input_pwr)

  mts_obj.disable_cw(output=opts.combiner, uncorr_src=True)
  print 'Disabled CW signal has power %f dBm' % (mts_obj.get_cw(output=opts.combiner))

  # Correlated CW output
  print '\nCW output from correlated source'
  input_pwr=-20
  mts_obj.set_cw(output=opts.combiner, corr_pwr=input_pwr, corr_freq=300.)
  print 'Requested power = %f dBm' % input_pwr
  print 'Output CW signal with power %f dBm' % (mts_obj.get_cw(output=opts.combiner, cal_tbl=mts_obj.CS_CW))
  print 'Requested frequency = 300 MHz'
  print 'Output CW signal frequency = %f MHz' % (mts_obj.get_freq(output=opts.combiner, corr_src=True))

  measurements = []
  for count in range(100):
    measurements.append(mts_obj.get_cw(output=opts.combiner, cal_tbl=mts_obj.CS_CW))
  measurements = numpy.array(measurements)
  e = abs(measurements - input_pwr)
  pylab.figure()
  pylab.errorbar(range(100), measurements, yerr=e, fmt='ro')
  pylab.title('Max spread = %f dB' % max(e))
  pylab.savefig('corr_cw_output.png')

  raw_input('Measure marker power at 300 MHz frequency spike and verify %f dBm. Enter to continue' % input_pwr)

  mts_obj.disable_cw(output=opts.combiner, corr_src=True)
  print 'Disabled CW signal has power %f dBm' % (mts_obj.get_cw(output=opts.combiner, cal_tbl=mts_obj.CS_CW))
  pylab.show()

  print '\nExit test controller...'
  mts_obj.exit()

# -fin-


