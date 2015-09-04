#!/usr/bin/python
import numpy, pylab, time

# construct lookup table from calibration measurements
def read_calib_data(calib_file):
  try:
    fin = open(calib_file, 'r')
  except IOError:
    sys.stderr.write('Unable to open output file %s \n' % calib_file)

  ucs_cal=[]
  cs_cal=[]
  # read header
  fin.readline()
  # read calibration data
  for line in fin.readlines():
    [atten, ucs_volt, ucs_pwr, cs_volt, cs_pwr] = numpy.array(line.strip().split(','), dtype=float)
    ucs_cal.append([atten, ucs_volt, ucs_pwr])
    cs_cal.append([atten, cs_volt, cs_pwr])
  fin.close()

  return [ucs_cal, cs_cal]

def set_pwr(cal_tbl, pwr_dbm):
  cal_tbl = numpy.array(cal_tbl)
  if pwr_dbm < min(cal_tbl[:,2]): raise RuntimeError('Power level %f dBm to low. Min power available %f dBm\n'%(pwr_dbm, min(cal_tbl[:,2])))
  if pwr_dbm > max(cal_tbl[:,2]): raise RuntimeError('Power level %f dBm to high. Max power available %f dBm\n'%(pwr_dbm, max(cal_tbl[:,2])))
  pwr_idx = numpy.argmin(abs(pwr_dbm - cal_tbl[:,2]))
  atten = cal_tbl[pwr_idx,0]
  print "\tClosest power level of %f dBm, set attenuation %f dB" % (cal_tbl[pwr_idx,2], cal_tbl[pwr_idx,0])

  # Choosing source and combiner attentuation over range
  MAX_ATTEN = 31.5 # use config value when mts up and running
  if (atten-atten%MAX_ATTEN) > 0:
    src_atten = (atten-atten%MAX_ATTEN)
    cmb_atten = atten-src_atten
  else:
    src_atten = atten
    cmb_atten = 0.0

  return [src_atten, cmb_atten]

def get_pwr(cal_tbl, pwr_sensor): # pwr_sensor in mV/dBm
  cal_tbl = numpy.array(cal_tbl)
  amp_idx = numpy.argmin(abs(pwr_sensor - cal_tbl[:,1]))
  print "Amplitude sensor reading of %f mV/dBm translates to %f dBm power" %(cal_tbl[amp_idx,1], cal_tbl[amp_idx,2])
  return cal_tbl[amp_idx,2]


print '\nNoise calibration table'

[ucs_noise, cs_noise] = read_calib_data('noise_calib_table.data')
[src_atten, cmb_atten] = set_pwr(ucs_noise, -27)
print 'Set src atten to %f dB and output atten to %f dB' % (src_atten, cmb_atten)
[src_atten, cmb_atten] = set_pwr(cs_noise, -40)
print 'Set src atten to %f dB and output atten to %f dB' % (src_atten, cmb_atten)

get_pwr(ucs_noise, pwr_sensor=1.5)


print '\nCW calibration table'

[ucs_cw, cs_cw] = read_calib_data('cw_calib_table.data')
[src_atten, cmb_atten] = set_pwr(ucs_cw, -10)
print 'Set src atten to %f dB and output atten to %f dB' % (src_atten, cmb_atten)
[src_atten, cmb_atten] = set_pwr(cs_cw, -38)
print 'Set src atten to %f dB and output atten to %f dB' % (src_atten, cmb_atten)

get_pwr(ucs_cw, pwr_sensor=0)

pylab.figure()
ucs_cw = numpy.array(ucs_cw)
ucs_noise = numpy.array(ucs_noise)
pylab.plot(ucs_cw[:,0], ucs_cw[:,2], 'b')
pylab.plot(ucs_noise[:,0], ucs_noise[:,2], 'r')
pylab.xlabel('Attenuation [dB]')
pylab.ylabel('FSU integrated power [dBm]')
pylab.legend(('UCS CW', 'UCS Noise'),0)
pylab.title('Uncorrelated calibration of attenuation to power')
pylab.savefig('uncorr_cal.png')

pylab.figure()
cs_cw = numpy.array(cs_cw)
cs_noise = numpy.array(cs_noise)
pylab.plot(cs_cw[:,0], cs_cw[:,2], 'b')
pylab.plot(cs_noise[:,0], cs_noise[:,2], 'r')
pylab.xlabel('Attenuation [dB]')
pylab.ylabel('FSU integrated power [dBm]')
pylab.legend(('CS CW', 'CS Noise'),0)
pylab.title('Correlated calibration of attenuation to power')
pylab.savefig('corr_cal.png')


pylab.show()
# -fin-
