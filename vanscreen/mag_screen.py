#!/usr/bin/env python3
"""
Collects data from twinleaf sensors for magnetic cleanliness testing.
"""
import sys           # System stuff
import os
import argparse    
import signal
import threading     # Mostly waiting on I/O so simple threads are okay
import time          # if the data rate needs to go up significantly we
import datetime      # will need to rewrite using the multiprocess module.
import getpass       # Username
import platform      # Hostname
from os.path import join as pjoin


# Math stuff
import numpy as np
from scipy.constants import pi
from scipy.constants import mu_0
from scipy.optimize import curve_fit
import scipy.stats as stats

from vanscreen import *

# The version of this software, need to be able to set this via the release
# process somehow
g_sVersion = "vanscreen-0.2"

# Output stuff
if (sys.platform != 'win32') and ('DISPLAY' not in os.environ):
	# Work around matplotlib bug on linux, it depends on the DISPLAY
	# environment variable but that's not always set anymore.
	os.environ['DISPLAY'] = ':0'
import matplotlib.pyplot as plt 

# Global variable and signal handler to halt main data collection loop
g_lCollectors = []
g_display = None
g_bSigInt = False

perr = sys.stderr.write  # shorten a long function name
			
def setDone():
	"""Function triggered by a timer alarm that is setup in main()"""
	global g_lCollectors
	for col in g_lCollectors:
		col.stop()
	if g_display != None:
		g_display.stop()

def setQuit(signal, frame):
	"""Signal handler for CTRL+C from the keyboard"""
	global g_bSigInt
	g_bSigInt = True      # Indicates early exit
	setDone()


# ############################################################################ #
# Data Processing #

def func(r, m): 
	"""equation of a magnetic field from a dipole moment"""
	return ((mu_0 * m) / (2*pi * r**3))

def ratio(magnetometer_distance, distance):
	"""
	Due to the Bx field and Bz field magnetometer being farther away from the object than the By field
	magnetometer, a ratio is needed to project the 3 B field components to the same place to accurately
	measure magntitude and direction
	"""
	return ((magnetometer_distance + distance)**3 / (distance)**3)

def rms(x, y, z):
	"""root mean squared function, eventually used to find magnitude of B"""
	return np.sqrt(x**2 + y**2 + z**2)

def angle(vector, B1, B2, B3):
	"""function finding angle from dot product of vectors"""
	z = np.array([0, 0, 1])
	return np.arccos( np.dot(vector, z) / np.sqrt(B1**2 + B2**2 + B3**2) )

def dipole_moment(object_length, distance, B, angle):
	"""General formula for finding dipole moment based off vector's magnitude and direction"""
	return (4*pi*(object_length/2+distance)**3*B) / (mu_0*(2*np.cos(angle)**2 - np.sin(angle)**2))

