#! /usr/bin/env python

from optparse import OptionParser
import inspect, signal, string
import valon_synth
from valon_synth import Synthesizer

## API to NRAO valon 5007 library

class TimeoutException(Exception): pass

class MTSvalon(Synthesizer):
  """
  Initialize valon synth to preset state with default values and provide access to interface functions

  @param synth    String: Synthesizer name
  @param port     String: USB port allocated to device when connected
  @param restore  Boolean: If False the synthesizer is initated with factory settings, else the user parameters saved on the valon flash memory is used.

  @return      Handle: Handle to synthesize object
  """
  # Initialize valon synth to preset state with default values
  def __init__(self, synth, port, restore=False, timeout=10):

    def timeout_handler(signum, frame):
      raise TimeoutException()
    if timeout > 0:
      # Warning: the "signal" implementation works only on linux systems
      signal.signal(signal.SIGALRM, timeout_handler)
      signal.alarm(timeout) # triggers alarm in 5 seconds

    try:
      Synthesizer.__init__(self, port)
    except valon_synth.serial.SerialException as err:
      raise RuntimeError("Unable to open serial port.\nError MSG:\n%s"%err)
    except:
      raise

    # Add usage instructions for parent call functions
    self.get_vco_range.__func__.__doc__ = "\
\nReturn the minimum and maximum frequency range of the selected synthesizer VCO. \
\nThe VCO Frequency Range information is used to limit and check the resulting VCO output frequency, \
\nentered in the set frequency request function. \
\n\t@param synth String: Synthesizer name \
\n\t@return      List:   (lowest VCO output frequency, highest VCO output frequency) in MHz \
\n"
    self.set_vco_range.__func__.__doc__ = "\
\nSet the minimum and maximum frequency range of the selected synthesizer VCO. \
\n\t@param synth String:  Synthesizer name \
\n\t@param min   Int:     The lowest VCO output frequency (MHz) that may be set \
\n\t@param max   Int:     The highest VCO output frequency (MHz) that may be set \
\n\t@return      Boolean: Reply message indicating success. \
\n"
    self.get_frequency.__func__.__doc__ = "\
\nReturn the current VCO output frequency for the selected synthesizer. \
\n\t@param synth String:  Synthesizer name \
\n\t@return      Float:   Synthesizer output frequency (MHz) \
\n"
    self.set_frequency.__func__.__doc__ = "\
\nRequest to set the desired frequency (MHz) for the selected synthesizer. \
\nThis is will cause the registers synthesizer to be updated and the new frequency generated. \
\nThe resulting output frequency must be within the range specified in the frequency range. \
\n\t@param synth        String:  Synthesizer name \
\n\t@param freq         Int:     Desired frequency (MHz) \
\n\t@param chan_spacing Float:   Frequency Increment (KHz) to set required output frequency resolution \
\n\t@return             Boolean: Reply message indicating success. \
\n"

    self.get_reference.__func__.__doc__ = "\
\nRequest the input frequency of the reference oscillator. \
\n\t@param  No input parameters \
\n\t@return Int: Reference input frequency (Hz) \
\n"

    self.set_reference.__func__.__doc__ = "\
\nSet the input frequency of the reference oscillator. \
\nThis value must be between 5 MHz and 150 MHz according to the 5007 datasheet. \
\n\t@param freq Int: Reference input frequency (Hz) \
\n\t@return     Boolean: Reply message indicating success. \
\n"

    self.get_rf_level.__func__.__doc__ = "\
\nReturns the current output power level: -4, -1, 2, 5 \
\n\t@param synth String:  Synthesizer name \
\n\t@return      Int:     Ouput power level \
\n"

    self.set_rf_level.__func__.__doc__ = "\
\nAllows user to select one of four output power levels: -4, -1, 2, 5 \
\nThese levels corresponds approximately to some preset output power. \
\n\t@param synth    String:  Synthesizer name \
\n\t@param rf_level Int:     Ouput power level \
\n\t@return         Boolean: Reply message indicating success. \
\n"

    self.get_ref_select.__func__.__doc__ = "\
\nReturns the currently selected reference clock. \
\n\t@param  No input parameters \
\n\t@return Int: 1 for external reference and 0 otherwise \
\n"

    self.set_ref_select.__func__.__doc__ = "\
\nSelects either internal or external reference clock. \
\n\t@parameter e_not_i Int: 1 for external reference and 0 for internal reference \
\n\t@return            Boolean: Reply message indicating success. \
\n"

    self.get_label.__func__.__doc__ = "\
\nRead the assigned synthesizer name. \
\n\t@param synth    String:  Synthesizer name \
\n\t@return         String:  Assigned synthesizer name \
\n"

    self.set_label.__func__.__doc__ = "\
\nLabel the selected synthesizer to suit your application, if desired. \
\nThe maximum length of a name is 16 characters. \
\n\t@param synth    String:  Synthesizer name \
\n\t@param label    String:  Synthesizer alias to assign\
\n\t@return         Boolean: Reply message indicating success. \
\n"

    self.get_phase_lock.__func__.__doc__ = " \
\n Return the VCO lock status of the selected synthesizer. \
\n\t@param synth    String:  Synthesizer name \
\n\t@return         Boolean: Reply message indicating VCO lock status. \
\n"

    self.flash.__func__.__doc__ = "\
\nWrite setup parameters to non-volatile flash memory in the microcontroller board. \
\nThe next time the board is powered up, the registers will be set to the values in the non-volatile flash memory. \
\nIf the board is powered down before the write flash command command is issued, all the data in the registers will be lost. \
\n\t@param  No input parameters \
\n\t@return Boolean: Reply message indicating parameters written to flash. \
\n"

    self.get_options.__func__.__doc__ = "\
\nOptional VCO Settings \
\n\tprint synth.get_options(valon_synth.SYNTH_B) \
\nOutput a list of 4 parameters, which can be 0 (disabled) or 1(enabled) \
\ndouble: The reference doubler is used to enable a multiply by 2 function before the internal reference divider. \
\n\tEnable the doubler when using a 5 MHz external reference frequency. \
\n\tWhen using the internal 10 MHz reference the doubler should be disabled. \
\nhalf: The reference divide by 2 is used to enable a divide by 2 function after the intercal reference divider. \
\n\tWhen enabled, the input to phase-frequency detector will have a 50% duty cycle which will allow for faster lock up time. \
\n\tIn order to use this mode a 20 MHz external reference would have to be available. \
\n\tFor normal operations set the reference div by 2 to disabled. \
\nr: ?? \
\nspur: Low noise mode vs Low spur mode. \
\n\tLow noise mode affects the operation of the fractional synthesizer, \
\n\tand this mode will produce the lowest phase noise but there may be some spurious output signals. \
\n\tLow spur mode will reduce spurious output response but the overall phase noise will be higher. \
\n"

    self.set_options.__func__.__doc__ = "\
\nOptional VCO Settings for a specified synthesizer \
\nOutput a list of 4 parameters, which can be 0 (disabled) or 1(enabled) \
\ndouble: The reference doubler is used to enable a multiply by 2 function before the internal reference divider. \
\n\tEnable the doubler when using a 5 MHz external reference frequency. \
\n\tWhen using the internal 10 MHz reference the doubler should be disabled. \
\nhalf: The reference divide by 2 is used to enable a divide by 2 function after the intercal reference divider. \
\n\tWhen enabled, the input to phase-frequency detector will have a 50% duty cycle which will allow for faster lock up time. \
\n\tIn order to use this mode a 20 MHz external reference would have to be available. \
\n\tFor normal operations set the reference div by 2 to disabled. \
\nr: ?? \
\nspur: Low noise mode vs Low spur mode. \
\n\tLow noise mode affects the operation of the fractional synthesizer, \
\n\tand this mode will produce the lowest phase noise but there may be some spurious output signals. \
\n\tLow spur mode will reduce spurious output response but the overall phase noise will be higher. \
\n"
    if not restore:
      ## Set valon to use internal reference clock
      try:
        if self.get_ref_select() =="1":
          self.set_rf_select(e_not_i=0)
