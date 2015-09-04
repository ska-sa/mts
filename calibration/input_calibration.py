#!/usr/bin/python
import numpy, pylab, time

def write_calib_file(filename, atten, ucs_volt, ucs_pwr, cs_volt, cs_pwr):
  fout=open(filename, 'w')
  try: fout.write('Attenuation [dB], UCS Amplitude [mV/dBm], UCS Power [dBm], CS Amplitude [mV/dBm], CS Power [dBm]\n')
  except IOError: raise RuntimeError('Unable to access output file %s \n' % filename)
  for idx in range(len(atten)):
    fout.write('%f, %f, %f, %f, %f\n' % (atten[idx], ucs_volt[idx], ucs_pwr[idx], cs_volt[idx], cs_pwr[idx]))
  fout.close()

def smooth_outliers(vector, verbose=False):
  the_diff = numpy.diff(vector)
  the_diff = the_diff - numpy.mean(the_diff)
  threshold = 3*numpy.std(the_diff)
  diff_idx=numpy.nonzero(abs(the_diff) > threshold)[0]

  vector_idx = []
  for idx in diff_idx:
    if the_diff[idx]>0:
      vector_idx.append(idx+1)
    else:
      vector_idx.append(idx)
  vector_idx = numpy.unique(vector_idx)

  cal_vector = numpy.array(vector)
  for idx in vector_idx:
    if idx < 3: cal_vector[idx] = cal_vector[3]
    elif idx > len(cal_vector)-3: cal_vector[idx] = cal_vector[idx-3]
    else: cal_vector[idx] = numpy.median(cal_vector[idx-3:idx+3])

  if verbose:
    pylab.ion()
    pylab.figure()
    pylab.plot(the_diff)
    pylab.axhline(y=numpy.mean(the_diff),color='y')
    pylab.axhline(y=threshold, color='r')
    pylab.axhline(y=-threshold, color='r')
    for idx in diff_idx: pylab.axvline(x=idx, color='k')
    pylab.draw()
    pylab.draw()
    time.sleep(1)
    pylab.close('all')
    pylab.ioff()

  return cal_vector

# read the noise measurements from the MTS and generates a calibration file
def calibrate_noise(infile, verbose=False):
  atten=[]
  pwr  =[]
  volt =[]
  try:
    fin = open(infile, 'r')
  except IOError:
    raise RuntimeError('Unable to open input file %s \n' % infile)
  # read header
  fin.readline()
  # read calibration data
  for line in fin.readlines():
    noise_data = numpy.array(line.strip().split(','), dtype=float)
    atten.append(noise_data[0])
    pwr.append(noise_data[1])
    volt.append(noise_data[2])
  fin.close()

  cal_volt = smooth_outliers(volt, verbose=verbose)
  cal_pwr = smooth_outliers(pwr, verbose=verbose)

  if verbose:
    pylab.ion()
    pylab.figure()
    pylab.subplot(221)
    pylab.plot(atten, volt)
    pylab.subplot(222)
    pylab.plot(atten, cal_volt)
    pylab.subplot(223)
    pylab.plot(atten, pwr)
    pylab.subplot(224)
    pylab.plot(atten, cal_pwr)
    pylab.draw()
    pylab.draw()
    time.sleep(3)
    pylab.close('all')
    pylab.ioff()

  return [atten, cal_volt, cal_pwr]

def calibrate_cw(infile, verbose=False):
  frequency_data={}
  try:
    fin = open(infile, 'r')
  except IOError:
    sys.stderr.write('Unable to open output file %s \n' % infile)

  # read header
  fin.readline()
  # read calibration data
  for line in fin.readlines():
    [freq, atten, pwr, volt] = numpy.array(line.strip().split(','), dtype=float)
    if frequency_data.has_key(freq):
      frequency_data[freq]['atten'].append(atten)
      frequency_data[freq]['pwr'].append(pwr)
      frequency_data[freq]['volt'].append(volt)
    else:
      frequency_data[freq] = {'atten': [atten], 'pwr': [pwr], 'volt': [volt]}
  fin.close()

  attenuation=[]
  powers=[]
  volts=[]
  for key in frequency_data.keys():
    atten = frequency_data[key]['atten']
    pwr = frequency_data[key]['pwr']
    volt = frequency_data[key]['volt']

    cal_volt = smooth_outliers(volt, verbose=verbose)
    cal_pwr = smooth_outliers(pwr, verbose=verbose)

    if verbose:
      pylab.ion()
      pylab.figure()
      pylab.subplot(221)
      pylab.plot(atten, volt)
      pylab.title('Frequency %f'%key)
      pylab.subplot(222)
      pylab.plot(atten, cal_volt)
      pylab.subplot(223)
      pylab.plot(atten, pwr)
      pylab.subplot(224)
      pylab.plot(atten, cal_pwr)
      pylab.draw()
      pylab.draw()
      time.sleep(3)
      pylab.close('all')
      pylab.ioff()

    attenuation.append(atten)
    powers.append(cal_pwr)
    volts.append(cal_volt)

  if verbose:
    pylab.ion()
    pylab.figure()
    pylab.subplot(211)
    pylab.plot(numpy.min(powers, axis=0),'b')
    pylab.plot(numpy.median(powers, axis=0),'g')
    pylab.plot(numpy.max(powers, axis=0),'r')
    pylab.subplot(212)
    pylab.plot(numpy.min(volts, axis=0),'b')
    pylab.plot(numpy.median(volts, axis=0),'g')
    pylab.plot(numpy.max(volts, axis=0),'r')
    pylab.draw()
    pylab.draw()
    time.sleep(3)
    pylab.close('all')
    pylab.ioff()

  return [numpy.median(attenuation, axis=0), numpy.median(volts, axis=0), numpy.median(powers, axis=0)]