def fit(x, y, z):
	'''
	Main magnetic screening function.

	Finds the magnitude and direction of the object's dipole moment, then
	calculates a best fit.  Using this best fit, the function calculates the 
	stray field at one (1) meter away assuming the strongest possible dipole
	orientation. If the stray field is too large, the object fails the test.
	If he stray field is below the required threshold but is within the top 95%,
	it passes... with caution.

	Args:
		x -
		y - 
		z - 

	Returns:

	'''    

	#three distances object is being measured at, converted to meters
	distance = np.array([9, 11, 15])*1e-2 
	
	#converting the input magnetic fields into Tesla
	B_Tesla = np.array([
		x[0,0]*ratio(.01025, distance[0]), y[0,0], z[0,0]*ratio(.00475, distance[0]), 
		x[0,1]*ratio(.01025, distance[0]), y[0,1], z[0,1]*ratio(.00475, distance[0]),
		x[0,2]*ratio(.01025, distance[0]), y[1,2], z[1,2]*ratio(.00475, distance[0]),
		
		x[1,0]*ratio(.01025, distance[1]), y[1,0], z[1,0]*ratio(.00475, distance[1]),
		x[1,1]*ratio(.01025, distance[1]), y[1,1], z[1,1]*ratio(.00475, distance[1]),
		x[1,2]*ratio(.01025, distance[1]), y[1,2], z[1,2]*ratio(.00475, distance[1]),
		 
		x[2,0]*ratio(.01025, distance[2]), y[2,0], z[2,0]*ratio(.00475, distance[2]),
		x[2,1]*ratio(.01025, distance[2]), y[2,1], z[2,1]*ratio(.00475, distance[2]),
		x[2,2]*ratio(.01025, distance[2]), y[2,2], z[2,2]*ratio(.00475, distance[2])
	])*1e-9
	
	# Organizing vectors of Bx, By, Bz components from 3 different orientations at 3
	# different distances
	# Hint: complex index calculations in loop below could be shortened if a 3-D array
	#       were used here.  The axes would be row, column, component, 
	#       i.e. B_Tesla[row,col,comp]

	vector = np.array([
		np.array([B_Tesla[ 0], B_Tesla[ 1], B_Tesla[ 2]]), 
		np.array([B_Tesla[ 3], B_Tesla[ 4], B_Tesla[ 5]]), 
		np.array([B_Tesla[ 6], B_Tesla[ 7], B_Tesla[ 8]]),
		np.array([B_Tesla[ 9], B_Tesla[10], B_Tesla[11]]), 
		np.array([B_Tesla[12], B_Tesla[13], B_Tesla[14]]),
		np.array([B_Tesla[15], B_Tesla[16], B_Tesla[17]]), 
		np.array([B_Tesla[18], B_Tesla[19], B_Tesla[20]]),
		np.array([B_Tesla[21], B_Tesla[22], B_Tesla[23]]), 
		np.array([B_Tesla[24], B_Tesla[25], B_Tesla[26]])
	])
	
	#finding dipole moment from each orientation at each distance, totaling 9 different dipole moments
	#m11 = dipole_moment(length_meters[0], distance[0], rms(B_Tesla[0], B_Tesla[1], B_Tesla[2]), angle(vector[0], B_Tesla[0], B_Tesla[1], B_Tesla[2]))
	#m12 = dipole_moment(length_meters[1], distance[0], rms(B_Tesla[3], B_Tesla[4], B_Tesla[5]), angle(vector[1], B_Tesla[3], B_Tesla[4], B_Tesla[5]))
	#m13 = dipole_moment(length_meters[2], distance[0], rms(B_Tesla[6], B_Tesla[7], B_Tesla[8]), angle(vector[2], B_Tesla[6], B_Tesla[7], B_Tesla[8]))
	#m21 = dipole_moment(length_meters[0], distance[1], rms(B_Tesla[9], B_Tesla[10], B_Tesla[11]), angle(vector[3], B_Tesla[9], B_Tesla[10], B_Tesla[11]))
	#m22 = dipole_moment(length_meters[1], distance[1], rms(B_Tesla[12], B_Tesla[13], B_Tesla[14]), angle(vector[4], B_Tesla[12], B_Tesla[13], B_Tesla[14]))
	#m23 = dipole_moment(length_meters[2], distance[1], rms(B_Tesla[15], B_Tesla[16], B_Tesla[17]), angle(vector[5], B_Tesla[15], B_Tesla[16], B_Tesla[17]))
	#m31 = dipole_moment(length_meters[0], distance[2], rms(B_Tesla[18], B_Tesla[19], B_Tesla[20]), angle(vector[6], B_Tesla[18], B_Tesla[19], B_Tesla[20]))
	#m32 = dipole_moment(length_meters[1], distance[2], rms(B_Tesla[21], B_Tesla[22], B_Tesla[23]), angle(vector[7], B_Tesla[21], B_Tesla[22], B_Tesla[23]))
	#m33 = dipole_moment(length_meters[2], distance[2], rms(B_Tesla[24], B_Tesla[25], B_Tesla[26]), angle(vector[8], B_Tesla[24], B_Tesla[25], B_Tesla[26]))
	
	# Should be equvalent to text above but double check
	m = np.zeros((3,3))
	
	for row in range(3):
		for col in range(3):
			m[row,col] = dipole_moment(
				length_meters[col], distance[row],
				rms( B_Tesla[ row*9 + col*3], B_Tesla[row*9 + col*3 + 1], B_Tesla[row*9 + col*3 + 2]),
				angle( vector[row*3 + col],   B_Tesla[row*9 + col*3 + 1], B_Tesla[row*9 + col*3 + 2])
			)
			
	m_observed = abs(np.array([m[1,1], m[1,2], m[1,3], m[2,1], m[2,2], m[2,3], m[3,1], m[3,2], m[3,3] ]))

	
	#x-axis is distances of from magnetometer plus center of object
	# Hint: Could use vectorized math operations here to make this a one-liner 
	#       i.e. xdata = distance + length_meters/2
	#       which would implicitly loop over all similar indicies.
	xdata = np.array([
		distance[0]+length_meters[0]/2, distance[0]+length_meters[1]/2, distance[0]+length_meters[2]/2,
		distance[1]+length_meters[0]/2, distance[1]+length_meters[1]/2, distance[1]+length_meters[2]/2, 
		distance[2]+length_meters[0]/2, distance[2]+length_meters[1]/2, distance[2]+length_meters[2]/2
	])
	ydata = func(xdata, m_observed) #y-axis is mangetic fields from strongest possible dipole orientation
	plt.plot(xdata*1e2, ydata*1e9, 'bo',label="observed data") #plotting measured strongest magnetic field vs. distance
	
	plt.xlabel("distance (centimeters)")
	plt.ylabel("magnetic field (nanoTesla)")
	popt, pcov = curve_fit(func, xdata, ydata) #curve fitting best fit of the nine magnetic fields measured
	plt.plot(xdata*1e2, func(xdata, *popt)*1e9, 'r-',label='best fit') #plotting best fit line
	plt.legend()
	plt.show()
	
	m_err = np.sqrt(np.diag(pcov)) #estimated covariance of popt, aka one standard deviation errors on the parameters
	
	#Chi-squared calculated from values deviated from the expected
	print("chi-squared test statistic: %.3f" %stats.chisquare(f_obs=m_observed, f_exp=popt)[0]) 
	
	#p-value calculated from chi-squared
	print("p-value: %.3f" %stats.chisquare(f_obs=m_observed, f_exp=popt)[1])
	
	stray_B = (mu_0 * popt) / (2*pi*1**3) #calculating stray field at 1 meter from strongest orientation best-fit magnetic dipole moment
	
	print("magnetic dipole moment m = %.5f" %popt, "+/- %.4f" %m_err) #printing best fit magnetic dipole moment
	print("stray field B = %.4f nT" %(stray_B*1e9), "+/- %.4f" %(((mu_0 * m_err) / (4*pi))*1e9)) #printing stray magnetic field at 1 meter

	# If best fit dipole moment over .1 mA^2, object does not pass test. 
	# If m is under 95% of .1, it passes completely. 
	# If m is between .1 and 95% of .1, it should be used with caution    
	if popt+m_err > .05: 
		print("-> FAIL")
	elif popt+m_err < (.95*.05):
		print("-> PASS")
	else:
		print("-> CAUTION")


