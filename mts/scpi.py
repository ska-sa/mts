#!/usr/bin/python

import serial
import socket
import time

# default FSU setup parameters
Ref = 5.  # dBm
Att = 0.  # dB
RBW = 300.  # kHz
VBW = 300.  # kHz
SWT = 0.015  # sec


# SCPI functional interface to allow user script in scripts/ directory to capture measurements using the R&S FSU or equivalent spectrum analyser

class SCPI:
    """
    Rohde & Schwarz allows software communication to any high end device via the SCPI socket interface using GPIB commands.

    @param host     String: IP address of host to connect to via a socket connection
    @param device   String: Alternative to the socket interface a series interface connection
    @param port     Integer: [Optional] Port for socket connection (default=5025)
    @param baudrate Integer: [Optional] For series connection (default=9600)
    @param timeout  Integer: [Optional] Timeout for waiting to establish connection

    @return   Handle: Handle to r&s device
    """

    PORT = 5025
    BAUDRATE = 9600

    # Connect to the R&S signal generator
    def __init__(self,
                 host=None,
                 port=PORT,  # set up socket connection
                 device=None,
                 baudrate=BAUDRATE,  # set up serial port
                 timeout=1):
        if host and device:
            raise RuntimeError('Only one connection can be initaited at a time.\nSelect socket or serial connection.\n')

        # Ethernet socket connection
        self.connection = None
        if host:
            self.connection = 'socket'
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((host, port))
            self.s.settimeout(1)
        elif device:
            self.connection = 'serial'
            self.s = serial.Serial(device, baudrate, timeout, rtscts=0)
        else:
            raise RuntimeError('No connections specified.\n')

    # Querie instrument identificaton
    def deviceID(self):
        """
        Query and report R&S device ID
        """
        self.write("*IDN?")
        print "DEVICE: " + self.read()

    # send query / command via relevant port comm
    def write(self, command):
        """
        Write command to port, depending on interface selected (socket/series)

        @param String: Command to send to port
        """
        if self.connection == 'serial':
            self.s.write(command + '\r\n')
        else:
            self.s.send(command + '\n')

    def read(self, bufsize=128):
        """
        Returns bytes read from port

        @param bufsize Integer: [Optional] Buffer size for socket connections

        @return Bytes read from port
        """
        if self.connection == 'serial':
            return self.s.readline()
        else:
            return self.s.recv(bufsize)

    # reset
    def reset(self):
        """
        Resets the R&S device to factory settings (preset function)
        """
        self.write("*RST")
        self.write("*CLS")

    # default setup using global variable as top of script
    def fsuSetup(self, freq_start, freq_stop):
        """
        R&S FSU spectrum analyzer setup using predefined values

        @param freq_start FLOAT: Start frequency [MHz]
        @param freq_stop  FLOAT: Stop frequency [MHz]
        """
        self.write("SYST:DISP:UPD ON")
        # set the ampl ref level 5dBm
        self.write("DISP:WIND:TRAC:Y:RLEV %.3f dBm" % (Ref,))
        # set the rf attenuation to 0dB
        self.write("INP:ATT %.3f dB" % (Att,))
        # set the resolution bandwidth to 300KHz
        self.write("BAND:AUTO OFF")
        self.write("BAND %.3fKHz" % (RBW,))
        # set the video bandwidth to 300KHz
        self.write("BAND:VID:AUTO OFF")
        self.write("BAND:VID %.3fKHz" % (VBW,))
        # set frequency range, start at 0MHz and stop at 400MHz
        self.write("FREQ:STAR %.2fMHz" % (freq_start,))
        self.write("FREQ:STOP %.2fMHz" % (freq_stop,))
        # set sweep time to 15ms
        self.write("SWE:TIME:AUTO OFF")
        self.write("SWE:TIME %.3f s" % (SWT,))

    # measure integrated channel power
    def setNoisePwr(self, channel_bw):
        """
        Measure channel power

        @param channel_bw FLOAT: Bandwidth of occupied channel [MHz]
        """
        # select absolute power measurement
        self.write("SENS:POW:ACH:MODE ABS")
        # set channel bandwidth of the main transmission channel
        self.write("SENS:POW:ACH:ACP 0")
        self.write("SENS:POW:ACH:BWID %.3fMHz" % (channel_bw,))
        # switch on power measurements
        self.write("CALC:MARK:FUNC:POW ON")

    # measure integrated channel power
    def getNoisePwr(self):
        """
        Measure channel power

        @return FLOAT: Measured channel power [dBm]
        """
        self.write("INIT:CONT OFF")  # single sweep
        # switch on power measurements
        self.write("CALC:MARK:FUNC:POW ON")
        # calculation of channel power
        self.write("CALC:MARK:FUNC:POW:SEL CPOW")
        self.write("INIT;*WAI")  # start and wait to complete the sweep
        self.write("CALC:MARK:FUNC:POW:RES? CPOW")
        return float(self.read(bufsize=32768))

    # measure integrated channel power
    def noisePwr(self, channel_bw):
        """
        Measure channel power

        @param channel_bw FLOAT: Bandwidth of occupied channel [MHz]

        @return FLOAT: Measured channel power [dBm]
        """
        self.write("INIT:CONT OFF")  # single sweep
        # select absolute power measurement
        self.write("SENS:POW:ACH:MODE ABS")
        # set channel bandwidth of the main transmission channel
        self.write("SENS:POW:ACH:ACP 0")
        self.write("SENS:POW:ACH:BWID %.3fMHz" % (channel_bw,))
        # switch on power measurements
        self.write("CALC:MARK:FUNC:POW ON")
        # calculation of channel power
        self.write("CALC:MARK:FUNC:POW:SEL CPOW")
        self.write("INIT;*WAI")  # start and wait to complete the sweep
        self.write("CALC:MARK:FUNC:POW:RES? CPOW")
        return float(self.read(bufsize=65536))

    # measure CW peak value and frequency
    def cwPeak(self):
        """
        Measure the peak amplitude of CW tone

        @return FLOAT: CW frequency [Hz]
        @return FLOAT: CW amplitude [dBm]
        """
        # determine the max peak
        self.write("INIT:CONT ON")  # cont sweep
        time.sleep(1)
        self.write("INIT:CONT OFF")  # single sweep
        self.write("CALC:MARK ON")  # switch on marker 1
        self.write("CALC:MARK:COUN ON")  # switch on frequency counter for marker 1
        self.write("CALC:MARK:MAX:AUTO ON")  # switch on automatic peak search for marker 1
        self.write("INIT:IMM;*WAI")  # start and wait to complete the sweep
        self.write("CALC:MARK:COUN:FREQ?")  # outputs the measured value
        freq_hz = float(self.read(bufsize=32768))
        self.write("CALC:MARK:Y?")  # outputs the measured value for marker 1
        amp_dbm = float(self.read(bufsize=65536))
        return [freq_hz, amp_dbm]

    # close the comms port to the R&S signal generator
    def __close__(self):
        """
        Close port connection
        """
        self.s.close()

if __name__ == '__main__':

    # FSU Spectrum Analyser IP address
    fsu_ip = '192.168.4.186'
    socket_port = 5025
    # Using SCPI class for comms to FSU R&S Spectrum Analyser
    print 'Connecting to device IP:', fsu_ip
    fsu_obj = SCPI(fsu_ip)

    try:
        fsu_obj.deviceID()
        fsu_obj.reset()
        # setup FSU SA
        fsu_obj.fsuSetup(freq_start=0., freq_stop=400.)
        # measure channel power
        channel_power = fsu_obj.noisePwr(chanel_bw=256.)
        print "Channel power: %f dBm" % channel_power
        # measure the CW ampl
        [freq_hz, amp_dbm] = fsu_obj.cwPeak()
        print "CW at %f MHz has amplitude %f dBm" % (freq_hz/1e6, amp_dbm)
    except:
        pass  # need to close port

    print 'Closing all ports...'
    try:
        fsu_obj.__close__()
    except:
        pass  # socket already closed

# -fin-