if __name__ == '__main__':

  # Read measured noise output and generate calibration charts
  [atten1ucs, volt1ucs, pwr1ucs] = calibrate_noise('combiner1ucscaldata_noise.csv', verbose=False)
  [atten1cs, volt1cs, pwr1cs]    = calibrate_noise('combiner1cscaldata_noise.csv', verbose=False)
  [atten2ucs, volt2ucs, pwr2ucs] = calibrate_noise('combiner2ucscaldata_noise.csv', verbose=False)
  [atten2cs, volt2cs, pwr2cs]    = calibrate_noise('combiner2cscaldata_noise.csv', verbose=False)
  atten=atten1ucs
  ucs_volt = numpy.mean([volt1ucs, volt2ucs], axis=0)
  ucs_pwr  = numpy.mean([pwr1ucs, pwr2ucs], axis=0)
  cs_volt  = numpy.mean([volt1cs, volt2cs], axis=0)
  cs_pwr   = numpy.mean([pwr1cs, pwr2cs], axis=0)

  filename = 'noise_calib_table.data'
  write_calib_file(filename, atten, ucs_volt, ucs_pwr, cs_volt, cs_pwr)

  pylab.figure()
  pylab.subplots_adjust(hspace=.7)
  pylab.subplots_adjust(wspace=.7)
  pylab.subplot(211)
  pylab.plot(atten1ucs, volt1ucs, 'b', atten1cs, volt1cs, 'r')
  pylab.plot(atten2ucs, volt2ucs, 'c', atten2cs, volt2cs, 'm')
  pylab.plot(atten, ucs_volt, 'k', atten, cs_volt, 'g')
  pylab.legend(['ucs1', 'cs1', 'ucs2', 'cs2', 'ucs','cs'])
  pylab.xlabel('Attenuation [dB]')
  pylab.ylabel('Volt [mV/dBm]')
  pylab.title('Noise calibration')
  pylab.subplot(212)
  pylab.plot(atten1ucs, pwr1ucs, 'b', atten1cs, pwr1cs, 'r')
  pylab.plot(atten2ucs, pwr2ucs, 'c', atten2cs, pwr2cs, 'm')
  pylab.plot(atten, ucs_pwr, 'k', atten, cs_pwr, 'g')
  pylab.legend(['ucs1', 'cs1', 'ucs2', 'cs2', 'ucs','cs'])
  pylab.xlabel('Attenuation [dB]')
  pylab.ylabel('Power [dBm]')

  # Read measured cw output and generate calibration charts
  [atten1ucs, volt1ucs, pwr1ucs] = calibrate_cw('combiner1ucscaldata_cw.csv', verbose=False)
  [atten1cs, volt1cs, pwr1cs]    = calibrate_cw('combiner1cscaldata_cw.csv', verbose=False)
  [atten2ucs, volt2ucs, pwr2ucs] = calibrate_cw('combiner2ucscaldata_cw.csv', verbose=False)
  [atten2cs, volt2cs, pwr2cs]    = calibrate_cw('combiner2cscaldata_cw.csv', verbose=False)
  atten=atten1ucs
  ucs_volt = numpy.mean([volt1ucs, volt2ucs], axis=0)
  ucs_pwr  = numpy.mean([pwr1ucs, pwr2ucs], axis=0)
  cs_volt  = numpy.mean([volt1cs, volt2cs], axis=0)
  cs_pwr   = numpy.mean([pwr1cs, pwr2cs], axis=0)

  filename = 'cw_calib_table.data'
  write_calib_file(filename, atten, ucs_volt, ucs_pwr, cs_volt, cs_pwr)

  pylab.figure()
  pylab.subplots_adjust(hspace=.7)
  pylab.subplots_adjust(wspace=.7)
  pylab.subplot(211)
  pylab.plot(atten1ucs, volt1ucs, 'b', atten1cs, volt1cs, 'r')
  pylab.plot(atten2ucs, volt2ucs, 'c', atten2cs, volt2cs, 'm')
  pylab.plot(atten, ucs_volt, 'k', atten, cs_volt, 'g')
  pylab.legend(['ucs1', 'cs1', 'ucs2', 'cs2', 'ucs','cs'])
  pylab.xlabel('Attenuation [dB]')
  pylab.ylabel('Volt [mV/dBm]')
  pylab.title('CW calibration')
  pylab.subplot(212)
  pylab.plot(atten1ucs, pwr1ucs, 'b', atten1cs, pwr1cs, 'r')
  pylab.plot(atten2ucs, pwr2ucs, 'c', atten2cs, pwr2cs, 'm')
  pylab.plot(atten, ucs_pwr, 'k', atten, cs_pwr, 'g')
  pylab.legend(['ucs1', 'cs1', 'ucs2', 'cs2', 'ucs','cs'])
  pylab.xlabel('Attenuation [dB]')
  pylab.ylabel('Power [dBm]')
  pylab.show()

# -fin-

