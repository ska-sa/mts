#!/usr/bin/python

from optparse import OptionParser
from mts.mts import MTS
from mts.scpi import SCPI
import numpy, string, time

## Calibrating the MTS output using the R&S FSU spectrum analyser and the SCPI socket interface

# Choosing source and combiner attentuation over range
def which_atten(comb, mod, atten):
  if (atten-atten%(mod.MAX_ATTEN+0.5)) == 0.0:
    src_atten=atten%(mod.MAX_ATTEN+0.5)
    comb_atten=comb.MIN_ATTEN
  else:
    src_atten=mod.MAX_ATTEN
    comb_atten=atten-mod.MAX_ATTEN
  return [src_atten, comb_atten]

# Measure channel power for noise source calibration
def calib_noise_pwr(comb, mod, fsu, atten_range, verbose=False):
  noise_scaling = {'atten': [], 'volt':[], 'pwr': []}

  # set up fsu for power measurement
  channel_bw = (comb.MAX_NOISE - comb.MIN_NOISE)
  fsu.setNoisePwr(channel_bw=channel_bw)

  # switch on power output
  mod.noise_output(enable=True)

  # measure channel power over attenuation range
  for atten_idx in range(len(atten_range)):
    cntr=0
    atten = atten_range[atten_idx]
    print 'Set attenuation: %.2f dB' % atten
    [src_atten, comb_atten] = which_atten(comb, mod, atten)

    # set relevant attenuators
    mod.set_noise_atten(atten=src_atten) # dB
    comb.set_comb_atten(atten=comb_atten) # dB
    # Allowing time for noise setting to stabilize
    time.sleep(2)
    # measure power from combiner detector
    [pwr_mv_per_dbm, temp_mv_per_deg] = comb.get_environment()
    # measure channel power from fsu
    while cntr < 5: # try a couple of times to get around random timeout errors
      cntr += 1
      try:
        channel_power = fsu.getNoisePwr()
        break
      except Exception as e:
        print e
        if cntr==5: raise RuntimeError('Connection to FSU timed out')
    if verbose:
      comb_atten = comb.get_comb_atten() # dB
      print '\tcomb attenuated %.2f dB' % comb_atten
      src_atten = mod.get_noise_atten() # dB
      print '\tsrc attenuated %.2f dB' % src_atten
      print '\tnoise attenuated %.2f dB' % (comb_atten+src_atten)
      print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
    print "Channel power: %f dBm" % channel_power

    # capture measurements
    noise_scaling['atten'].append(atten)
    noise_scaling['volt'].append(pwr_mv_per_dbm)
    noise_scaling['pwr'].append(channel_power)

  # switch off power output
  mod.noise_output(enable=False)
  return noise_scaling

# Measure CW amplitude for valon calibration
def calib_cw_pwr(comb, src, fsu, atten_range, verbose=False):
  cw_scaling = {'freq':[], 'amp':[], 'atten':[], 'volt':[]}

  # switch on power output
  src.cw_output(enable=True)

  # step through all attenuation values
  for atten_idx in range(len(atten_range)):
    cntr=0
    atten = atten_range[atten_idx]
    print atten_idx, 'Set attenuation: %.2f dB' % atten
    [src_atten, comb_atten] = which_atten(comb, src, atten)

    # set relevant attenuators
    src.set_cw_atten(atten=src_atten) # dB
    comb.set_comb_atten(atten=comb_atten) # dB

    # Allowing time for CW setting to stabilize
    time.sleep(3)
    # measure power from combiner detector
    [pwr_mv_per_dbm, temp_mv_per_deg] = comb.get_environment()

    # measure the CW ampl
    while cntr < 5: # try a couple of times to get around random timeout errors
      cntr += 1
      try:
        [freq_hz, amp_dbm] = fsu.cwPeak()
        break
      except Exception as e:
        print e
        if cntr==5: raise RuntimeError('Connection to FSU timed out')
    print "CW at %f MHz has amplitude %f dBm" % (freq_hz/1e6, amp_dbm)

    # capture measurements
    cw_scaling['freq'].append(freq_hz/1e6)
    cw_scaling['amp'].append(amp_dbm)
    cw_scaling['atten'].append(atten)
    cw_scaling['volt'].append(pwr_mv_per_dbm)

    if verbose:
      comb_atten = comb.get_comb_atten() # dB
      print '\tcomb attenuated %.2f dB' % comb_atten
      src_atten = src.get_cw_atten() # dB
      print '\tsrc attenuated %.2f dB' % src_atten
      print '\tnoise attenuated %.2f dB' % (comb_atten+src_atten)
      print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm

  # switch off power output
  src.cw_output(enable=False)
  return cw_scaling



if __name__ == '__main__':

  usage = "\n python %prog [options] <FSU IP> \
\nExample: \
\n python %prog  -p /dev/ttyUSB1 -v /dev/ttyUSB0 -o comb1 192.168.4.186 --src=cs --signal=cw --tofile=combiner1cscaldata"

  parser = OptionParser(usage=usage, version="%prog 0.1")
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
                    help='MTS has 2 outputs available, from \'comb1\' and/or from \'comb2\', default output is \'%default\'.')
  parser.add_option('--src',
                    action='store',
                    dest='src',
                    default='ucs',
                    help='Each output has 2 source attached: and uncorrelated source \'ucs\' and a correlated source \'cs\', default source selected is \'%default\'.')
  parser.add_option('--signal',
                    action='store',
                    dest='signal',
                    default='noise',
                    help='Each calibrated source can produce 2 signals: a Gaussian noise \'noise\' or a CW \'cw\', default signal is \'%default\'.')
  parser.add_option('--tofile',
                    action='store',
                    dest='tofile',
                    default=None,
                    help='Save calibration measurements to CSV file, default is \'%default\'.')
  (opts, args) = parser.parse_args()


  if len(args) < 1:
    parser.print_usage()
    raise SystemExit('Cannot connect to unknown IP')
  fsu_ip = str(args[0]).strip()

  if opts.tofile:
    import os
    noiseout = os.path.splitext(opts.tofile)[0]+'_noise.csv'
    cwout = os.path.splitext(opts.tofile)[0]+'_cw.csv'

