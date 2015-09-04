#!/usr/bin/python

import serial
import sys, time

class DeviceError(Exception):
  def __init__(self, level, msg):
    self.args  = (level, msg)
    self.level = level
    self.msg   = msg

def __register_address__(mod, reg, read=False):
  addr = ((mod << 12) | reg) | read << 2
  return addr

def ping(device):
  # try to ping the controller
  ctrl_byte = '\x08'
  device.write(bytearray(ctrl_byte))
  time.sleep(0.5)
  rtrn_byte = device.read(1)
  print `ctrl_byte`, `rtrn_byte`
  if `ctrl_byte` != `rtrn_byte`:
    raise DeviceError('Fatal', 'Could not ping serial port')
  return True 

def write(device, address, data): 
  write_array = bytearray()
  # write data to the controller
  ctrl_byte = '\x02'
  write_array.append(ctrl_byte)
  print `write_array`
  print address, hex(address)
  for byte in range(0,2):
#     print byte, hex((address>>(byte*8)) & 0xFF)
    write_array.append((address >> (byte*8)) & 0xFF)
  print `write_array`
  print data, hex(data)
  for byte in range(0,4):
#     print byte, hex((data>>(byte*8)) & 0xFF)
    write_array.append((data>> (byte*8)) & 0xFF)
  print `write_array`
  device.write(write_array)
  time.sleep(0.5)
  rtrn_byte = device.read(1)
  print `ctrl_byte`, `rtrn_byte`

def read(device, address): 
  write_array = bytearray()
  # write data to the controller
  ctrl_byte = '\x01'
  write_array.append(ctrl_byte)
  print `write_array`
  print address, hex(address)
  for byte in range(0,2):
    print byte, hex((address>>(byte*8)) & 0xFF)
    write_array.append((address >> (byte*8)) & 0xFF)
  print `write_array`
  device.write(write_array)

  a = bytearray(device.read(5))
  rtrn_byte = a[0]
  val = 0
  for b in range(0,4):
    val |= a[b + 1] << (b * 8)
  print hex(val)
  print ord(ctrl_byte)==rtrn_byte


# Set up serial comms
# serial_comm = serial.Serial(port='/dev/ttyUSB1', baudrate=115200, timeout=1)
serial_comm = serial.Serial(port='/dev/ttyUSB1', baudrate=115200)

# Establish communication
try:
 serial_comm.open()
except Exception as e:
  print str(e)
  sys.exit(1)

if serial_comm.isOpen():
  print 'port %s is open' % serial_comm.name
  try:
    serial_comm.flushInput()  # flush input buffer, discarding all its contents
    serial_comm.flushOutput() # flush output buffer, aborting current output and discard all that is in buffer
    starttime = time.time()
    ping(serial_comm)         #
    print "ping device took %f seconds" % (time.time()-starttime)
  except DeviceError as de:
    print '%s: %s' % (de.level, de.msg)
    sys.exit(1)
else:
  print 'Cannot open serial port', serial_comm.name
  # Closing before exit
  print 'Closing port %s' % serial_comm.name
  serial_comm.close()
  sys.exit(1)

# create the register address
addr=__register_address__(mod=1,reg=1)
print `addr`, bin(addr), hex(addr)
addr=__register_address__(mod=2,reg=2, read=True)
print `addr`, bin(addr), hex(addr)
starttime = time.time()
addr=__register_address__(mod=3,reg=5, read=True)
print `addr`, bin(addr), hex(addr)
print "generate address took %f seconds" % (time.time()-starttime)

# write data to port
addr=__register_address__(mod=1,reg=2)
print `addr`, bin(addr), hex(addr)
data = int('00001380', base=16)
starttime = time.time()
write(serial_comm, addr, data)
print "write data took %f seconds" % (time.time()-starttime)
# read data from port
addr=__register_address__(mod=1,reg=6, read=True)
print `addr`, bin(addr), hex(addr)
starttime = time.time()
read(serial_comm, addr)
print "read data took %f seconds" % (time.time()-starttime)


# Closing before exit
print 'Closing port %s' % serial_comm.name
serial_comm.close()


# -fin-
