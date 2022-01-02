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

def _test_properties(sPart, sComments=None):
	"""Return a dictionary of basic properties for a screening test"""
	d = {
		'Part':sPart,
		'Timestamp': time.strftime('%Y-%m-%dT%H:%M:%S%z'), # Use ISO 8601 local times
		'User': getpass.getuser(),
		'Host': platform.node().lower(),
		'Version':g_sVersion
	}

	if sComments: d['Note'] = sComments.replace('"',"'")
	return d	


def test_summary(sOutFile, dProps, lDatasets):

	# Now for the roll-up information...
	(aDist, aRotRate, aBmax, rMoment, rMomErr) = calc.dipole_from_rotation(lDatasets)
	
	(rStray, rStrayErr) = calc.stray_field(1, rMoment, rMomErr)
	
	


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
		perr('ERROR: Test duration must be between 1 second and 1 hour\n')
		return 7
	
	# Set at X samples per second per sensor, should be no more then
	# 10 samples per second so that slow python code can keep up
	if (opts.sample_hz < 1) or (opts.sample_hz >= 200):
		perr("ERROR: Requested sample rate %d is out of expected range 1 to 200 (Hz)."%opts.sample_hz)
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
			perr("ERROR: UART serial number %s is not unique!\n")
			return 13

		try:
			g_lCollectors.append( VMR('%d'%i, tSer[i], opts.sample_hz) )
		except OSError as e:
			perr("ERROR: %s\n"%e)
			perr('INFO:  Sensors can be ignored using -s0 "", -s1 "", or -s2 "".')
			perr('  Use -h for more info.\n')
			return 15

		g_lCollectors[-1].set_time0(rTime0)
		g_lCollectors[-1].set_dist(opts.sample_hz)

	if len(g_lCollectors) == 0:
		perr('INFO:  No data collection ports specified, successfully did nothing.\n')
		return 0
	
	# Create a display output thread
	perr("MSG:   Use CTRL+C to quit early\n")
	g_display = Display("MSG:   Collecting ~%d seconds of data "%opts.duration)
	
	# create an alarm thread to stop taking data
	alarm = threading.Timer(opts.duration + (time.time() - rTime0), setDone)
	
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
		perr('WARN:  Data collection terminated, no output written\n')
		return 4  # An error return value
	
	# Save raw-data from collectors
	sFile = pjoin(opts.out_dir, "%s.csv"%safe_filename(opts.PART))
	sTitle = "Magnetic Screening Test, Raw Data"
	write_mag_vecs(sFile, g_lCollectors, sTitle, _test_properties(opts.PART, opts.msg))

	# Plot time series and PSD of the raw data, as a cross check
	(dProps, lDatasets) = semcsv.read(sFile)
	plot.screen_plot_pdf(dProps, lDatasets, sFile.replace('.csv','.pdf'))
	
	# Open the roll-up info file (or create one if it doesn't exist)
	test_summary("summary.csv", dProps, lDatasets)
	
	return 0  # An all-okay return value
	
	
# Run the main function and give it the command line arguments
if __name__ == "__main__":
	sys.exit(main())