##Using SCPI class for comms to FSU R&S Spectrum Analyser
  print 'Connecting to device IP:', fsu_ip
  fsu_obj=SCPI(fsu_ip)
  try:
    fsu_obj.deviceID()
    fsu_obj.reset()
  except Exception as e:
    print "Exception Msg:", e
    fsu_obj.__close__()
    raise RuntimeError('Cannot reach FSU device')

##Connection to MTS for calibration
  print 'Initiating all controller modules...'
  start=time.time()
  mts = MTS(port=opts.tty, baudrate=int(opts.baudrate), valon=opts.cwtty, config_file=opts.config_file)
  print 'Initiation takes %.4f seconds' %(time.time()-start)

# Use mts parameters to set up default FSU environment for calibration
  print '\nConnect output from %s to spectrum analyser' % opts.combiner
  print 'Available frequency range from %f MHz to %f MHz' % (mts.MIN_BASE, mts.MAX_BASE)
  fsu_obj.fsuSetup(freq_start=mts.MIN_BASE, freq_stop=mts.MAX_BASE)

##Verify output measured from combiner is similar for both correlated and uncorrelated sources
  comb = mts.select_combiner(opts.combiner)
  comb.power_temp_sensor(enable=True)
  [pwr_mv_per_dbm, temp_mv_per_deg] = comb.get_environment()
  print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
  print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg
# Start capturing data with all attentuation on min
  comb.set_comb_atten(atten=comb.MIN_ATTEN) # dB
  atten = comb.get_comb_atten() # dB
  print '\tcomb attenuated %.2f dB' % atten

  # calibration masurement for uncorrelated, or correlated source
#   if opts.ucs: src = comb.ucs
#   else: src = comb.cs
  if opts.src == 'ucs': src = comb.ucs
  else: src = comb.cs

  # measure channel power over attenuation range
  min_atten = src.MIN_ATTEN + comb.MIN_ATTEN
  max_atten = src.MAX_ATTEN + comb.MAX_ATTEN
  atten_range = numpy.arange(min_atten, max_atten+0.5, 0.5)

  if opts.signal == 'noise':
##Noise output from source
    noise_calib = calib_noise_pwr(comb=comb, mod=src, fsu=fsu_obj, atten_range=atten_range, verbose=True)

    if opts.tofile:
      try:
        fout = open(noiseout, 'w')
      except IOError:
        sys.stderr.write('Unable to open output file %s \n' % noiseout)
      fout.write('Attenuation [dB], Channel Power [dBm], Volt [mv/dBm]\n')
      for line in range(len(noise_calib['atten'])):
        fout.write('%f, %f, %f\n' % (noise_calib['atten'][line], noise_calib['pwr'][line], noise_calib['volt'][line]))
      fout.close()

  else:
##CW output from source
    min_freq_mhz=max([comb.MIN_CW, comb.MIN_NOISE])
    max_freq_mhz=min([comb.MAX_CW, comb.MAX_NOISE])
#     freq_range = numpy.arange(min_freq_mhz, max_freq_mhz+1)
#     # measure cw amplitude over all available frequencies
#     if opts.tofile:
#       try:
#         fout = open(cwout, 'w')
#       except IOError:
#         sys.stderr.write('Unable to open output file %s \n' % cwout)
#       fout.write('Frequency [MHz], Attenuation [dB], CW Power [dBm], Volt [mv/dBm]\n')
#       fout.close()
    freq_range = numpy.arange(324, max_freq_mhz+1)


    for freq_idx in range(len(freq_range)):
      freq = freq_range[freq_idx]
      print freq_idx, 'CW frequency set to %s MHz' % freq
      src.set_freq(freq_mhz=freq)

      cw_freq_mhz = src.get_freq()
      print '\tcw frequency %s MHz' % cw_freq_mhz

      cw_calib = calib_cw_pwr(comb, src, fsu_obj, atten_range, verbose=True)
      print numpy.median(cw_calib['freq']), freq, numpy.abs(numpy.median(cw_calib['freq'])-freq)
      if numpy.abs(numpy.median(cw_calib['freq'])-freq)>1: raise RuntimeError('FSU did not update')

      if opts.tofile:
        try:
          fout = open(cwout, 'a')
        except IOError:
          sys.stderr.write('Unable to open output file %s \n' % cwout)
        for line in range(len(cw_calib['atten'])):
          fout.write('%f, %f, %f, %f\n' % (freq, cw_calib['atten'][line], cw_calib['amp'][line], cw_calib['volt'][line]))
        fout.close()

  print 'Closing all ports...'
  start=time.time()
  try:
    mts.exit()
    fsu_obj.__close__()
  except:
    pass # socket already closed
  print 'Exiting takes %.4f seconds' %(time.time()-start)

# -fin-


