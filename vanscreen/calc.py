"""Dataset calculations for Magnetic Cleanliness Screening"""

import sys
import numpy as np

from scipy import signal
from scipy.constants import pi
from scipy.constants import mu_0
from scipy.optimize import curve_fit

import vanscreen.semcsv as semcsv

perr = sys.stderr.write  # shorten a long function name

def spectrum(vTime, vData):
	"""Get the spectrum of a signal, ignoring the sampling period.
	
	Side Note: Though we don't return real frequency values we probably
	  should because then we could double check that the maximum component
	  changes at twice the rotation rate, which should be true for a dipole
	  field.

	Args:
	vTime (float, indexable, or semcsv.Variable)
		Either a real number representing the sampling frequency, or a 
		Variable object with the sample times

	vData (ndarray, indexable, or semcsv.Variable)
		The time series data from which the PSD should be derived.

	Returns: (frequencies, amplitudes)
		frequencies - An array of values containing frequency components as if
			the sampling period was 1 Hz.

		amplitudes - An array of values containing the square root of the power
	"""
	if isinstance(vTime, (float, int)):
		rFreq = vTime
	else:
		if isinstance(vTime, semcsv.Variable):
			if vTime.units != 's':
				raise ValueError("Unit conversion from %s to seconds is not implemented."%vTime.units)
			vTime = vTime.data		
		
		# Assume it's a iterable of some sort
		N = len(vTime)
		rPeriod = (vTime[-1] - vTime[0]) / (N - 1)

		# Check for missing points, individual samples must be within 0.25
		# average sampling periods
		rHi = rPeriod * 1.25
		rLo = rPeriod * 0.75
		for i in range(len(vTime)-1):
			rDiff = (vTime[i+1] - vTime[i])
			if (rDiff < 0) or (rLo >= rDiff) or (rDiff >= rHi):
				raise ValueError(
					"Sampling period for point %d is %.2e, expected %.2e to %.2e"%(
					i+1, rDiff, rLo, rHi
				))

		rFreq = 1/rPeriod

	if isinstance(vData, semcsv.Variable):
		vData = vData.data
		
	nSegLen = 256
	if len(vData) < nSegLen: nSegLen = len(vData)
	(aXf, aYf) = signal.welch(vData, rFreq, window='blackman', nperseg=nSegLen, scaling='spectrum')
	aYf = np.sqrt(aYf)

	return (aXf, aYf)

# ########################################################################## #

def moment_from_bvec(r_meters, mag_Tesla, angle):
	"""Determine the magnetic dipole moment of an object give a measurement of
	the surrounding field at a single point.
	
	Args:
		r_meters (float):
			The distance from measurement point to the center of the object in 
			meters.  This center of the object is assumed to be the center of
			the dipole field.

		mag_Tesla (float):
			The B-field magnitude measured at a distance r from the center
			object generating the field.

		angle (float):
			The angle between ????? in radians

			FIXME: Figure out what this angle is measured between, it looks to
			       be the Z-axis of the sensor, but there is no physical
			       reason the Z axis should matter more than any other.

	Returns:
		The magnetic dipole moment in [N m T**−1]
	"""
	return (
		( 4 * pi * r_meters**3 * mag_Tesla ) / 
		( mu_0*(2*np.cos(angle)**2 - np.sin(angle)**2) )
	)


def _rms(vec):
	"""Get the root-mean squared valued of a vector"""
	return np.sqrt(  np.sum([n*n for n in vec]) /len(vec) )

def _mag(vec):
	"""Return the magnitude of a vector"""
	return np.sqrt( np.sum( [n*n for n in vec]))


def _angleZ(vec):
	"""Find angle between a 3-vector and the Z axis [0,0,1]
	Args:
		vec (array-like): A 3-vector, in the order X, Y, Z

	Returns:
		The angle between the vector and the Z axis in radians.

	(Function named "angle" in old sources)
	"""
	if len(vec) != 3: raise ValueError("Expected a 3-vector")

	return np.arccos( np.dot(vec, np.array([0,0,1])) / _mag(vec) )


