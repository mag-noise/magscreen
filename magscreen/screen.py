#
# Copyright 2022 Chris Piker, Cole Dorman
#
# This file is part of magscreen
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

import magscreen.common as common # Local modules
import magscreen.tlvmr as tlvmr
import magscreen.semcsv as semcsv
import magscreen.plot as plot
import magscreen.summary as summary


# The version of this software, need to be able to set this via the release
# process somehow
g_sVersion = "magscreen-0.3"

# Output stuff
#  This is no longer needed using AGG matplotlib backend...
#if (sys.platform != 'win32') and ('DISPLAY' not in os.environ):
#	# Work around matplotlib bug on linux, it depends on the DISPLAY
#	# environment variable but that's not always set anymore.
#	os.environ['DISPLAY'] = ':0'

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
	
	
def main():
	"""Program entry point, see argparse setup below or run with -h for overall
	scope and usage information.

	Returns:
		A standard integer success or fail code suitable for return to
		the calling shell. 0 = success, non-zero = various error conditions
	"""
	global g_lCollectors, g_display, g_sigint

	psr = argparse.ArgumentParser(formatter_class=common.BreakFormatter)
	psr.description = '''\
		Use 2 to N twinleaf VMR sensors to calculate the dipole moment of 
		an object slowly spinning in a static magnetic field.'''
	psr.epilog = '''\
	Author: chris-piker@uiowa.edu, cole-dorman@uiowa.edu\v
	Source: https://research-git.uiowa.edu/space-physics/utilities/python/vangse
	'''

	# By tradition, optional command line parameters are first...
	psr.add_argument(
		'-f', '--freq', dest='sRate', metavar='HZ', type=int, default=10,
		help='The number of data points to collect per sensor, per second.  '+\
				'Defaults to 10 Hz so that slow python code can keep up.\n'
	)

	psr.add_argument(
		'-t', '--time', dest='sDuration', metavar='SEC', type=int, default=20,
			help='The total number of seconds to collect data, defaults to 20.\n'
	)

	sDef="9,11,15"
	psr.add_argument(
		"-r","--radius", dest='sRadii', metavar="CM,CM,...", type=str, 
		default=sDef,  help="The distance from the center of the object to "+\
		"each VMR sensor face in centimeters.  Defaults to %s cm.  Note "%sDef+\
		"that the number of distances given (or assumed) defines the number "+\
		"of expected sensors.  If less than, or more than 3 sensors are to "+\
		"be read this argument is required.\n"
	)

	sDef='DT04H6OF,DT04H6OX,DT04H6NY'
	psr.add_argument(
		"-u","--uarts", dest='sUarts', metavar="SERIAL,SERIAL,...", type=str, 
		default=sDef, help="The serial number of the UARTs to read for each "+\
		"radius.  This defaults to %s.  Note that the number of "%sDef+\
		"sensors read is based on the number of sensor distances provided in "+\
		"the --radius argument.\n"
	)

	psr.add_argument(
		'-m', '--message', dest="sMsg", metavar='"Short msg"', type=str, default=None,
		help="Add a one line message to be saved with the test data."
	)

	psr.add_argument(
		'-d', '--out-dir', dest='sOutDir', metavar='DIR', type=str,
		default='.', help='Output detailed test files to '+\
		'folder%sdirectory DIR instead of the current location.'%os.sep
	)

	psr.add_argument(
		'-s', '--summary', dest="sSummary", metavar="FILE", type=str, 
		default="ScreenResults.csv", help="A summary of the screening results "+\
		"are appended to this file.  May be given as an absolute path, parent "+\
		"directories will be created as needed."
	)

	# ... and positional parameters follow
	psr.add_argument("PART", 
		help="An identifier for the object to be measured.  Will be used as "+\
		"part of the output filenames."
	)

	# return psr.parse_args()

	opts = psr.parse_args()
	# Set user interup handlers in case user wants to quite early.
	signal.signal(signal.SIGINT, setQuit)
	signal.signal(signal.SIGTERM, setQuit)
	
	# Since SIGALRM isn't available on Windows, spawn a thread to countdown to
	# the end of the data collection period, check user supplied time
	if opts.sDuration < 1 or opts.sDuration > 60*60:
		perr('ERROR: Test sDuration must be between 1 second and 1 hour\n')
		return 7
	
	# Set at X samples per second per sensor, should be no more then
	# 10 samples per second so that slow python code can keep up
	if (opts.sRate < 1) or (opts.sRate >= 200):
		perr("ERROR: Requested sample rate %d is out of expected range 1 to 200 (Hz)."%opts.sRate)
		return 8

	# See how many sensors we're going to use
	lDist = [int(s.strip(),10) for s in opts.sRadii.split(',')]
	nSensors = len(lDist)
	if nSensors < 1:
		perr("ERROR: At least one measurement distance must be given via -r\n")
		return 9

	lSerial = [s.strip() for s in opts.sUarts.split(',')]
	if len(lSerial) < nSensors:
		perr("ERROR: %d UARTs are required for measurements at %d distances.\n"%(
			nSensors, nSensors
		))
		return 10

	rTime0 = time.time()  # Current unix time in floating point seconds	
	g_bSigInt = False    # Global interrupt flag

	# Check that our non-empty sensors can be distinguished from each other
	g_lCollectors = []
	for i in range(nSensors):
		lTest = []
		for j in range(nSensors): 
			if (j != i): lTest.append(lSerial[j])
		if lSerial[i] in lTest:
			perr("ERROR: UART serial number %s is not unique in %s!\n"%(lSerial[i], opts.sUarts))
			return 13

		try:
			g_lCollectors.append( tlvmr.VMR('%d'%i, lSerial[i], opts.sRate) )
		except OSError as e:
			perr("ERROR: %s\n"%e)
			perr('HINT:  Sensors can be ignored by requesting data at fewer distances.')
			perr('  Use -h for more info.\n')
			return 15

		g_lCollectors[-1].set_time0(rTime0)
		g_lCollectors[-1].set_dist(lDist[i])

	if len(g_lCollectors) == 0:
		perr('INFO:  No data collection ports specified, successfully did nothing.\n')
		return 0
	
	# Create a display output thread
	perr("MSG:   Use CTRL+C to quit early\n")
	g_display = common.Display("MSG:   Collecting ~%d seconds of data "%opts.sDuration)
	
	# create an alarm thread to stop taking data
	alarm = threading.Timer(opts.sDuration + (time.time() - rTime0), setDone)
	

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
	sFile = pjoin(opts.sOutDir, "%s.csv"%(common.safe_filename(opts.PART)+str(time.strftime('%Y_%m_%dT%H_%M_%S'))))
	sTitle = "Magnetic Screening Test, Raw Data"
	tlvmr.write_mag_vecs(
		sFile, g_lCollectors, sTitle, _test_properties(opts.PART, opts.sMsg)
	)

	# Plot time series and PSD of the raw data, as a cross check
	(dProps, lDatasets) = semcsv.read(sFile)
	plot.screen_plot_pdf(dProps, lDatasets, sFile.replace('.csv','.pdf'))
	
	# Open the roll-up info file (or create one if it doesn't exist)
	if os.sep not in opts.sSummary:
		opts.sSummary = pjoin(opts.sOutDir, opts.sSummary)
	
	summary.append(opts.sSummary, dProps, lDatasets)
	perr("INFO:  Summary appended to %s\n"%opts.sSummary)
	
	return 0  # An all-okay return value

# ############################################################################ #

	
# Run the main function if this is a top level script
if __name__ == "__main__":
	sys.exit(main())