def get_moments(collectors):
	"""Convert the raw data stream off a Twinleaf mag sensor set into
	a dictionary of values that contains information we care about.  Also
	folds in the object measurements.
	
	args:
		collectors: A list of Collector objects that presumably have
					collected data from a TwinLeaf sensor. 
	"""    
	#data = {'DIMS':obj_dims}
	data = {}
	
	for collector in collectors:
		sId = collector.sid
	
		perr('Sensor %s: %d rows collected\n'%(sId, len(collector.raw_data)))
		
		# Cole: Make calls to fit() and the other function above here.  Then 
		# Gather all output into a dictionary object and return it, for now
		# I'm just outputting the raw data.  Feel free to ajdust the output 
		# data dictionary to have whatever structure you deem suitable.
		data[sId] = {'T':collector.times(), 'B':collector.mag_vectors()}
	
		T = data[sId]['T']
		B = data[sId]['B']
	
		perr('%s Sensor, Row    0: %7.3f (%10.3f, %10.3f, %10.3f)\n'%(
			sId, T[0], B[ 0,0], B[ 0,1], B[ 0,2]
		))
		perr('          Row    1: %7.3f (%10.3f, %10.3f, %10.3f)\n'%(
			T[1], B[1,0], B[1,1], B[1,2]
		))
		perr('          Row    2: %7.3f (%10.3f, %10.3f, %10.3f)\n'%(
			T[2], B[2,0], B[2,1], B[2,2]
		))
		perr('          Row %4d: %7.3f (%10.3f, %10.3f, %10.3f)\n'%(
			len(T), T[-1], B[-1,0], B[-1,1], B[-1,2]
		))
		
	perr('Data formatter not yet implemented\n')
	return data

