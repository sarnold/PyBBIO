# i2c.py 
# Part of PyBBIO
# github.com/alexanderhiam/PyBBIO
# This library - github.com/deepakkarki
# Apache 2.0 license
# 
# Beaglebone i2c driver

#Note : Three i2c buses are present on the BBB; i2c-0 is used for eeprom access - so not useable
#		i2c-1 is loaded default; /devices/ocp.2/4819c000.i2c/i2c-1  ---- this actually is the i2c2 bus
#		to activate i2c1 bus; echo BB-I2C1 > /sys/devices/bone_capemgr.8/slots; will be now present at /dev/i2c-2
#		reference : http://datko.net/2013/11/03/bbb_i2c/

##
##		NOTE : UNTESTED CODE! DO NOT USE!
##

from config import *
import  cape_manager, bbio

try:
  import smbus
except:
  print "\n python-smbus module not found\n"

#currently for kernel 3.8 only
def i2cInit(bus):
	'''
	Initializes reqd I2C bus
	i2c0 (/dev/i2c-0) and i2c2 (/dev/i2c-1) are already initialized
	overlay to be applied for i2c1 (/dev/i2c-2)
	'''
	dev_file, overlay = I2C[bus]
	if os.path.exists(dev_file): 
		return True
	cape_manager.load(overlay, auto_unload=False)
	
	if os.path.exists(dev_file): 
		return True

	for i in range(5):
		bbio.delay(5)
		if os.path.exists(dev_file): 
			return True

	return False


class _I2C_BUS(object):

	def __init__(self, bus):
		'''
		self : _I2C_BUS object
		bus : string - represents bus address eg. i2c1, i2c2
		'''
		self.config = bus
		self.bus = None # This is the smbus object
		self.open = False

	def begin(self):
		'''
		Initializes the I2C bus with BBB as master
		'''
		if not i2cInit(self.config):
			print "Could not initialize i2c bus : %s" % self.config 
			return
		self.bus = smbus.SMBus(int(I2C[self.config][0][-1]))
		self.open = True

	def write(self, addr, val):
		'''
		Writes value 'val' to address 'addr'
		addr : integer between (0-127) - Address of slave device
		val : string, integer or list - if list, writes each value in the list
		returns number of bytes written
		'''
		if not self.open:
			print "I2C bus : %s - not initialized" % self.config

		if type(addr) == int:
			return self.bus.write_byte(addr, val)

		else:
			data = self._format(val)
			written = 0 #bytes of data written
			for unit in data:
				written += self.bus.write_byte(addr, val)
			return written


	def _format(self, val):
		'''
		used to format values given to write into reqd format 
		val : string or list (of integers or strings)
		returns : list of integers, if bad paramater - returns None
		'''

		if type(val) == str:
			return map(lambda x: ord(x), list(val))

		if type(val) == list and len(val):
			#non empty list

			if len(filter(lambda x: type(x) == int, val)) == len(val):
				#all variables are integers
				return val

			if len(filter(lambda x: type(x) == str, val)) == len(val):
				#all variables are strings
				data = []
				for unit in val:
					data.extend(list(unit))
				return map(lambda x: ord(x), list(data))

		return None



	def read(self, addr, size=1):
		'''
		Reads 'size' number of bytes from slave device 'addr'
		addr : integer between (0-127) - Address of slave device
		size : integer - number of bytes to be read
		returns an int if size is 1; else list of integers
		'''
		if not self.open:
			print "I2C bus : %s - not initialized, open before read" % self.config

		if size == 1:
			return self.bus.read_byte(addr)

		else:
			read_data = []
			for i in range(size):
				data = self.bus.read_byte(addr)
				if data == -1: #No more data to be read
					break
				else :
					read_data.append(data)

		return read_data


	def end(self):
		'''
		BBB exits the bus
		'''
		if self.bus:
			result = self.bus.close()
			if not result:
				print "Failed to close i2c bus : %s" % self.config 
				return False
			self.open = False
			return True
		else:
			print "i2c bus : %s - is not open. use begin() first" % self.config 



	def _process(self, val):
		'''
		Internal function to handle datatype conversions while writing to the devices
		val - some object
		returns a processed val that can be written to the I2C device
		'''
		# Keep this for prints, add the below check in write itself. All that is allowed is [int, str, list(int), list(str)]
		pass

	def prints(self, addr, string):
		'''
		prints a string to the device with address 'addr' 
		addr : integer(0-127) - address of slave device
		string : string - to be written to slave device
		'''
		pass
		#fill this later - could be used to send formatted text across to some I2C based screens (?)

def i2c_cleanup():
	"""
	Ensures that all i2c buses opened by current process are freed. 
	"""
	for bus in (Wire1, Wire2):
		if bus.open:
			bus.end()

Wire1 = _I2C_BUS('i2c1')
Wire2 = _I2C_BUS('i2c2')