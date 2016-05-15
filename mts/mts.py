#!/usr/bin/python

from mts_api import MTSAPI
from optparse import OptionParser
from valon_api import MTSvalon
import numpy
import sys
import time
import valon_synth

import mts_config

DEBUG_CMD = False  # True
DEBUG_COMM = False  # True
VERBOSE = False  # True


# output cmd send to register on serial port
def debug_cmd(addr, cmd):
    print hex(addr), "0x%08x" % cmd


# verify cmd sent to match data read from register via port
def verify_cmd(data, cmd):
    if DEBUG_COMM:
        print 'data = 0x%08x' % (data)
    if ('0x%08x' % data) != ('0x%08x' % cmd):
        raise RuntimeError('Port read error:\nCmd sent 0x%08x not same as cmd read 0x%08x' % (cmd, data))


# construct lookup table from calibration measurements
def read_calib_data(calib_file):
    try:
        fin = open(calib_file, 'r')
    except IOError:
        raise RuntimeError('Unable to open output file %s \n' % calib_file)
    ucs_cal = []
    cs_cal = []
    # read header
    fin.readline()
    # read calibration data
    for line in fin.readlines():
        [atten, ucs_volt, ucs_pwr, cs_volt, cs_pwr] = numpy.array(line.strip().split(','), dtype=float)
        ucs_cal.append([atten, ucs_volt, ucs_pwr])
        cs_cal.append([atten, cs_volt, cs_pwr])
    fin.close()
    return [ucs_cal, cs_cal]