# Data Processing #
# ############################################################################ #

# ############################################################################ #
# Data Output #


def test_properties(sPart, sComments=None):
	"""Return a dictionary of basic properties for a screening test"""
	d = {
		'Part':sPart,
		'Timestamp': time.strftime('%Y-%m-%dT%H:%M:%S%z'), # Use ISO 8601 local times
		'User': getpass.getuser(),
		'Host': platform.node(),
		'Version':g_sVersion
	}

	if sComments: d['Note'] = sComments.replace('"',"'")
	return d	

def write_pdf(directory, name, data):
	"""Generate plots using matplotlib of formatted data and save to a PDF file
	
	args:
		directory (str): The directory to write to, if None use current location.
		name (str): The filename to write, if None generate name based of current
			timestamp
		data (dict): The data dictionary as created by get_moments above
	"""
	
	perr('PDF plotter function not yet implemented\n')

# Data Output #
# ############################################################################ #

def main():
	"""Program entry point, see argparse setup below or run with -h for overall
	scope and usage information.

	Returns:
		A standard integer success or fail code suitable for return to
		the calling shell. 0 = success, non-zero = various error conditions
	"""
	global g_lCollectors, g_display, g_sigint
	
	psr = argparse.ArgumentParser(formatter_class=CustomFormatter)
	psr.description = '''\
		Collect magnetic sensor data from twinleaf sensors for a fixed time
		period and output data and plot files.'''
	psr.epilog = '''\
	Author: cole-dorman@uiowa.edu, chris-piker@uiowa.edu\v
	Source: https://research-git.uiowa.edu/space-physics/tracers/magic/utilities
	'''
	
	# By tradition, optional command line parameters are first...
	psr.add_argument(
		'-r', '--rate', dest='sample_hz', metavar='HZ', type=int, default=10,
		help='The number of data points to collect per sensor, per second.  '+\
		     'Defaults to 10 Hz so that slow python code can keep up.\n'
	)
	
	psr.add_argument(
		'-t', '--time', dest='duration', metavar='SEC', type=int, default=20,
		  help='The total number of seconds to collect data, defaults to 20.\n'
	)
		 
	defs = {
		'name':(0,1,2), 'dist':(9, 11, 15), 'serial':('DT04H6OF','DT04H6OX','DT04H6NY')
	}
	
	for i in range(3):
		ser_num = defs['serial'][i]
		
		psr.add_argument(
			"--s%d"%defs['name'][i], dest='serialno%d'%defs['name'][i], metavar='SERIAL',
			type=str, default=ser_num,
			help='The UART serial number of the UART hosting VMR sensor ' +\
			"%d"%defs['name'][i] + '.  Defaults to ' + ser_num + '.  To ignore data '+\
			'from this sensor give an empty string as the serial number (i.e. "").' +\
			'The full serial number need not be supplied so long the provide string '+\
			'is sufficent to distinguish each sensor.'
		)

		psr.add_argument(
			"--d%d"%defs['name'][i], dest='dist%s'%defs['name'][i], metavar='CM', 
			type=float, default=defs['dist'][i],
			help='The distance in cm from the (TBD location) to the front face '+\
			'of sensor %d'%defs['name'][i] + '.  Defaults to %d cm.\n'%defs['dist'][i]
		)
	
	psr.add_argument(
		'-d', '--out-dir', dest='out_dir', metavar='DIR', type=str,
		default='.', help='Output files to folder/directory DIR instead of '+\
		'the current location'
	)

	psr.add_argument(
		'-m', '--message', dest="msg", metavar="NOTE", type=str, default=None,
		help="Add a message to be included in the output files."
	)
	
	# ... and positional parameters follow
	psr.add_argument("PART", 
		help="An identifier for the object to be measured.  Will be used as "+\
		"part of the output filenames."
	)
	
	opts = psr.parse_args()
		
	# Set user interup handlers in case user wants to quite early.
	signal.signal(signal.SIGINT, setQuit)
	signal.signal(signal.SIGTERM, setQuit)
	
	# Since SIGALRM isn't available on Windows, spawn a thread to countdown to
	# the end of the data collection period, check user supplied time
	if opts.duration < 1 or opts.duration > 60*60:
		perr('Test duration must be between 1 second and 1 hour\n')
		return 7
	
	# Set at X samples per second per sensor, should be no more then
	# 10 samples per second so that slow python code can keep up
	if (opts.sample_hz < 1) or (opts.sample_hz >= 200):
		perr("Requested sample rate %d is out of expected range 1 to 200 (Hz)."%opts.sample_hz)
		return 8

	rTime0 = time.time()  # Current unix time in floating point seconds
	
	g_bSigInt = False    # Global interrupt flag

	# Check that our non-empty sensors can be distinguished from each other
	g_lCollectors = []
	tSer = (opts.serialno0, opts.serialno1, opts.serialno2)
	for i in range(3):
		if len(tSer) == 0: continue

		lTest = []
		for j in range(3): 
			if (j != i) and (len(tSer[j]) > 0): lTest.append(tSer[j])
		if i in lTest:
			perr("UART serial number %s is not unique!\n")
			return 13

		try:
			g_lCollectors.append( VMR('%d'%i, tSer[i], opts.sample_hz) )
		except OSError as e:
			perr("ERROR: %s\n"%e)
			perr('INFO: Sensors can be ignored using -s0 "", -s1 "", or -s2 "".')
			perr('  Use -h for more info.\n')
			return 15

		g_lCollectors[-1].set_time0(rTime0)
		g_lCollectors[-1].set_dist(opts.sample_hz)

	if len(g_lCollectors) == 0:
		perr('No data collection ports specified, successfully did nothing.\n')
		return 0
	
	# Create a display output thread
	perr("Use CTRL+C to quit early\n")
	g_display = Display("Collecting ~%d seconds of data "%opts.duration)
	
	# create an alarm thread to stop taking data
	alarm = threading.Timer(opts.duration + (time.time() - time0), setDone)
	
	# Start all the threads
	for collector in g_lCollectors:
		collector.start()
	alarm.start()
	g_display.start()
	
	# Wait on all my threads to exit
	for collector in g_lCollectors:
		if collector:
			collector.join()
	g_display.join()
	
	alarm.cancel() # Cancel the alarm if it hasn't gone off
	perr('\n')
	if g_bSigInt:
		perr('Data collection terminated, no output written\n')
		return 4  # An error return value
	
	# Save raw-data from collectors
	sFile = pjoin(opts.out_dir, "%s.csv"%safe_filename(opts.PART))
	sTitle = "Magnetic Screening Test, Raw Data"
	save_mag_vecs(sFile, g_lCollectors, sTitle, test_properties(opts.PART, opts.msg))

	# Parse raw data from the collectors into meaningful measurments
	data = get_moments(g_lCollectors)
	
	# Output what we got
	write_pdf(opts.PART, opts.out_dir, data)
	
	return 0  # An all-okay return value
	
	
# Run the main function and give it the command line arguments
if __name__ == "__main__":
	sys.exit(main())
