"""Utilities for magnetic screening, mostly using Twinleaf sensors"""

import argparse
import threading
import time
import sys
import numpy as np

perr = sys.stderr.write  # shorten a long function names

class VertFormatter(argparse.HelpFormatter):
	"""Allow for manual line breaks in description and epilog blocks of help text.
	To insert a line break use the vertical tab (\\v) character into a text block."""
	def _fill_text(self, text, width, indent):
		import textwrap
		l = []
		for s in text.split('\v'):
			s = self._whitespace_matcher.sub(' ', s).strip()
			l.append(textwrap.fill(
				s, width, initial_indent=indent, subsequent_indent=indent
			))
		return '\n'.join(l)
		

class TlCollector(threading.Thread):
	"""
	Gather data from a single serial port and generate a list ofdata values
	and associated time values
	"""
	def __init__(self, tlmodule, sid, port, time0):
		threading.Thread.__init__(self)
		self.sid = sid
		self.port = port
		self.time0 = time0
		self.time = []
		self.raw_data = []
		perr('Connecting to %s for sensor %s data.\n'%(port, sid))
		self.device = tlmodule.Device(port)
		
		# Save off the names of the data columns
		self.columns = self.device._tio.protocol.columns
		self.go = False      

	def stop(self):
		self.go = False
	
	def run(self):
		self.go = True
		for row in self.device.data.iter():
			if not self.go:
				break
			self.time.append(time.time() - self.time0)
			self.raw_data.append(row)
			
	def mag_vectors(self):
		"""Output an [N x 3] array of the mag vectors"""
		vecs = np.zeros([len(self.raw_data), 3])
		iX = self.columns.index('vector.x')
		iY = self.columns.index('vector.y')
		iZ = self.columns.index('vector.z')
		
		# TODO: Vectorize this
		for i in range(len(self.raw_data)):
			vecs[i,0] = self.raw_data[i][iX]
			vecs[i,1] = self.raw_data[i][iY]
			vecs[i,2] = self.raw_data[i][iZ]
		
		return vecs
		
	def times(self):
		"""Output an [N] length array of the time points"""
		return np.array(self.time)
		
	def time0(self):
		"""Get time0 as an ISO-8601 string"""
		dt = datetime.datetime.utcfromtimestamp(self.time0)
		return "%04d-%02d-%02dT%02d:%02d:%02d"%(
			dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second
		)


class Display(threading.Thread):
	"""This is a simple aliveness printer.  It outputs a single . once a 
	second to stdout.  You could customize it to do more interesting things
	if desire.
	"""
	def __init__(self, prefix=""):
		threading.Thread.__init__(self)
		self.prefix = prefix
		self.go = False

	def stop(self):
		self.go = False
	
	def run(self):
		# Write dot's to screen so folks know the program isn't dead.  For a
		# fancier display see:
		# https://github.com/twinleaf/tio-python/blob/master/examples/tio-monitor.py
		# specifically the update() function.
		self.go = True
		num_dots = 0
		while self.go:
			if num_dots == 0: perr(self.prefix)
 
			time.sleep(1) # Sleep for 1 second           
			if num_dots % 10 == 9:
				perr('%d'%(num_dots+1))
			else:
				perr('.')
			sys.stderr.flush()
			num_dots += 1