class mts_mod(MTSvalon):
    device = {
        "ad7888": {
            "channel": 0,
            "register": 1,
            "init": [0x3000, 0x800],
            "set_mask": 0x00010000
        },

        "max7301": {
            "channel": 1,
            "register": 2,
            "init": [0x401, 0x9d5, 0xa55, 0xf55],
            "set_mask": 0x00010000
        }
    }

    component = {
        "ns": {
            "channel": 1,
            "register": 2,
            "cmd": [0x2600, 0x2400, 0x3f00],
            "set_mask": 0x00010000,
        },

        "ns_switch": {
            "channel": 1,
            "register": 2,
            "cmd": [0x2500],
            "set_mask": 0x00010000,
        },

        "ns_atten": {
            "channel": 2,
            "register": 3,
            "cmd": [],
            "set_mask": 0x00000100,
        },

        "cw": {
            "channel": 1,
            "register": 2,
            "cmd": [0x3c00, 0x3d00],
            "set_mask": 0x00010000,
        },

        "cw_switch": {
            "channel": 1,
            "register": 2,
            "cmd": [0x3e00],
            "set_mask": 0x00010000,
        },

        "cw_atten": {
            "channel": 3,
            "register": 3,
            "cmd": [],
            "set_mask": 0x01000000,
        },

        "lock": {
            "channel": 1,
            "register": 2,
            "cmd": [0xa700],
            "set_mask": 0x00010000,
        },

        "pwr_switch": {
            "channel": 1,
            "register": 2,
            "cmd": [0x3c00],
            "set_mask": 0x00010000,
        }
    }

    def __init__(self, mts_obj, module, valon=None, synth=None):

        for dev in self.device.keys():
            if VERBOSE:
                print "init", dev
            # use reg_chanelsel register to identify device
            addr = mts_obj.__get_address__(mod=module, reg=0)
            cmd = self.device[dev]["channel"]
            if DEBUG_CMD:
                debug_cmd(addr, cmd)
            mts_obj.write(addr, cmd)
            # verify data read back from register
            verify_cmd(mts_obj.read(addr), cmd)

            # use device write register (reg_ad7888_wr, reg_max7301_wr) to send init data
            addr = mts_obj.__get_address__(mod=module, reg=self.device[dev]['register'])
            for cmd in self.device[dev]["init"]:
                set_cmd = self.device[dev]["set_mask"] | cmd
                if DEBUG_CMD:
                    debug_cmd(addr, set_cmd)
                mts_obj.write(addr, set_cmd)
                # verify data read back from register
                verify_cmd(mts_obj.read(addr), set_cmd)
                if DEBUG_CMD:
                    debug_cmd(addr, cmd)
                mts_obj.write(addr, cmd)
                # verify data read back from register
                verify_cmd(mts_obj.read(addr), cmd)
            if DEBUG_CMD or DEBUG_COMM:
                print
        self.module = module
        self.mts = mts_obj
        self.synth = synth
        self.valon = valon

    def get_freq(self, verbose=False, timeout=-1):
        """
        Returns the current output frequency (MHz) of the CW signal.

        @param verbose Boolean: Optional parameter to enable explicit output of command
        @param timeout Integer: Allow wait for ever if < 0 , else valon connection will stop trying after timeout seconds

        @return        Float  : Synthesizer output frequency (MHz)
        """
        self.select_valon(verbose=verbose)
        if self.valon and self.synth:
            # Set up serial comms to valon controller
            try:
                synth = MTSvalon(self.synth, self.valon, timeout=timeout)
                synth_cw_freq = synth.get_frequency(synth=self.synth)
            except Exception as e:
                raise RuntimeError('Cannot connect to Synthesizer: %s' % e)
        return synth_cw_freq

    def set_freq(self, freq_mhz, verbose=False, timeout=-1):
        """
        Sets the frequency (MHz) of the CW signal

        @param freq_mhz Float: Frequency (MHz) to set synthesizer
        @param verbose  Boolean: [Optional] Verbose output messages
        @param timeout Integer: Allow wait for ever if < 0 , else valon connection will stop trying after timeout seconds
        """
        self.select_valon(verbose=verbose)
        if self.valon and self.synth:
            # Set up serial comms to valon controller
            synth = MTSvalon(self.synth, self.valon, timeout=timeout)
            synth.set_frequency(synth=self.synth, freq=freq_mhz)
            if VERBOSE or verbose:
                print 'CW frequency set to %s MHz' % synth.get_frequency(synth=self.synth)
        else:
            raise RuntimeError('No valon synth available for this module')

    def cw_source(self, enable=False, verbose=False):
        """
        Enable Valon CW source

        @param enable  Boolean: True for on and False for off
        @param verbose Boolean: Verbose output messages
        """
        if VERBOSE or verbose:
            print 'Enable cw source', enable
        cw = self.component['cw']
        # use reg_chanelsel register to identify device
        addr = self.mts.__get_address__(mod=self.module, reg=0)
        cmd = cw["channel"]
        if DEBUG_CMD:
            debug_cmd(addr, cmd)
        self.mts.write(addr, cmd)
        verify_cmd(self.mts.read(addr), cmd)  # verify data read back from register
        # use device write register (reg_max7301_wr) to send data
        addr = self.mts.__get_address__(mod=self.module, reg=cw['register'])
        for cmd in cw["cmd"]:
            set_cmd = cw["set_mask"] | cmd
            if DEBUG_CMD:
                debug_cmd(addr, (set_cmd | enable))
            self.mts.write(addr, (set_cmd | enable))
            verify_cmd(self.mts.read(addr), (set_cmd | enable))  # verify data read back from register
            if DEBUG_CMD:
                debug_cmd(addr, (cmd | enable))
            self.mts.write(addr, (cmd | enable))
            verify_cmd(self.mts.read(addr), (cmd | enable))  # verify data read back from register
        if DEBUG_CMD or DEBUG_COMM:
            print

    def noise_source(self, enable=False, verbose=False):
        """
        Enable noise source

        @param enable  Boolean: True for on and False for off
        @param verbose Boolean: Verbose output messages
        """
        if VERBOSE or verbose:
            print 'Enable noise source', repr(enable)
        ns = self.component['ns']
        # use reg_chanelsel register to identify component
        addr = self.mts.__get_address__(mod=self.module, reg=0)
        cmd = ns["channel"]
        if DEBUG_CMD:
            debug_cmd(addr, cmd)
        self.mts.write(addr, cmd)
        verify_cmd(self.mts.read(addr), cmd)  # verify data read back from register
        # use component write register (reg_max7301_wr) to send data
        addr = self.mts.__get_address__(mod=self.module, reg=ns['register'])
        for cmd in ns["cmd"]:
            set_cmd = ns["set_mask"] | cmd
            if DEBUG_CMD:
                debug_cmd(addr, (set_cmd | enable))
            self.mts.write(addr, (set_cmd | enable))
            verify_cmd(self.mts.read(addr), (set_cmd | enable))  # verify data read back from register
            if DEBUG_CMD:
                debug_cmd(addr, (cmd | enable))
            self.mts.write(addr, (cmd | enable))
            verify_cmd(self.mts.read(addr), (cmd | enable))  # verify data read back from register
        if DEBUG_CMD or DEBUG_COMM:
            print

    def power_temp_sensor(self, enable=False, verbose=False):
        """
        Enable output from power detector

        @param enable  Boolean: True for on and False for off
        @param verbose Boolean: Verbose output messages
        """
        if VERBOSE or verbose:
            print 'Enable power sensor', repr(enable)
        ns = self.component['pwr_switch']
        # use reg_chanelsel register to identify component
        addr = self.mts.__get_address__(mod=self.module, reg=0)
        cmd = ns["channel"]
        if DEBUG_CMD:
            debug_cmd(addr, cmd)
        self.mts.write(addr, cmd)
        verify_cmd(self.mts.read(addr), cmd)  # verify data read back from register
        # use component write register (reg_max7301_wr) to send data
        addr = self.mts.__get_address__(mod=self.module, reg=ns['register'])
        for cmd in ns["cmd"]:
            set_cmd = ns["set_mask"] | cmd
            if DEBUG_CMD:
                debug_cmd(addr, (set_cmd | enable))
            self.mts.write(addr, (set_cmd | enable))
            verify_cmd(self.mts.read(addr), (set_cmd | enable))  # verify data read back from register
            if DEBUG_CMD:
                debug_cmd(addr, (cmd | enable))
            self.mts.write(addr, (cmd | enable))
            verify_cmd(self.mts.read(addr), (cmd | enable))  # verify data read back from register
        if DEBUG_CMD or DEBUG_COMM:
            print

    def cw_output(self, enable=True, verbose=False):
        """
        Enable output by swithing on CW signal path

        @param enable  Boolean: True for on and False for off
        @param verbose Boolean: Verbose output messages
        """
        if VERBOSE or verbose:
            print 'Enable cw signal', enable
        switch_setting = (not enable)
        # switch must be on (1) to prevent signal from flowing
        cws = self.component['cw_switch']
        # use reg_chanelsel register to identify device
        addr = self.mts.__get_address__(mod=self.module, reg=0)
        cmd = cws["channel"]
        if DEBUG_CMD:
            debug_cmd(addr, cmd)
        self.mts.write(addr, cmd)
        verify_cmd(self.mts.read(addr), cmd)  # verify data read back from register
        # use device write register (reg_max7301_wr) to send data
        addr = self.mts.__get_address__(mod=self.module, reg=cws['register'])
        for cmd in cws["cmd"]:
            set_cmd = cws["set_mask"] | cmd
            if DEBUG_CMD:
                debug_cmd(addr, (set_cmd | switch_setting))
            self.mts.write(addr, (set_cmd | switch_setting))
            verify_cmd(self.mts.read(addr), (set_cmd | switch_setting))  # verify data read back from register
            if DEBUG_CMD:
                debug_cmd(addr, (cmd | switch_setting))
            self.mts.write(addr, (cmd | switch_setting))
            verify_cmd(self.mts.read(addr), (cmd | switch_setting))  # verify data read back from register
        if DEBUG_CMD or DEBUG_COMM:
            print

    def noise_output(self, enable=True, verbose=False):
        """
        Enable output by swithing on noise signal path

        @param enable  Boolean: True for on and False for off
        @param verbose Boolean: Verbose output messages
        """
        if VERBOSE or verbose:
            print 'Enable noise output', enable
        switch_setting = (not enable)
        nss = self.component['ns_switch']
        # use reg_chanelsel register to identify device
        addr = self.mts.__get_address__(mod=self.module, reg=0)
        cmd = nss["channel"]
        if DEBUG_CMD:
            debug_cmd(addr, cmd)
        self.mts.write(addr, cmd)
        verify_cmd(self.mts.read(addr), cmd)  # verify data read back from register
        # use device write register (reg_max7301_wr) to send data
        addr = self.mts.__get_address__(mod=self.module, reg=nss['register'])
        for cmd in nss["cmd"]:
            set_cmd = nss["set_mask"] | cmd
            if DEBUG_CMD:
                debug_cmd(addr, (set_cmd | switch_setting))
            self.mts.write(addr, (set_cmd | switch_setting))
            verify_cmd(self.mts.read(addr), (set_cmd | switch_setting))  # verify data read back from register
            if DEBUG_CMD:
                debug_cmd(addr, (cmd | switch_setting))
            self.mts.write(addr, (cmd | switch_setting))
            verify_cmd(self.mts.read(addr), (cmd | switch_setting))  # verify data read back from register
        if DEBUG_CMD or DEBUG_COMM:
            print

    def set_cw_atten(self, atten, verbose=False):
        """
        Set attenuator in CW signal path

        @param atten   Float: Amount of attenuation (dB) to apply
        @param verbose Boolean: Verbose output messages
        """
        if VERBOSE or verbose:
            print 'Setting CW attenuation to ', atten, 'dB'
        step = int(atten*2)
        cwatten = self.component['cw_atten']
        # use reg_chanelsel register to identify device
        addr = self.mts.__get_address__(mod=self.module, reg=0)
        cmd = cwatten["channel"]
        if DEBUG_CMD:
            debug_cmd(addr, cmd)
        self.mts.write(addr, cwatten["channel"])
        verify_cmd(self.mts.read(addr), cmd)  # verify data read back from register
        # use device write register (reg_zx76_wr) to send data
        addr = self.mts.__get_address__(mod=self.module, reg=cwatten['register'])
        if DEBUG_CMD:
            debug_cmd(addr, (cwatten["set_mask"] + (step << 16)))
        self.mts.write(addr, (cwatten["set_mask"] + (step << 16)))
        verify_cmd(self.mts.read(addr), (cwatten["set_mask"] + (step << 16)))  # verify data read back from register
        if DEBUG_CMD:
            debug_cmd(addr, (step << 16))
        self.mts.write(addr, (step << 16))
        verify_cmd(self.mts.read(addr), (step << 16))  # verify data read back from register
        if DEBUG_CMD or DEBUG_COMM:
            print

    def get_cw_atten(self):
        """
        Get current attenuation of CW signal path

        @return Float: Attenuation (dB)
        """
        cwatten = self.component['cw_atten']
        addr = self.mts.__get_address__(mod=self.module, reg=cwatten['register'])
        if DEBUG_CMD:
            print "0x%04x" % (addr)
        data = self.mts.read(addr)
        if DEBUG_COMM:
            print 'data = 0x%08x' % (data)
        return float(data >> 16) / 2.

    def set_noise_atten(self, atten, verbose=False):
        """
        Set attenuator in noise signal path

        @param atten   Float: Amount of attenuation (dB) to apply
        @param verbose Boolean: Verbose output messages
        """
        if VERBOSE or verbose:
            print 'Setting noise attenuation to ', atten, 'dB'
        step = int(atten*2)
        nsatten = self.component['ns_atten']
        # use reg_chanelsel register to identify device
        addr = self.mts.__get_address__(mod=self.module, reg=0)
        cmd = nsatten["channel"]
        if DEBUG_CMD:
            debug_cmd(addr, cmd)
        self.mts.write(addr, nsatten["channel"])
        verify_cmd(self.mts.read(addr), cmd)  # verify data read back from register
        # use device write register (reg_zx76_wr) to send data
        addr = self.mts.__get_address__(mod=self.module, reg=nsatten['register'])
        if DEBUG_CMD:
            debug_cmd(addr, nsatten["set_mask"] + step)
        self.mts.write(addr, (nsatten["set_mask"] + step))
        verify_cmd(self.mts.read(addr), (nsatten["set_mask"] + step))  # verify data read back from register
        if DEBUG_CMD:
            debug_cmd(addr, step)
        self.mts.write(addr, (step))
        verify_cmd(self.mts.read(addr), step)  # verify data read back from register
        if DEBUG_CMD or DEBUG_COMM:
            print

    def get_noise_atten(self):
        """
        Get current attenuation of noise signal path

        @return Float: Attenuation (dB)
        """
        nsatten = self.component['ns_atten']
        addr = self.mts.__get_address__(mod=self.module, reg=nsatten['register'])
        if DEBUG_CMD:
            print "0x%04x" % (addr)
        data = self.mts.read(addr)
        if DEBUG_COMM:
            print 'data = 0x%08x' % (data)
        return float(data)/2.

    def set_comb_atten(self, atten, verbose=False):
        """
        Set attenuator of combiner module

        @param atten   Float: Amount of attenuation (dB) to apply
        @param verbose Boolean: Verbose output messages
        """
        self.set_noise_atten(atten, verbose)

    def get_comb_atten(self):
        """
        Get current attenuation of combiner module

        @return Float: Attenuation (dB)
        """
        return self.get_noise_atten()

    def select_valon(self, verbose=False):
        """
        To set a CW signal the relevant module valon must be selected via the MTS controller
        """
        if VERBOSE or verbose:
            print 'select valon for module ', self.module
        # use reg_chanelsel register of module 0 to identify valon index
        addr = self.mts.__get_address__(mod=0, reg=0)
        if DEBUG_CMD:
            print "0x%04x" % addr, "0x%08x" % self.module
        self.mts.write(addr, self.module)
        verify_cmd(self.mts.read(addr), self.module)  # verify data read back from register
        if DEBUG_CMD or DEBUG_COMM:
            print

    def valon_lock(self, verbose=False):
        if VERBOSE or verbose:
            print 'Read valon lock detect'
        valon_lock = self.component['lock']
        # use reg_chanelsel register to identify device
        addr = self.mts.__get_address__(mod=self.module, reg=0)
        cmd = valon_lock["channel"]
        if DEBUG_CMD:
            debug_cmd(addr, cmd)
        self.mts.write(addr, valon_lock['channel'])
        verify_cmd(self.mts.read(addr), cmd)  # verify data read back from register
        # use device write register (reg_max7301_wr) to send data
        addr = self.mts.__get_address__(mod=self.module, reg=valon_lock['register'])
        for cmd in valon_lock["cmd"]:
            set_cmd = valon_lock["set_mask"] | cmd
            if DEBUG_CMD:
                debug_cmd(addr, set_cmd)
            self.mts.write(addr, set_cmd)
            verify_cmd(self.mts.read(addr), set_cmd)  # verify data read back from register
            if DEBUG_CMD:
                debug_cmd(addr, cmd)
            self.mts.write(addr, cmd)
            verify_cmd(self.mts.read(addr), cmd)  # verify data read back from register
        if DEBUG_CMD:
            addr = self.mts.__get_address__(mod=self.module, reg=6)
            print hex(addr)
        if DEBUG_COMM:
            addr = self.mts.__get_address__(mod=self.module, reg=6)
            data = self.mts.read(addr)
            print 'data = 0x%08x' % (data)
        if DEBUG_CMD or DEBUG_COMM:
            print

    def get_environment(self):
        """
        Read current temperature and power from power detector in combiner module

        @return Float: Power (mV/dBm)
        @return Float: Temperature (mV/deg)
        """
        conv_factor = 610.351e-6  # V
        adc = self.device['ad7888']
        # use reg_chanelsel register to identify device
        addr = self.mts.__get_address__(mod=self.module, reg=0)
        if DEBUG_CMD:
            print hex(addr), "0x%08x" % adc["channel"]
        self.mts.write(addr, adc["channel"])
        # use device write register (reg_ad7888_wr) to send data
        if DEBUG_COMM:
            data = self.mts.read(addr)
            print 'data = 0x%08x' % (data)
        addr = self.mts.__get_address__(mod=self.module, reg=adc['register'])
        # toggle run bit
        cmd = adc['init'][0]
        set_cmd = adc["set_mask"] | cmd
        if DEBUG_CMD:
            print hex(addr), "0x%08x" % set_cmd
        self.mts.write(addr, set_cmd)
        if DEBUG_COMM:
            data = self.mts.read(addr)
            print 'data = 0x%08x' % (data)
        if DEBUG_CMD:
            print hex(addr), "0x%08x" % cmd
        self.mts.write(addr, cmd)
        if DEBUG_COMM:
            data = self.mts.read(addr)
            print 'data = 0x%08x' % (data)
        # read init val
        addr = self.mts.__get_address__(mod=self.module, reg=adc['register'], read=True)
        if DEBUG_CMD:
            print "0x%04x" % (addr)
        data = self.mts.read(addr)
        if DEBUG_COMM:
            print 'data = 0x%08x' % (data)
        # write to get temp
        addr = self.mts.__get_address__(mod=self.module, reg=adc['register'])
        cmd = adc['init'][1]
        set_cmd = adc["set_mask"] | cmd
        if DEBUG_CMD:
            print hex(addr), "0x%08x" % set_cmd
        self.mts.write(addr, set_cmd)
        if DEBUG_COMM:
            data = self.mts.read(addr)
            print 'data = 0x%08x' % (data)
        if DEBUG_CMD:
            print hex(addr), "0x%08x" % cmd
        self.mts.write(addr, cmd)
        if DEBUG_COMM:
            data = self.mts.read(addr)
            print 'data = 0x%08x' % (data)
        # read temp
        addr = self.mts.__get_address__(mod=self.module, reg=adc['register'], read=True)
        if DEBUG_CMD:
            print "0x%04x" % (addr)
        data = self.mts.read(addr)
        if DEBUG_COMM:
            print 'data = 0x%08x' % (data)
        temp_mv_per_deg = float(data)*conv_factor
        # write to get power
        addr = self.mts.__get_address__(mod=self.module, reg=adc['register'])
        cmd = adc['init'][1]
        set_cmd = adc["set_mask"] | cmd
        if DEBUG_CMD:
            print hex(addr), "0x%08x" % set_cmd
        self.mts.write(addr, set_cmd)
        if DEBUG_COMM:
            data = self.mts.read(addr)
            print 'data = 0x%08x' % (data)
        if DEBUG_CMD:
            print hex(addr), "0x%08x" % cmd
        self.mts.write(addr, cmd)
        if DEBUG_COMM:
            data = self.mts.read(addr)
            print 'data = 0x%08x' % (data)
        # read power
        addr = self.mts.__get_address__(mod=self.module, reg=adc['register'], read=True)
        if DEBUG_CMD:
            print "0x%04x" % (addr)
        data = self.mts.read(addr)
        if DEBUG_COMM:
            print 'data = 0x%08x' % (data)
        pwr_mv_per_dbm = float(data)*conv_factor
        if DEBUG_CMD or DEBUG_COMM:
            print
        return [pwr_mv_per_dbm, temp_mv_per_deg]