def _dipole_adjust(reading, reference, offset):
	"""Adjust field readings as if they were dipole field measurements collected
	at reference point.

      Sensor Package               Dipole Field Source         
	________________                       _   _
	         |     |                      / \ / \
	         |<Off>|<------ reference ------>+| |
	_________|_____|                      \_/ \_/

            ^
            |
            +-- Magnetometer/Voltmeter
	Args:
		reading (float): A dipole field reading, or close enough to a dipole 
		   field that it's good enough for government work.

		reference (float): The distance from the center of the generated
			field to the reference point on the sensor, which is typically
			the front plastic face.

		offset (float): The internal distance from the sensor reference
			point to the center actual internal magnetometer.

	Returns (float):
		The adjusted field strength which is greater then the original
		if the offset is positive, and less than the original if it's 
		negative

	(Function called "ratio" in old sources )
	"""
	adj = reading * ( (reference + offset)**3 / reference**3 )
	
	#perr("Input Reading %s, ref %s, offset %s, output reading %s\n"%(
	#		reading, reference, offset, adj)
	#)
	return adj


def bmag_from_moment(distance, moment):
	"""Given a distance from a point magnetic dipole source, determine the
	magnetic field strength at the point.

	This is the fitting funcion, the curve_fit routine below will search
	the parameter space and find the value of moment that provides Bmag
	values closest to the data.

	Args:
		distance (array): The distance from the dipole source center in [m].
			Fixme: is this distance assumed in a plane perpendicular to the
			dipole moment vector?

		moment (array): The moment in [N m T**-1] 

	Returns (array):
		The field magnitude at the given distance in units of Tesla

	Fixme: How is an angle not involved here?  Does this assume a moment in 
	       the Z axis and the distance is in the x-y plane?
	"""
	return ((mu_0 * moment) / (2*pi * distance**3))


