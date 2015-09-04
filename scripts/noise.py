#!/usr/bin/python

from optparse import OptionParser
from mts.mts import MTS
import numpy, string, time

##Example commands to show direct interactions with MTS source and or combiner modules to set up noise output signals

if __name__ == '__main__':

  parser = OptionParser(version="%prog 0.1")
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
  (opts, args) = parser.parse_args()

  print 'Initiating all controller modules...'
  start=time.time()
  mts_obj = MTS(port=opts.tty, baudrate=int(opts.baudrate), config_file=opts.config_file)
  print 'Initiation takes %.4f seconds' %(time.time()-start)

  print 'Attach Module 1 noise output to spectrum analyzer using 20dB attenuation'
  raw_input('Enter to continue')
  mts_obj.ucs1.noise_source(enable=True, verbose=True)
  mts_obj.ucs1.noise_output(enable=True, verbose=True)
  mts_obj.ucs1.set_noise_atten(atten=mts_obj.ucs1.MIN_ATTEN, verbose=True)
  print 'Verify that no signal is measured from the noise output of source module 2 and 3'
  raw_input('Enter to continue')
  print 'Measure similar noise power from combiner 1'
  raw_input('Enter to continue')
  print 'Measure similar noise power from combiner 2'
  raw_input('Enter to continue')

  mts_obj.ucs1.set_noise_atten(atten=mts_obj.ucs1.MAX_ATTEN, verbose=True)
  print 'Measure similar noise power from combiner 1'
  raw_input('Enter to continue')
  print 'Measure similar noise power from combiner 2'
  raw_input('Enter to continue')
  mts_obj.ucs1.noise_source(enable=False, verbose=True)
  mts_obj.ucs1.noise_output(enable=False, verbose=True)

  print 'Attach Module 3 noise output to spectrum analyzer using 20dB attenuation'
  raw_input('Enter to continue')
  mts_obj.cs1.noise_source(enable=True, verbose=True)
  mts_obj.cs1.noise_output(enable=True, verbose=True)
  mts_obj.cs1.set_noise_atten(atten=mts_obj.cs1.MIN_ATTEN, verbose=True)
  print 'Verify that no signal is measured from the noise output of source module 2 and 3'
  raw_input('Enter to continue')
  print 'Measure similar noise power from combiner 1'
  raw_input('Enter to continue')
  print 'Measure similar noise power from combiner 2'
  raw_input('Enter to continue')

  mts_obj.cs1.set_noise_atten(atten=mts_obj.cs1.MAX_ATTEN, verbose=True)
  print 'Measure similar noise power from combiner 1'
  raw_input('Enter to continue')
  print 'Measure similar noise power from combiner 2'
  raw_input('Enter to continue')
  mts_obj.cs1.noise_source(enable=False, verbose=True)
  mts_obj.cs1.noise_output(enable=False, verbose=True)


  print 'Attach Module 2 noise output to spectrum analyzer using 20dB attenuation'
  raw_input('Enter to continue')
  output = mts_obj.select_combiner('comb2')
  output.ucs.noise_source(enable=True, verbose=True)
  output.ucs.noise_output(enable=True, verbose=True)
  output.ucs.set_noise_atten(atten=output.ucs.MIN_ATTEN, verbose=True)
  print 'Verify that no signal is measured from the noise output of source module 2 and 3'
  raw_input('Enter to continue')
  print 'Measure similar noise power from combiner 1'
  raw_input('Enter to continue')
  print 'Measure similar noise power from combiner 2'
  raw_input('Enter to continue')

  output.ucs.set_noise_atten(atten=output.ucs.MAX_ATTEN, verbose=True)
  print 'Measure similar noise power from combiner 1'
  raw_input('Enter to continue')
  print 'Measure similar noise power from combiner 2'
  raw_input('Enter to continue')
  output.ucs.noise_source(enable=False, verbose=True)
  output.ucs.noise_output(enable=False, verbose=True)

  print 'Attach Module 3 noise output to spectrum analyzer using 20dB attenuation'
  raw_input('Enter to continue')
  output.cs.noise_source(enable=True, verbose=True)
  output.cs.noise_output(enable=True, verbose=True)
  output.cs.set_noise_atten(atten=output.cs.MIN_ATTEN, verbose=True)
  print 'Verify that no signal is measured from the noise output of source module 2 and 3'
  raw_input('Enter to continue')
  print 'Measure similar noise power from combiner 1'
  raw_input('Enter to continue')
  print 'Measure similar noise power from combiner 2'
  raw_input('Enter to continue')

  output.cs.set_noise_atten(atten=output.cs.MAX_ATTEN, verbose=True)
  print 'Measure similar noise power from combiner 1'
  raw_input('Enter to continue')
  print 'Measure similar noise power from combiner 2'
  raw_input('Enter to continue')
  output.cs.noise_source(enable=False, verbose=True)
  output.cs.noise_output(enable=False, verbose=True)


  print 'Exit test controller...'
  start=time.time()
  mts_obj.exit()
  print 'Exiting takes %.4f seconds' %(time.time()-start)

# -fin-


