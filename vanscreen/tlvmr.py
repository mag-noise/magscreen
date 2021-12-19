"""Utilities for collecting data from Twinleaf VMR sensors"""

import os
import sys
import threading
import numpy as np
import time
import datetime

from os.path import dirname as dname

perr = sys.stderr.write  # shorten a long function names

class VMR(threading.Thread):
	"""
	Gather data from a single serial port and generate a list ofdata values
	and associated time values
	"""
	def __init__(self, tlmodule, sid, port, dist, time0):
		threading.Thread.__init__(self)
		self.sid = sid      # Sensor ID
		self.port = port    # Comm port
		self.dist = dist    # In centimeters
		self.time0 = time0  # Zero time for measurements
		self.time = []      # Time values for measurements 
		self.raw_data = []  # Raw mag, accel, gyro, pressure & thermal data values

		perr('Connecting to %s for sensor %s data.\n'%(port, sid))
		self.device = tlmodule.Device(port)
		
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

	def time0(self, new_zero):
		"""Reset the zero time for measurements.
		Args:
			new_zero (float): A unix time as returned by time.time()
		"""
		self.time0 = new_zero

	def stop(self):
		self.go = False
	
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