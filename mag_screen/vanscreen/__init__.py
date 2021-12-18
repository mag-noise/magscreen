"""Utilities for magnetic screening, mostly using Twinleaf sensors"""

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
	def __init__(self, tlmodule, axis, port, time0):
		threading.Thread.__init__(self)
		self.axis = axis
		self.port = port
		self.time0 = time0
		self.time = []
		self.raw_data = []
		perr('Connecting to %s for %s axis data.\n'%(port, axis))
		self.device = tlmodule.Device(port)
		
		# Save off the names of the data columns
		self.columns = self.device._tio.protocol.columns
	
	def run(self):
		global g_quit, g_collect
		for row in self.device.data.stream_iter():
			if g_quit or (not g_collect):
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