def dipole_from_rotation(lDsRaw):
	"""Calculate the dipole moment of an object slowly spinning in a magnetic
	field.

	This function makes the assumption that some object is in periodic motion
	within an existing magnetic field.  It also assumes that the biggest source
	of magnetic field variation is due to the dipole field of the object in
	motion.

	Args:
	lDsRaw (list[semcsv.Dataset]): A list of raw datasets from three-axis
		magnetometers in the presence of a slowly rotating object.

		The datasets should have variables named: 
			Offset, Bx, By, Bz
		which provide three-axis measurements in nanoTesla and relative 
		times for each measurment

		The datasets should have the following properties:

		Distance - distance from the center of the object to the front of the
		           magnetometer plastic packaging

		Offset_cm - Three component offsets from the external sensor
		            casing to the center of each magnetometer, in centimeters.

		More datasets are preferred, but a least two are required.

	Returns:
		(dist, rate, Zangle, Bdipole, moment, merror)

		dist [m]:     Array of sensor distances from center of object
		rate [Hz]:    Array of rotation rates at each sensor (should be constant)
		Zangle [rad]: Array of angles from dipole axis to zaxis at each distance
		Bdipole [T]:  Array of dipole component field values at each distance

		moment [N m T**-1]: The calculated dipole moment (scalar)
		merror [N n T**-1]: The estimated error in the dipole moment calculation (scalar)

	Note: If the measured rotation rate is far from the know value then 
		   the assumptions built into this calculation may not be correct.
	"""

	iX = 0
	iY = 1
	iZ = 2
	tComp = ('Bx','By','Bz')

	# 1. Since the object is rotating in the earths magnetic field, find out 
	#    how much it changes the field using by calculationg the magnetic 
	#    sepectral density.

	lDist   = []  # Distance to the center of the object in [m]
	lRate = []
	lZangle = []
	lDipole = []  # Dipole in units of [N m T**-1]

	for dataset in lDsRaw:

		# Make sure all the component arrays are the same length
		if (len(dataset.vars['Bx']) != len(dataset.vars['By'])) or \
			(len(dataset.vars['Bx']) != len(dataset.vars['Bz'])) or \
			(len(dataset.vars['Offset']) != len(dataset.vars['Bx'])): 
			raise ValueError("Component arrays are not the same length")

		lFreq = [None]*3
		lAmp = [None]*3

		for i in range(3):
			(lFreq[i], lAmp[i]) = spectrum(
				float(dataset.props['Rate'][0]), dataset.vars[tComp[i]]
			)

		lMax = [ np.argmax(amp) for amp in lAmp ]
		#perr("INFO:  %s, max freq %s\n"%(dataset.props['UART'][2], lMax))

		# Check to see than all maximums fall on the same (or adjacent) freq. bin
		_temp = ('x','y','z')
		for i in range(1,3):
			freq_0 = lFreq[iX][lMax[iX]]
			if abs(lMax[i] - lMax[iX]) > 1:
				
				freq_N = lFreq[i][lMax[i]]

				perr("WARN:  For %s Bx_max @ %0.3f Hz but B%s_max @ %0.3f Hz. %s\n"%(
					dataset.props['UART'][2], freq_0, _temp[i], freq_N, 
					"Was the sensor in the near field?"
				))

		lRate.append( (lFreq[0][lMax[0]] + lFreq[1][lMax[1]] + lFreq[2][lMax[2]])/3.0 )
		
		rDist_m = float(dataset.props['Distance'][0]) * 0.01
		if dataset.props['Distance'][1] != '[cm]':
			raise ValueError(
				"General unit handling not implemented, 'Distance' property is " +\
				"expected in units of centimeters [cm]."
			)

		# Normalize B components to front face of sensor, since we can measure
		# that in the real world with a ruler.
		lOffset_m = [ float(sItem)*0.01 for sItem in dataset.props['Offset_cm'] ]
		
		Bmax_nT = [ _dipole_adjust( lAmp[i][lMax[i]], rDist_m, lOffset_m[i]) for i in range(3) ]

		lDist.append(rDist_m)
		lZangle.append(_angleZ(Bmax_nT))

		# FIXME: I've renamed the original funcion angle() to _angleZ() since
		#    that's what angle() seemed to calculate.  I think it's supposed
		#    to calculate angle of the maximum field value, but with respect 
		#    to what?  Each sensor is rotated about it's Z axis compared to the
		#    others, so maybe the Z angle is actually what's desired here.
		#    Not sure.  -cwp
		m = moment_from_bvec(rDist_m, _mag(Bmax_nT)*1e-9, lZangle[-1])

		lDipole.append(m)

	aDist_m = np.array(lDist)
	aAngle_rad = np.array(lZangle)
	aRot_Hz = np.array(lRate)

	# axis is mangetic fields from strongest possible dipole orientation
	# (actually, I don't see how that is true, angle calculation seems off)
	aBmax_T = bmag_from_moment(aDist_m, abs(np.array(lDipole)))  # aka func()

	# SciPy curve fitting magic explained:
	#
	#  The scipy curve_fit function uses introspection to see how many parameters
	#  the model function, in this case "bmag_from_moment", requires.  It then
	#  searches for the values of the function arguments that best reproduces 
	#  the data aBmax_T.  In this way it determines what magnetic moment would
	#  be needed to best produce the given values.
	#
	rMomentFit, mCovariance = curve_fit(bmag_from_moment, aDist_m, aBmax_T)

	# estimated covariance of the moment fit, aka one standard deviation.
	rMomentErr = np.sqrt(np.diag(mCovariance)) 

	return (aDist_m, aRot_Hz, aAngle_rad, aBmax_T, rMomentFit, rMomentErr)

# ########################################################################## #
# Stray Field #

status_text = ["FAILED", "PASSED", "CAUTION"]

FAIL    = 0
CAUTION = 1
PASS    = 2

def stray_field_1m(rMoment, rError):
	"""Given a dipole moment and error, determine the stray field at 1 meter

	Args:
		rMoment (float): The dipole moment of a part
		rError  (float): The uncertianty in the dipole moment
	Returns (stray_magnitude, stray_error, status):
		stray_magnitude: The stray field at 1 meter in [nT] 
		stray_error:     The uncertianty in the stray field at 1 meter in [nT]
		status:          A value of calc.PASS, calc.FAIL, or calc.CAUTION
	"""
	Bstray = bmag_from_moment(1.0,rMoment) # Field @ 1 meter 
	BstrayErr = bmag_from_moment(1.0, rError) # Err @ 1 meter
	if (Bstray + BstrayErr) > 0.05:
		nStatus = 'FAIL'
	elif (Bstray + BstrayErr) < (0.95 * 0.05):
		nStatus = 'PASS'
	else:
		nStatus = 'CAUTION'

	return (Bstray*1e9, BstrayErr*1.9, nStatus)