class MTS(MTSAPI):
    """
    Initializing a MTS object will create an interface to the various modules and available devices.
    All available modules will be initiated, all sources enables and all signal path outputs disabled, ready for usage.
    All implementation constants will be assigned.

    @param port  String: Series port associated with MTS controller
    @param baudrate Integer: Baudrate of MTS controller series connection
    @param valon String: Series port associated with Valon controller
    @param synth Integer: Synthesizer to connect to from ValonSynth interface
    @param timeout Integer: Time for waiting on response from Series ports
    @param config_file String: Name of file containing MTS setup and usage parameters

    """
    PORT = '/dev/ttyUSB0'
    BAUDRATE = 115200
    VALON = '/dev/ttyUSB1'
    # this is a hardwired setup inside the MTS, so it will not be available for users to select SYNTH_A through this interface
    SYNTH = valon_synth.SYNTH_B
    CONFIG = '/etc/mts/mts_default'

    src_dict = {
      'ucs1': {'module': 1, 'available': True},
      'ucs2': {'module': 2, 'available': True},
      'cs1': {'module': 3, 'available': True}
    }
    cmb_dict = {
      'comb1': {'module': 4, 'available': True},
      'comb2': {'module': 5, 'available': True}
    }

    # Initialize MTS comms ports for control and valon settings
    def __init__(self, port=PORT, baudrate=BAUDRATE, valon=VALON, synth=SYNTH, timeout=1, config_file=CONFIG):
        # Set up serial comms to mts controller
        self.ctrl = MTSAPI(port, baudrate)
        try:
            self.ctrl.ping()
        except Exception as e:
            # Closing before exit
            self.ctrl.__close__()
            raise RuntimeError('Cannot ping controller: Error received\n%s' % (e))
            sys.exit(1)

        # Get setup parameters
        self.config = mts_config.conf(config_file)
        self.MIN_BASE = self.config.get_float('kat7', 'min_base_freq_mhz')
        self.MAX_BASE = self.config.get_float('kat7', 'max_base_freq_mhz')
        # read calibration data for output signals
        [self.UCS_NOISE, self.CS_NOISE] = read_calib_data('/etc/mts/noise_calib_table.data')
        [self.UCS_CW, self.CS_CW] = read_calib_data('/etc/mts/cw_calib_table.data')

        # a for loop is used to prevent duplication of code:
        #   # uncorrelated source 1
        #   self.ucs1 = mts_mod(self.ctrl, self.module['ucs1'])
        #   # switch on all components in signal path, but leave the switch open
        #   self.ucs1.noise_source(enable=True)
        #   self.ucs1.noise_output(enable=True)
        #   # uncorrelated source 2
        #   self.ucs2 = mts_mod(self.ctrl, self.module['ucs2'])
        #   self.ucs2.noise_source(enable=True)
        #   self.ucs2.noise_output(enable=True)
        for key in self.src_dict.keys():
            print 'Initiating %s, module %d' % (key, self.src_dict[key]['module'])
            obj = mts_mod(self.ctrl, self.src_dict[key]['module'], valon=valon, synth=synth)
            # assign the object to self from the key name:
            #  e.g. create object self.ucs1 from the key='ucs1'
            self.__dict__[key] = obj
            # if 'available' is true, the assigned object attribute will be switched on or off
            if self.src_dict[key]['available']:
                # switch off signal paths
                obj.noise_output(enable=False)
                obj.cw_output(enable=False)
                # switch on signal sources
                obj.noise_source(enable=True)
                obj.cw_source(enable=True)
                # set attenuator to max attenuation
                max_atten = self.config.get_float(key, 'max_atten')
                obj.set_noise_atten(atten=max_atten)  # dB
                obj.set_cw_atten(atten=max_atten)  # dB
                # set config values
                obj.MIN_ATTEN = self.config.get_float(key, 'min_atten')
                obj.MAX_ATTEN = self.config.get_float(key, 'max_atten')
                obj.MIN_NOISE = self.config.get_float(key, 'min_noise_freq_mhz')
                obj.MAX_NOISE = self.config.get_float(key, 'max_noise_freq_mhz')
                obj.MIN_CW = self.config.get_float(key, 'min_cw_freq_mhz')
                obj.MAX_CW = self.config.get_float(key, 'max_cw_freq_mhz')

        for key in self.cmb_dict.keys():
            print 'Initiating %s, module %d' % (key, self.cmb_dict[key]['module'])
            obj = mts_mod(self.ctrl, self.cmb_dict[key]['module'])
            # assign the object to self from the key name:
            self.__dict__[key] = obj
            # if 'available' is true, the assigned object attribute will be switched on or off
            if self.cmb_dict[key]['available']:
                obj.power_temp_sensor(enable=True)
                min_atten = self.config.get_float(key, 'min_atten')
                obj.set_comb_atten(atten=min_atten)  # dB
                # set config values
                obj.MIN_ATTEN = self.config.get_float(key, 'min_atten')
                obj.MAX_ATTEN = self.config.get_float(key, 'max_atten')
                obj.MIN_NOISE = self.config.get_float(key, 'min_noise_freq_mhz')
                obj.MAX_NOISE = self.config.get_float(key, 'max_noise_freq_mhz')
                obj.MIN_CW = self.config.get_float(key, 'min_cw_freq_mhz')
                obj.MAX_CW = self.config.get_float(key, 'max_cw_freq_mhz')
                # assign associated source modules
                uncorr_src = self.config.get_str(key, 'ucs')
                if uncorr_src in self.src_dict:
                    obj.ucs = self.__dict__[uncorr_src]
                corr_src = self.config.get_str(key, 'cs')
                if corr_src in self.src_dict:
                    obj.cs = self.__dict__[corr_src]

    def exit(self):
        """
        Exiting the MTS interface will return all device states in the MTS to most optimal.
        This includes disabling all module sources and setting the output signal switches to lowest power
        """
        # switch off all components in signal path, but leave the switch closed for min power consumption
        for key in self.src_dict.keys():
            if self.src_dict[key]['available']:
                obj = self.__dict__[key]
                # switch off signal sources
                obj.noise_source(enable=False)
                obj.cw_source(enable=False)
                # switch on signal paths
                obj.noise_output(enable=True)
                obj.cw_output(enable=True)
        # Closing before exit
        self.ctrl.__close__()

    def select_combiner(self, comb, verbose=False):
        """
        Selecting a combiner for output enable all 4 signal devices associated with that combiner by default, but will not enable output.

        @param comb    String: Name of the combiner to connect to, currently comb1 and comb2 is available
        @param verbose Boolean: [Optional] More user output as sources are enabled

        @return        Object: Combiner object from MTS
        """
        if comb in self.__dict__:
            # identify object
            return self.__dict__[comb]
        else:
            raise RuntimeError('Output module %s not available' % comb)

    def __set_pwr__(self, comb, src, pwr, cal_tbl=None, signal='noise', verbose=False):
        """
        Internal function that can address the module functions of the selected combiner and associated source to calculate and set attenuators to achieve the requested power level.

        @param comb    Object: Combiner module object
        @param src     Object: Source module object
        @param pwr     Float: Requested power level of noise signal in dBm
        @param cal_tbl Array: [Optional] Specify the calibration table associated with the source to calculate power to attenuation convertion
        @param signal  String: [Optional] Specify "noise" or "cw" type signal power to set
        @param verbose Boolean: [Optional] Be verbose in power computation and setting

        @return None
        """
        if not cal_tbl:
            cal_tbl = self.UCS_NOISE
        cal_tbl = numpy.array(cal_tbl)
        if pwr < min(cal_tbl[:, 2]):
            raise RuntimeError('Power level %f dBm to low. Min power available %f dBm\n' % (pwr, min(cal_tbl[:, 2])))
        if pwr > max(cal_tbl[:, 2]):
            raise RuntimeError('Power level %f dBm to high. Max power available %f dBm\n' % (pwr, max(cal_tbl[:, 2])))
        pwr_idx = numpy.argmin(abs(pwr - cal_tbl[:, 2]))
        atten = cal_tbl[pwr_idx, 0]
        if verbose:
            print "\tClosest power level of %f dBm, set attenuation %f dB" % (cal_tbl[pwr_idx, 2], cal_tbl[pwr_idx, 0])

        # Choosing source and combiner attentuation over range
        if (atten-atten % src.MAX_ATTEN) > 0:
            src_atten = (atten-atten % src.MAX_ATTEN)
            cmb_atten = atten-src_atten
        else:
            src_atten = atten
            cmb_atten = 0.0
        if verbose:
            print 'Set src atten to %f dB and output atten to %f dB' % (src_atten, cmb_atten)

        if signal == 'noise':
            src.set_noise_atten(atten=src_atten, verbose=verbose)  # dB
            if src.get_noise_atten() != src_atten:
                raise RuntimeError('Cannot set source attenuation\n')
        else:
            src.set_cw_atten(atten=src_atten, verbose=verbose)  # dB
            if src.get_cw_atten() != src_atten:
                raise RuntimeError('Cannot set source attenuation\n')
        comb.set_comb_atten(atten=cmb_atten, verbose=verbose)  # dB
        if comb.get_comb_atten() != cmb_atten:
            raise RuntimeError('Cannot set combiner attenuation\n')

    def __get_pwr__(self, comb, cal_tbl=None, sensor=None):
        """
        Internal function to read the combiner sensor output and convert the value to power in dBm.

        @param comb    Object: Combiner module object
        @param cal_tbl Array: [Optional] Specify the calibration table associated with the source to calculate power to attenuation convertion
        @param sensor  Float: [Optional] Combiner power sensor output reading

        @return Float: Signal power in dBm
        """
        if not cal_tbl:
            cal_tbl = self.UCS_NOISE
        cal_tbl = numpy.array(cal_tbl)
        if not sensor:
            sensor = comb.get_environment()[0]
        amp_idx = numpy.argmin(abs(sensor - cal_tbl[:, 1]))
        return cal_tbl[amp_idx, 2]

    def set_noise(self, output, uncorr_pwr=None, corr_pwr=None):
        """
        Enable either or both the uncorrelated and correlated noise signals of a selected combiner output.

        @param output     String: Name of combiner from which output is expected
        @param uncorr_pwr Float: [Optional] Signal output power for uncorrelated noise source in dBm
        @param corr_pwr   Float: [Optional] Signal output power for correlated noise source in dBm

        @return None
        """
        # convert power to attenuation and enable signal output
        def enable_noise(comb, src, pwr, cal_tbl):
            self.__set_pwr__(comb, src, pwr, cal_tbl=cal_tbl, signal='noise')
            src.noise_source(enable=True)
            src.noise_output(enable=True)
        combiner = self.select_combiner(comb=output)
        if uncorr_pwr:
            enable_noise(comb=combiner, src=combiner.ucs, pwr=uncorr_pwr, cal_tbl=self.UCS_NOISE)
        if corr_pwr:
            enable_noise(comb=combiner, src=combiner.cs, pwr=corr_pwr, cal_tbl=self.CS_NOISE)

    def get_noise(self, output, cal_tbl=None):
        """
        Read the noise power measured at a selected output combiner module.

        @param output  String: Name of combiner from which output is expected
        @param cal_tbl Array: [Optional] Specify the calibration table associated with the source to calculate power to attenuation convertion

        @return Float: Output power read from combiner sensor
        """
        if not cal_tbl:
            cal_tbl = self.UCS_NOISE
        return self.__get_pwr__(comb=self.select_combiner(comb=output), cal_tbl=cal_tbl)

    def disable_noise(self, output, uncorr_src=False, corr_src=False):
        """
        Disable either or both the uncorrelated and correlated noise signals of a selected combiner output.

        @param output     String: Name of combiner from which output is expected
        @param uncorr_src Float: [Optional] Disable noise output from uncorrelated noise source
        @param corr_src   Float: [Optional] Disable noise output from correlated noise source

        @return None
        """
        combiner = self.select_combiner(comb=output)
        if uncorr_src:
            combiner.ucs.noise_output(enable=False)
        if corr_src:
            combiner.cs.noise_output(enable=False)

    def set_cw(self, output, uncorr_pwr=None, uncorr_freq=None, corr_pwr=None, corr_freq=None):
        """
        Enable either or both the uncorrelated and correlated CW signals of a selected combiner output.

        @param output      String: Name of combiner from which output is expected
        @param uncorr_pwr  Float: [Optional] Signal output power for uncorrelated CW source in dBm
        @param uncorr_freq Float: [Optional] Uncorrelated CW signal frequency in MHz
        @param corr_pwr    Float: [Optional] Signal output power for correlated CW source in dBm
        @param corr_freq   Float: [Optional] Correlated CW signal frequency in MHz

        @return None
        """
        # convert power to attenuation, set CW frequency and enable signal output
        def enable_cw(comb, src, pwr, cal_tbl):
            self.__set_pwr__(comb, src, pwr, cal_tbl=cal_tbl, signal='cw')
            src.cw_source(enable=True)
            src.cw_output(enable=True)
        combiner = self.select_combiner(comb=output)
        if uncorr_pwr:
            enable_cw(comb=combiner, src=combiner.ucs, pwr=uncorr_pwr, cal_tbl=self.UCS_CW)
            if uncorr_freq:
                combiner.ucs.set_freq(freq_mhz=uncorr_freq)
                if abs(combiner.ucs.get_freq() - uncorr_freq) > 0:
                    raise RuntimeError('Could not set requested frequency %f MHz' % uncorr_freq)
        if corr_pwr:
            enable_cw(comb=combiner, src=combiner.cs, pwr=corr_pwr, cal_tbl=self.CS_CW)
            if corr_freq:
                combiner.cs.set_freq(freq_mhz=corr_freq)
                if abs(combiner.cs.get_freq() - corr_freq) > 0:
                    raise RuntimeError('Could not set requested frequency %f MHz' % corr_freq)

    def get_cw(self, output, cal_tbl=None):
        """
        Read the CW power measured at a selected output combiner module.

        @param output  String: Name of combiner from which output is expected
        @param cal_tbl Array: [Optional] Specify the calibration table associated with the source to calculate power to attenuation convertion

        @return Float: Output power read from combiner sensor
        """
        if not cal_tbl:
            cal_tbl = self.UCS_CW
        return self.__get_pwr__(comb=self.select_combiner(comb=output), cal_tbl=cal_tbl)

    def disable_cw(self, output, uncorr_src=False, corr_src=False):
        """
        Disable either or both the uncorrelated and correlated CW signals of a selected combiner output.

        @param output     String: Name of combiner from which output is expected
        @param uncorr_src Float: [Optional] Disable CW output from uncorrelated CW source
        @param corr_src   Float: [Optional] Disable CW output from correlated CW source

        @return None
        """
        combiner = self.select_combiner(comb=output)
        if uncorr_src:
            combiner.ucs.cw_output(enable=False)
        if corr_src:
            combiner.cs.cw_output(enable=False)

    def get_freq(self, output, uncorr_src=False, corr_src=False):
        """
        Read the CW frequency of the selected source at the requested combiner output.

        @param output     String: Name of combiner from which output is expected
        @param uncorr_src Float: [Optional] Read CW frequency setting of uncorrelated CW source
        @param corr_src   Float: [Optional] Read CW frequency setting of correlated CW source

        @return Float: CW frequency in MHz
        """
        combiner = self.select_combiner(comb=output)
        if uncorr_src:
            return combiner.ucs.get_freq()
        if corr_src:
            return combiner.cs.get_freq()

    def set_freq(self, output, uncorr_freq=None, corr_freq=None):
        """
        Set the CW frequency of the selected source at the requested combiner output.

        @param output     String: Name of combiner from which output is expected
        @param uncorr_freq Float: [Optional] Uncorrelated CW signal frequency in MHz
        @param corr_freq   Float: [Optional] Correlated CW signal frequency in MHz

        @return None
        """
        combiner = self.select_combiner(comb=output)
        if uncorr_freq:
            combiner.ucs.set_freq(freq_mhz=uncorr_freq)
        if corr_freq:
            combiner.cs.set_freq(freq_mhz=corr_freq)