#         ## Set frequency to 2.4 GHz
#         self.set_frequency(synth, freq=2465)
#         ## Set rf level to be minimum available
#         self.set_rf_level(synth,-4)
      except TimeoutException:
        raise RuntimeError('Could not connect to Valon')
    self.synth=synth

  # Add MTS extensions to parent class
  def set_cw_freq(self, freq_mhz):
    """ \
\nSet the desired output frequency (MHz) for the synthesizer. \
\n\t@param  freq_mhz Int:     Desired frequency (MHz) \
\n\t@return          Boolean: Reply message indicating success. \
"""
    [min_mhz, max_mhz] = self.get_vco_range(self.synth)
    freq_set_success = self.set_frequency(self.synth, freq=freq_mhz, chan_spacing=1.) # Frequency step to 1 KHz resolution default
    if not freq_set_success:
      raise RuntimeError('Frequency request failed:\nfunction %s, line no %s\n' %(__name__, inspect.currentframe().f_lineno))
    return freq_set_success

  def get_cw_freq(self):
    """ \
\nReturn the current output frequency for the synthesizer. \
\n\t@param  No input parameters \
\n\t@return Float:   Synthesizer output frequency (MHz) \
"""
    return self.get_frequency(self.synth)

  def set_ref_freq(self, freq_mhz):
    """ \
\nSet the input frequency (MHz) of the reference oscillator. \
\n\t@param freq_mhz Int: Reference input frequency (MHz) \
\n\t@return         Boolean: Reply message indicating success. \
"""
    # Reference freq must be between 5 MHz and 150 MHz according to the 5007 datasheet.
    min_mhz = 5
    max_mhz = 150
    if (freq_mhz < min_mhz) or (freq_mhz > max_mhz):
      raise RuntimeError('Frequency request out of range: Specify a frequency between %d MHz and %d MHz' %(min_mhz, max_mhz))
    freq_set_success = self.set_reference(int(freq_mhz)*1e6)
    if not freq_set_success:
      raise RuntimeError('Frequency request failed:\nfunction %s, line no %s\n' %(__name__, inspect.currentframe().f_lineno))
    return freq_set_success

  def set_external_ref(self):
    """ \
\nSet external reference clock. \
\n\t@param  No input parameters \
\n\t@return Boolean: Reply message indicating success. \
"""
    ref_set_success = synth.set_ref_select(e_not_i=1)
    if not ref_set_success:
      raise RuntimeError('External reference request failed:\nfunction %s, line no %s\n' %(__name__, inspect.currentframe().f_lineno))
    return ref_set_success


