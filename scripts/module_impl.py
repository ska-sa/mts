#!/usr/bin/python

from optparse import OptionParser
import mts
import string, time

## There are 2 ways available to interact with the MTS
#  This script shows the usage interaction when directly setting up the MTS on a per module basis

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
#  1 - On a per module way
  from mts import MTS
  print 'Initiating all controller modules...'
  mts_obj = MTS(port=opts.tty, baudrate=int(opts.baudrate), valon=opts.cwtty, config_file=opts.config_file)

  print '\nConnect output from %s to spectrum analyser' % opts.combiner
  print 'Available frequency range from %f MHz to %f MHz' % (mts_obj.MIN_BASE, mts_obj.MAX_BASE)
  output = mts_obj.select_combiner(opts.combiner)
  output.power_temp_sensor(enable=True)

  print 'Noise output from uncorrelated source'
  output.ucs.noise_output(enable=True, verbose=True)
  output.ucs.set_noise_atten(atten=output.ucs.MAX_ATTEN, verbose=True) # dB
  atten = output.ucs.get_noise_atten() # dB
  print '\tnoise attenuated %.2f dB' % atten
  [pwr_mv_per_dbm, temp_mv_per_deg] = output.get_environment()
  print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
  print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg
  output.ucs.set_noise_atten(atten=28.5, verbose=True) # dB
  atten = output.ucs.get_noise_atten() # dB
  print '\tnoise attenuated %.2f dB' % atten
  [pwr_mv_per_dbm, temp_mv_per_deg] = output.get_environment()
  print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
  print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg
  raw_input('Enter to disable uncorrelated noise output')
  output.ucs.noise_output(enable=False, verbose=True)

  print 'Noise output from correlated source'
  output.cs.noise_output(enable=True, verbose=True)
  output.cs.set_noise_atten(atten=output.cs.MAX_ATTEN, verbose=True) # dB
  atten = output.cs.get_noise_atten() # dB
  print '\tnoise attenuated %.2f dB' % atten
  [pwr_mv_per_dbm, temp_mv_per_deg] = output.get_environment()
  print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
  print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg
  output.cs.set_noise_atten(atten=28.5, verbose=True) # dB
  atten = output.cs.get_noise_atten() # dB
  print '\tnoise attenuated %.2f dB' % atten
  [pwr_mv_per_dbm, temp_mv_per_deg] = output.get_environment()
  print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
  print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg
  raw_input('Enter to disable correlated noise output')
  output.cs.noise_output(enable=False, verbose=True)

  print 'CW output from uncorrelated source'
  cw_freq_mhz = output.ucs.get_freq(verbose=True)
  print '\tcw frequency set to %s MHz' % cw_freq_mhz
  output.ucs.set_cw_atten(atten=output.ucs.MIN_ATTEN, verbose=True)
  atten = output.ucs.get_cw_atten() # dB
  print '\tcw attenuated %.2f dB' % atten
  output.ucs.set_freq(freq_mhz=220., verbose=True)
  cw_freq_mhz = output.ucs.get_freq(verbose=True)
  print '\tcw frequency set to %s MHz' % cw_freq_mhz
  output.ucs.cw_output(enable=True, verbose=True)
  [pwr_mv_per_dbm, temp_mv_per_deg] = output.get_environment()
  print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
  print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg
  raw_input('Enter to disable uncorrelated cw output')
  output.ucs.cw_output(enable=False, verbose=True)
  [pwr_mv_per_dbm, temp_mv_per_deg] = output.get_environment()
  print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
  print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg

  print 'CW output from correlated source'
  cw_freq_mhz = output.cs.get_freq(verbose=True)
  print '\tcw frequency set to %s MHz' % cw_freq_mhz
  output.cs.set_cw_atten(atten=output.cs.MIN_ATTEN, verbose=True)
  atten = output.cs.get_cw_atten() # dB
  print '\tcw attenuated %.2f dB' % atten
  output.cs.set_freq(freq_mhz=220., verbose=True)
  cw_freq_mhz = output.cs.get_freq(verbose=True)
  print '\tcw frequency set to %s MHz' % cw_freq_mhz
  output.cs.cw_output(enable=True, verbose=True)
  [pwr_mv_per_dbm, temp_mv_per_deg] = output.get_environment()
  print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
  print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg
  raw_input('Enter to disable correlated cw output')
  output.cs.cw_output(enable=False, verbose=True)
  [pwr_mv_per_dbm, temp_mv_per_deg] = output.get_environment()
  print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
  print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg

  print 'Exit test controller...'
  mts_obj.exit()

# -fin-


