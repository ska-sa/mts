#!/usr/bin/python

from optparse import OptionParser
import serial
import sys
# import time


# MTS controller series interface as defined by the README
class DeviceError(Exception):
    def __init__(self, level, msg):
        self.args = (level, msg)
        self.level = level
        self.msg = msg


class MTSAPI():
    """
    Set up serial communication to the MTS controller board.

    @param port     String: USB port allocated to device when connected
    @param baudrate Integer: Baudrate of serial communication
    @param timeout  Integer; [Option] To prevent serial port from waiting for ever to establish connection

    @return      Handle: Handle to synthesize object
    """
    # Control sequences
    CTRL_PING = '\x08'
    CTRL_READ = '\x01'
    CTRL_WRITE = '\x02'
    RTRN_SUCCESS = '\x01'
    RTRN_OVERFLOW = '\xfd'  # A buffer overflow occurred
    RTRN_BUSERROR = '\xfe'  # There was a internal bus error (slave timeout or other)
    RTRN_CMDERROR = '\xff'  # The command was not recognized

    def __init__(self, port='/dev/ttyUSB0', baudrate=115200, timeout=1):

        # Set up serial comms
        self._port = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        # Establish communication
        if not self._port:
            try:
                self._port.open()
            except Exception as e:
                raise DeviceError('Fatal', str(e))
        # Initiate data transfer
        if self._port:
            print 'Port %s is open' % self._port.name
            try:
                self._port.flushInput()  # flush input buffer, discarding all its contents
                self._port.flushOutput()  # flush output buffer, aborting current output and discard all that is in buffer
            except Exception as e:
                raise DeviceError('Fatal', str(e))
        else:
            # Closing before exit
            try:
                self._port.close()
            except Exception as e:
                raise DeviceError('Fatal', str(e))
            raise DeviceError('Fatal', 'Serial port %s not open, cleanup and exit' % self._port.name)

    def __get_address__(self, mod, reg, read=False):
        """
        Generate the correct address to read and/or write a register

        @param mod  Integer: MTS module to address
        @param reg  Integer: Relevant module register
        @param read Boolean: Default is False which means a 'write' register address, while True returns the relevant 'read' register address

        @return Interger: Register address
        """
        addr = ((mod << 12) | reg) | read << 2
        return addr

    def __close__(self):
        """Close serial connection"""
        # Closing before exit
        print 'Closing port %s' % self._port.name
        self._port.close()

    def ping(self):
        """Ping open serial port"""
        # try to ping the controller
        self._port.write(bytearray(self.CTRL_PING))
###     time.sleep(0.01)
        rtrn_byte = self._port.read(1)
        # print repr(self.CTRL_PING), repr(rtrn_byte)
        if ord(rtrn_byte) != ord(self.CTRL_PING):
            raise DeviceError('Fatal', 'Could not ping serial port')
        return True

    def write(self, address, data):
        """
        Writes data to a register address

        @param address Interger: Register address to write data to
        @param data:   String: Data to write to register

        @return Boolean: Indicating if 'write' to register was successful.
        """

        write_array = bytearray()
        # write data to the controller
        write_array.append(self.CTRL_WRITE)
        for byte in range(0, 2):
            write_array.append((address >> (byte*8)) & 0xFF)
        for byte in range(0, 4):
            write_array.append((data >> (byte*8)) & 0xFF)
        # print 'writing:', repr(write_array)
        self._port.write(write_array)