# class MTSoutput(MTS):
#   """
#   Selecting a combiner for output enable all 4 signal devices associated with that combiner by default, but will not enable output.
#   Access to combiner output and input functions
#
#   @param output      String: Name of the combiner to connect to, currently comb1 and comb2 is available
#   @param port        String: Series port associated with MTS controller
#   @param baudrate    Integer: Baudrate of MTS controller series connection
#   @param valon       String: Series port associated with Valon controller
#   @param synth       Integer: Synthesizer to connect to from ValonSynth interface
#   @param timeout     Integer: Time for waiting on response from Series ports
#   @param config_file String: Name of file containing MTS setup and usage parameters
#
#   @return        Object: Output object for MTS
#   """
#
#   def __init__(self, output, port, baudrate=None, valon=None, synth=None, timeout=None, config_file=None):
#     kwargs = {}
#     if baudrate:
#       kwargs['baudrate'] = baudrate
#     if valon:
#       kwargs['valon'] = valon
#     if synth:
#       kwargs['synth'] = synth
#     if timeout:
#       kwargs['timeout'] = timeout
#     if config_file:
#       kwargs['config_file'] = config_file
#     self.mts = MTS(port, **kwargs)
#     if self.mts.__dict__.has_key(output):
#       # identify object
#       self.output = self.mts.__dict__[output]
#       # enable output sources
#       self.output.ucs.noise_source(enable=True)
#       self.output.ucs.cw_source(enable=True)
#       self.output.cs.noise_source(enable=True)
#       self.output.cs.cw_source(enable=True)
#     else: raise RuntimeError('Output module %s not available' % comb)