if __name__ == '__main__':

  parser = OptionParser(version="%prog 0.1")
  parser.add_option('-p', '--port',
                    action='store',
                    dest='tty',
                    default='/dev/ttyUSB0',
                    help='Set Serial Port, default is \'%default\'.')
  parser.add_option('-f', '--freq',
                    action='store',
                    dest='cw_freq',
                    default=None, # MHz
                    type=int,
                    help='Set frequency for CW test signal (values specified in MHz, e.g. 2465 for 2.465GHz).')
  parser.add_option('-r', '--ref',
                    action='store',
                    dest='ref_freq',
                    default=None, # MHz
                    type=int,
                    help='Set input reference frequency (MHz).')
  parser.add_option('-s', '--save',
                    action='store_true',
                    dest='flash',
                    default=False,
                    help='Write settings to non-volatile memory.')
  parser.add_option('--restore',
                    action='store_true',
                    dest='restore',
                    default=False,
                    help='Do not initiate default synthesizer, use values as read from flash memory.')
  (opts, args) = parser.parse_args()
 
  # MTS uses only one of the available synthesizers (currently SYNTH 2)
  synth = MTSvalon(valon_synth.SYNTH_B, opts.tty, restore=opts.restore)

  print synth.get_vco_range.__doc__
  print synth.set_vco_range.__doc__

  print synth.get_rf_level.__doc__
  print synth.set_rf_level.__doc__

  print synth.get_label.__doc__
  print synth.set_label.__doc__

  # Sequence is important here -- always set the reference clock first if you want to set it
  # Set external reference clock
  print synth.get_reference.__doc__
  print synth.set_reference.__doc__
  if opts.ref_freq:
    synth.set_ref_freq(freq_mhz=opts.ref_freq)
  print 'Reference frequency set to %d MHz' % (synth.get_reference()/1e6)

  print synth.get_ref_select.__doc__
  print synth.set_ref_select.__doc__
  print synth.set_external_ref.__doc__

  # Set CW signal frequency
  print synth.get_frequency.__doc__
  print synth.set_frequency.__doc__
  if opts.cw_freq:
    synth.set_cw_freq(freq_mhz=opts.cw_freq)
  print 'CW frequency set to %s MHz' % synth.get_cw_freq()
  print synth.get_cw_freq.__doc__
  print synth.set_cw_freq.__doc__


  print synth.get_phase_lock.__doc__
  if synth.get_phase_lock(valon_synth.SYNTH_B):
    print 'Synthesizer "%s" is locked' % (string.strip(synth.get_label(valon_synth.SYNTH_B))) 
  else:
    print 'Synthesizer "%s" is unlocked' % (string.strip(synth.get_label(valon_synth.SYNTH_B))) 

  print synth.flash.__doc__
  if opts.flash:
    if synth.flash():
      print 'New settings written to non-volatile memory'
    else:
      raise RuntimeError('Could not write to memory:\nfunction %s, line no %s\n' %(__name__, inspect.currentframe().f_lineno))

  print synth.get_options.__doc__
  print synth.set_options.__doc__

  print 'Closing connection to valon'
  synth.conn.close()

# -fin-
