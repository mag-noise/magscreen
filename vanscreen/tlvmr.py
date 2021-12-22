"""Utilities for collecting data from Twinleaf VMR sensors"""

import os
import sys
import threading
import numpy as np
import time
import datetime
import serial
import serial.tools.list_ports
from os.path import dirname as dname

try:
	import tldevice
except ImportError as exc:
	perr('%s\nGo to https://github.com/twinleaf/tio-python install instructions\n'%str(exc))
	
perr = sys.stderr.write  # shorten a long function names

# ########################################################################## #
def find_device(serialno, pid=0x6015, vid=0x0403):
	"""Find the port number for a serial device.

	Args:
		serialno (str): The inital portion of the serial number.  The device 
			serial number must start with this string.  On Windows serial
			numbers are typically right extended with sub identifier, thus
			the full serial number need not match.

		pid (int): The product ID for the device.  An example is 0x6015,
			which is the FTDI, FT230X Basic UART.

		vid (int): The vendor ID for the device.  An example is 0x0403 which
		   is assigned to 'FTDI - Future Technology Devices International LTD'

	Returns:
		str: The port name.  On Linux this will be /dev/ttyUSB0 or similar. 
			On Windows it will be COM1 or similar
		None: If the device could not be found.
	"""
	port = None
	lDevs = serial.tools.list_ports.comports()
	for dev in lDevs:
		if not dev.serial_number: continue
		if dev.vid != vid: continue
		if dev.pid != pid: continue

		if dev.serial_number.startswith(serialno):
			return dev.device  # The device file name or com port name

	return None

# ########################################################################## #

class VMR(threading.Thread):
	"""
	Gather data from a single serial port and generate a list ofdata values
	and associated time values
	"""
	def __init__(self, sid, serialno, hertz, pid=0x6015, vid=0x0403):
		"""Create a new VMR communication object.

		Instead of connecting to a specific COM or TTY port, available ports are
		queried for the given UART serial number, and if a match is found, a port
		number association is made.  Since adaptor boxen can be physically labeled
		with the UART serial number this avoids port assignment confusion.

		Args:
			sid (str): Sensor ID, this is typically an integer from 0 to 2 as a string.

			hertz (int): Set the data sampling rate in Hertz.  Value must be between
				1 Hz and 200 Hz inclusive.  For three sensors 10 Hz is recommended.
				
				Note: On Windows rate settings can't be changed after collecting data.
				      So the rate is sent in this constructor.

			serialno (str): The serial number of the UART to which the sensor is
				attached.  The full serial number need not be supplied.  The device
				serial number only needs to startwith this string in order to be 
				considered a match.

			pid (int): The product ID for the device.  Defaults to 0x6015,
				which is the FTDI, FT230X Basic UART.

			vid (int): The vendor ID for the device.  Defaults to 0x0403 which
		   is assigned to 'FTDI - Future Technology Devices International LTD'
		"""
		threading.Thread.__init__(self)
		self.sid = sid      # Sensor ID
		self.serialno = serialno
		self.dist = 999     # In centimeters
		self.rate = hertz
		self.time0 = time.time()
		self.time = []      # Time values for measurements 
		self.raw_data = []  # Raw mag, accel, gyro, pressure & thermal data values

		self.port = find_device(serialno,pid,vid)
		if self.port is None:
			raise EnvironmentError(
				"Could not locate device serial %s, VID:SID=%04X:%04X."%(serialno, pid, vid)+\
				"\n       Try unplugging and replugging the USB cable to trigger hot-plug actions."
			)

		perr('Connecting to UART %s on port %s for %d Hertz data for sensor %s\n'%(
			self.serialno, self.port, self.rate, self.sid
		))

		xPkt = bytearray(b'data.rate %d\r'%hertz)
		s = serial.serial_for_url(self.port, baudrate=115200, timeout=1)
		s.write(xPkt)
		s.close()

		self.device = tldevice.Device(self.port)
		
		# Save off the names of the data columns
		self.columns = self.device._tio.protocol.columns
		self.iBx = self.columns.index('vector.x')
		self.iBy = self.columns.index('vector.y')
		self.iBz = self.columns.index('vector.z')
		self.go = False

		# Information about this sensor
		self.dev_info = self.device.dev.desc()
		
      # Internal magnetometer displacement from front face of sensor in long
      # dimension.        X     Y     Z
		self.displace = [0.01025, 0, 0.00475]

	def set_dist(self, dist):
		"""Set the distance from the sensor to the object measured

		Args:
			dist (float): The distance in centimeters from front face of the VMR 
				sensor to the (center?) of the object to be measured.
		"""
		self.dist = dist

	def set_time0(self, new_zero):
		"""Reset the zero time for measurements.
		Args:
			time0 (float): The zero time for all measurements.  Data are saved as
				offsets from this time point.  This is a floating point number of 
				seconds as output from time.time().
		"""
		self.time0 = new_zero

	def stop(self):
		self.go = False

	def close(self):
		"""Close the comm port for this sensor.  Do this before creating an 
		new connection to the same sensor at a different sampling rate.
		"""
	
	def run(self):
		self.raw_data = []
		self.go = True
		for row in self.device.data.iter():
			if not self.go:
				break
			self.time.append(time.time() - self.time0)
			self.raw_data.append(row)
			
	def mag_vectors(self):
		"""Output an [N x 3] array of the mag vectors"""
		vecs = np.zeros([len(self.raw_data), 3])
		
		# TODO: Vectorize this
		for i in range(len(self.raw_data)):
			vecs[i,0] = self.raw_data[i][self.iBx]
			vecs[i,1] = self.raw_data[i][self.iBy]
			vecs[i,2] = self.raw_data[i][self.iBz]
		
		return vecs

	def __len__(self):
		"""Provide data length method"""
		return len(self.raw_data)

	def __getitem__(self, key):
		"""Provide get data by index method, akay []"""
		return (
			self.time[key], self.raw_data[key][self.iBx],
			self.raw_data[key][self.iBy], self.raw_data[key][self.iBz]
		)

		
	def times(self):
		"""Output an [N] length array of the time points"""
		return np.array(self.time)
		
	def time0(self):
		"""Get time0 as an ISO-8601 string"""
		dt = datetime.datetime.utcfromtimestamp(self.time0)
		return "%04d-%02d-%02dT%02d:%02d:%02d"%(
			dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second
		)