if __name__ == '__main__':

    parser = OptionParser(version="%prog 0.1")
    parser.add_option('-p', '--port',
                      action='store',
                      dest='tty',
                      default='/dev/ttyUSB0',
                      help='Set serial port, default is \'%default\'.')
    parser.add_option('-v', '--valon',
                      action='store',
                      dest='cwtty',
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
    mts = MTS(port=opts.tty, baudrate=int(opts.baudrate), valon=opts.cwtty, config_file=opts.config_file)
    print 'Initiation takes %.4f seconds' % (time.time()-start)

# Verify output measured from combiner is similar for both correlated and uncorrelated sources
    output = mts.select_combiner(opts.combiner)
    print '\nConnect output from %s to spectrum analyser' % opts.combiner
    print 'Available frequency range from %f MHz to %f MHz' % (mts.MIN_BASE, mts.MAX_BASE)
    output.power_temp_sensor(enable=True)
    [pwr_mv_per_dbm, temp_mv_per_deg] = output.get_environment()
    print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
    print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg
    output.set_comb_atten(atten=mts.comb2.MIN_ATTEN)  # dB
    atten = output.get_comb_atten()  # dB
    print '\tcomb attenuated %.2f dB' % atten

# Noise output from uncorrelated source
    raw_input('Enter for uncorrelated noise output')
    output.ucs.noise_output(enable=True, verbose=True)
    output.ucs.set_noise_atten(atten=output.ucs.MIN_ATTEN, verbose=True)  # dB
    atten = output.ucs.get_noise_atten()  # dB
    print '\tnoise attenuated %.2f dB' % atten
    [pwr_mv_per_dbm, temp_mv_per_deg] = output.get_environment()
    print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
    print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg
    raw_input('Enter to continue')

    output.ucs.set_noise_atten(atten=output.ucs.MAX_ATTEN, verbose=True)  # dB
    atten = output.ucs.get_noise_atten()  # dB
    print '\tnoise attenuated %.2f dB' % atten
    [pwr_mv_per_dbm, temp_mv_per_deg] = output.get_environment()
    print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
    print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg
    raw_input('Enter to continue')
    output.ucs.noise_output(enable=False, verbose=True)

# Noise output from correlated source
    raw_input('Enter for correlated noise output')
    output.cs.noise_output(enable=True, verbose=True)
    output.cs.set_noise_atten(atten=output.cs.MIN_ATTEN, verbose=True)  # dB
    atten = output.cs.get_noise_atten()  # dB
    print '\tnoise attenuated %.2f dB' % atten
    [pwr_mv_per_dbm, temp_mv_per_deg] = output.get_environment()
    print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
    print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg
    raw_input('Enter to continue')

    output.cs.set_noise_atten(atten=output.cs.MAX_ATTEN, verbose=True)  # dB
    atten = output.cs.get_noise_atten()  # dB
    print '\tnoise attenuated %.2f dB' % atten
    [pwr_mv_per_dbm, temp_mv_per_deg] = output.get_environment()
    print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
    print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg
    raw_input('Enter to continue')
    output.cs.noise_output(enable=False, verbose=True)

# CW output from uncorrelated source
    raw_input('Enter for uncorrelated cw output')
    output.ucs.set_cw_atten(atten=output.ucs.MIN_ATTEN, verbose=True)
    cw_freq_mhz = output.ucs.get_freq(verbose=True)
    print '\tcw frequency set to %s MHz' % cw_freq_mhz
    atten = output.ucs.get_cw_atten()  # dB
    print '\tcw attenuated %.2f dB' % atten
    output.ucs.cw_output(enable=True, verbose=True)
    [pwr_mv_per_dbm, temp_mv_per_deg] = output.get_environment()
    print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
    print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg
    raw_input('Enter to continue')

    output.ucs.set_freq(freq_mhz=220., verbose=True)
    cw_freq_mhz = output.ucs.get_freq(verbose=True)
    print '\tcw frequency set to %s MHz' % cw_freq_mhz
    output.ucs.set_cw_atten(atten=output.ucs.MAX_ATTEN, verbose=True)
    atten = output.ucs.get_cw_atten()  # dB
    print '\tcw attenuated %.2f dB' % atten
    [pwr_mv_per_dbm, temp_mv_per_deg] = output.get_environment()
    print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
    print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg
    raw_input('Enter to continue')
    output.ucs.cw_output(enable=False, verbose=True)

# CW output from correlated source
    raw_input('Enter for correlated cw output')
    output.cs.set_cw_atten(atten=output.cs.MIN_ATTEN, verbose=True)
    atten = output.cs.get_cw_atten()  # dB
    print '\tcw attenuated %.2f dB' % atten
    try:
        # cw_freq_mhz = output.cs.get_freq(verbose=True, timeout=5)
        cw_freq_mhz = output.cs.get_freq(verbose=True)
        print '\tcw frequency set to %s MHz' % cw_freq_mhz
        output.cs.cw_output(enable=True, verbose=True)
        [pwr_mv_per_dbm, temp_mv_per_deg] = output.get_environment()
        print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
        print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg
        raw_input('Enter to continue')

        output.cs.set_freq(freq_mhz=220.)
        cw_freq_mhz = output.cs.get_freq()
        print '\tcw frequency set to %s MHz' % cw_freq_mhz
        output.cs.set_cw_atten(atten=output.cs.MAX_ATTEN, verbose=True)
        atten = output.cs.get_cw_atten()  # dB
        print '\tcw attenuated %.2f dB' % atten
        [pwr_mv_per_dbm, temp_mv_per_deg] = output.get_environment()
        print '\tcomb power %.2f [mV/dBm]' % pwr_mv_per_dbm
        print '\tcomb temp %.2f [mV/degC]' % temp_mv_per_deg
        raw_input('Enter to end')

    except Exception as e:
        print e
        pass  # continue, there is nothing you can do
    output.cs.cw_output(enable=False, verbose=True)

    print 'Exit test controller...'
    start = time.time()
    mts.exit()
    print 'Exiting takes %.4f seconds' % (time.time() - start)

# -fin-