###     time.sleep(0.01) # time.sleep(0.5)
        rtrn_val = bytearray(self._port.read(1))[0]
        if ord(self.RTRN_SUCCESS) != rtrn_val:
            if rtrn_val == ord(self.RTRN_OVERFLOW):
                raise DeviceError('Error', 'Could not write data to serial port:\n Buffer overflow occurred')
            elif rtrn_val == ord(self.RTRN_BUSERROR):
                raise DeviceError('Error', 'Could not write data to serial port:\n Internal bus error')
            elif rtrn_val == ord(self.RTRN_CMDERROR):
                raise DeviceError('Error', 'Could not write data to serial port:\n Command not recognized')
            else:
                raise DeviceError('Error', 'Could not write data to serial port:\n Unknown return value %s' % (hex(rtrn_val)))
        return True

    def read(self, address):
        """
        Reads data to a register address

        @param Integer: Register address to read from

        @return String: Data read form register
        """
        write_array = bytearray()
        # read data via the controller
        write_array.append(self.CTRL_READ)
        for byte in range(0, 2):
            write_array.append((address >> (byte*8)) & 0xFF)
        self._port.write(write_array)
        read_array = bytearray(self._port.read(5))
        # print 'read:', repr(read_array)
        rtrn_val = read_array[0]
        if ord(self.RTRN_SUCCESS) != rtrn_val:
            if rtrn_val == ord(self.RTRN_OVERFLOW):
                raise DeviceError('Error', 'Could not read data from serial port:\n Buffer overflow occurred')
            elif rtrn_val == ord(self.RTRN_BUSERROR):
                raise DeviceError('Error', 'Could not read data from serial port:\n Internal bus error')
            elif rtrn_val == ord(self.RTRN_CMDERROR):
                raise DeviceError('Error', 'Could not read data from serial port:\n Command not recognized')
            else:
                raise DeviceError('Error', 'Could not read data from serial port:\n Unknown return value %s' % (hex(rtrn_val)))
        data = 0
        for byte in range(0, 4):
            data |= read_array[byte + 1] << (byte * 8)
        return data

if __name__ == '__main__':

    parser = OptionParser(version="%prog 0.1")
    parser.add_option('-p', '--port',
                      action='store',
                      dest='tty',
                      default='/dev/ttyUSB0',
                      help='Set serial port, default is \'%default\'.')
    parser.add_option('-b', '--baud',
                      action='store',
                      dest='baudrate',
                      default=115200,
                      help='Set serial port baudrate, default is \'%default\'.')
    (opts, args) = parser.parse_args()

    # Set up serial comms
    mts = MTSAPI(port=opts.tty, baudrate=int(opts.baudrate))
    try:
        mts.ping()
    except DeviceError as de:
        # Closing before exit
        mts.__close__()
        print '%s: %s' % (de.level, de.msg)
        sys.exit(1)

    print
    print 'create the register address'
    addr = mts.__get_address__(mod=1, reg=1)
    print repr(addr), bin(addr), hex(addr)
    addr = mts.__get_address__(mod=2, reg=2, read=True)
    print repr(addr), bin(addr), hex(addr)
    addr = mts.__get_address__(mod=3, reg=5, read=True)
    print repr(addr), bin(addr), hex(addr)

    print
    print 'read data from port'
    addr = mts.__get_address__(mod=1, reg=6, read=True)
    print repr(addr), bin(addr), hex(addr)
    try:
        data = mts.read(addr)
    except DeviceError as de:
        # Closing before exit
        mts.__close__()
        print '%s: %s' % (de.level, de.msg)
        sys.exit(1)
    print 'data =', hex(data)

    print
    print 'write data to port'
    addr = mts.__get_address__(mod=1, reg=2)
    data = int('00001380', base=16)
    print 'Write data =', hex(data), 'to address =', hex(addr)
    try:
        mts.write(addr, data)
    except DeviceError as de:
        # Closing before exit
        mts.__close__()
        print '%s: %s' % (de.level, de.msg)
        sys.exit(1)
    print 'Read data from address =', hex(addr)
    try:
        data = mts.read(addr)
    except DeviceError as de:
        # Closing before exit
        mts.__close__()
        print '%s: %s' % (de.level, de.msg)
        sys.exit(1)
    print 'data =', hex(data)

    print
    # Closing before exit
    mts.__close__()

# -fin-