def save_mag_vecs(sFile, lVMRs, sTitle=None, dProps=None):
	"""Save a set of VMR readings to a CSV file
	Args:
		sFile (str): The abs pathname to write, directories are created if needed
		lVMRs (list,VMR): A list of VMR objects with data
		dProps (dict): A dictionary of extra properties to save in the file
	Returns:
		The total number of mag vectors written


	Output:
		Writes data in the following layout:

		Properties

		Sens1 Time, Sens1 Bx, Sens1 By, Sens1 Bz, (empty row), Sens2 Time, Sens2 Bx, ...

		All columns have header rows
	"""

	sDir = dname(sFile)
	if len(sDir) > 0: os.makedirs(sDir, exist_ok=True)
		
	if not sFile.lower().endswith('.csv'):  sFile = "%s.csv"%sFile

	# Number of columns is lVMRs*4 or 2 if no vmrs
	if len(lVMRs) > 0:
		nCols = len(lVMRs)*4 + (len(lVMRs) - 1)
	else:
		nCols = 2

	nSensors = len(lVMRs)

	# Control our newline chars, mime text/csv (RFC-4180) calls for \r\n explicitly
	with open(sFile, 'w', newline='') as fOut:

		if sTitle:
			fOut.write('"%s"'%sTitle.replace('"',"'"))
			fOut.write("%s\r\n%s\r\n"%(','*(nCols - 2), ','*(nCols - 1)))

		# Property headers
		if dProps:
			lKeys = list(dProps.keys())
			lKeys.sort()
			for key in lKeys:
				fOut.write('"%s","%s"'%(key.replace('"',"'"), dProps[key].replace('"',"'")))

				if nCols > 2: fOut.write(','*(nCols - 2))
				fOut.write('\r\n')

		if nSensors == 0: return  # If no sensors, just write the properties

		# Sensor Headers
		fOut.write(','*(nCols-1)+'\r\n')

		for i in range(nSensors):   # Device ID
			vmr = lVMRs[i]
			if i > 0: fOut.write(',,')
			fOut.write('"Sensor %s ID","%s",,'%(vmr.sid, vmr.dev_info))
		fOut.write('\r\n')

		for i in range(nSensors):   # Device port
			vmr = lVMRs[i]
			if i > 0: fOut.write(',,')
			fOut.write('"Sensor %s Port","%s",,'%(vmr.sid, vmr.port))
		fOut.write('\r\n')		

		for i in range(nSensors):   # Device distance
			vmr = lVMRs[i]
			if i > 0: fOut.write(',,')
			fOut.write('"Sensor %s Dist",%0.2f,"[cm]",'%(vmr.sid, vmr.dist))
		fOut.write('\r\n')

		for i in range(nSensors):   # Device time base
			vmr = lVMRs[i]
			if i > 0: fOut.write(',,')
			fOut.write('"Sensor %s Time[0]","%s",,'%(vmr.sid, _basetime(vmr.time0)))
		fOut.write('\r\n')

		fOut.write('%s\r\n'%(','*(nCols-1)))

		# Data column headers
		if nSensors: fOut.write(','*nCols+'\r\n')
		for i in range(nSensors):
			vmr = lVMRs[i]
			if i > 0: fOut.write(',,')
			fOut.write('"time offset [s]","Bx [nT]","By [nT]","Bz [nT]"')
		fOut.write('\r\n')

		# Saving data values
		i = 0 # Sensor
		nRow = 0
		while True:
			nRow += 1
			nDone = 0
			for i in range(nSensors):
				vmr = lVMRs[i]
				if nRow > len(vmr): nDone += 1

			if nDone >= nSensors:  break # Stop condition

			# At least one still has data
			for i in range(nSensors):
				vmr = lVMRs[i]
				if i > 0: fOut.write(',,')

				if nRow > len(vmr):  fOut.write(',,,')
				else:  fOut.write('%.3f,%.1f,%.1f,%.1f'%vmr[nRow - 1])

			fOut.write('\r\n')

	nVals = sum([ len(vmr) for vmr in lVMRs]) * 3

	perr("%d raw measurements written to %s"%(nVals, sFile))


def _basetime(rTime):
	sTime = datetime.datetime.fromtimestamp(rTime).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
	sTz = time.strftime("%z",time.localtime(rTime))
	return "%s%s"%(sTime, sTz)