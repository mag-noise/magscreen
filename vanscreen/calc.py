"""Dataset calculations for Magnetic Cleanliness Screening"""

import sys
import numpy as np

from scipy import signal
from scipy.constants import pi
from scipy.constants import mu_0
from scipy.optimize import curve_fit
import scipy.stats as stats


perr = sys.stderr.write  # shorten a long function name

def relative_spectrum(ary):
	"""Get the spectrum of a signal, ignoring the sampling period.
	
	Side Note: Though we don't return real frequency values we probably
	  should because then we could double check that the maximum component
	  changes at twice the rotation rate, which should be true for a dipole
	  field.

	Args:
		ary (array[float]): A 1-D array over values collected at a constant rate.

	Returns: (frequencies, amplitudes)
		frequencies - An array of values containing frequency components as if
			the sampling period was 1 Hz.

		amplitues - An array of values containing the square root of the power
	"""
	nSegLen = 256
	if len(ary) < nSegLen: nSegLen = len(ary)
	(aXf, aYf) = signal.welch(ary, nperseg=nSegLen, scaling='spectrum')
	aYf = np.sqrt(aYf)

	return (aXf, aYf)


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

	return reading * ( (reference + offset)**3 / reference**3 )


def bmag_from_moment(distance, moment):
	"""Given a distance from a point magnetic dipole source, determine the
	magnetic field strength at the point.

	This is the fitting funcion, the curve_fit routine below will search
	the parameter space and find the value of moment that provides Bmag
	values closest to the data.

	Args:
		distance (float): The distance from the dipole source center in [m].
			Fixme: is this distance assumed in a plane perpendicular to the
			dipole moment vector?

		moment (float): The moment in [N m T**-1] 

	Returns:
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
		(aDist, aBmax, rMoment, aBerr, Bstray, BstrayErr)

		aDist [m]:           Original sensor distance poisitions
		aRate [Hz]:          The measured rotation rate of the object at each distance
		aBmax [T]:           The dipole component only field values at each distance
		rMoment [N m T**-1]: The calculated dipole moment
		rMomErr [N n T**-1]: The estimated error in the dipole moment calculation

	Note: If the measured rotation rate is far from the know value then 
		   the assumptions built into this calculation may not be correct.
	"""

	# 1. Since the object is rotating in the earths magnetic field, find out 
	#    how much it changes the field using by calculationg the magnetic 
	#    sepectral density.

	lDist   = []  # Distance to the center of the object in [m]
	lDipole = []  # Dipole in units of [N m T**-1]

	for dataset in lDsRaw:

		# Make sure all the component arrays are the same length
		if (len(dataset.vars['Bx']) != len(dataset.vars['By'])) or \
			(len(dataset.vars['Bx']) != len(dataset.vars['Bz'])) or \
			(len(dataset.vars['Offset']) != len(dataset.vars['Bx'])): 
			raise ValueError("Component arrays are not the same length")


		(freq_X, amp_X) = relative_spectrum(dataset.vars['Bx'].data)
		(freq_Y, amp_Y) = relative_spectrum(dataset.vars['By'].data)
		(freq_Z, amp_Z) = relative_spectrum(dataset.vars['Bz'].data)

		# Get the sampling frequency
		rSampFreq = _getFreqHz(dataset.vars['Offset'].data, dataset.vars['Offset'].units)

		rDist_m = float(dataset.props['Distance'][0]) * 0.01
		if dataset.props['Distance'][1] != '[cm]':
			raise ValueError(
				"General unit handling not implemented, 'Distance' property is " +\
				"expected in units of centimeters [cm]."
			)

		# Normalize B components to front face of sensor, since we can measure
		# that in the real world with a ruler.
		lOffset_m = [ float(sItem) for sItem in dataset.props['Offset_cm'] ]
		B_nT = [
			_dipole_adjust( amp_X.max(), lOffset_m[0], rDist_m ),
			_dipole_adjust( amp_Y.max(), lOffset_m[0], rDist_m ),
			_dipole_adjust( amp_Z.max(), lOffset_m[0], rDist_m )
		]

		lDist.append(rDist_m)

		# FIXME: I've renamed the original funcion angle() to _angleZ() since
		#    that's what angle() seemed to calculate.  I think it's supposed
		#    to calculate angle of the maximum field value, but with respect 
		#    to what?  Each sensor is rotated about it's Z axis compared to the
		#    others, so maybe the Z angle is actually what's desired here.
		#    Not sure.  -cwp
		
		#perr('B_nT = %s\nmag(B_nT) = %s\nZ angle = %s\n'%((B_nT, _mag(B_nT), _angleZ(B_nT))))
		m = moment_from_bvec(rDist_m, _mag(B_nT)*1e-9, _angleZ(B_nT))
		lDipole.append(m)

	aDist_m = np.array(lDist)

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

	return (aDist_m, aBmax_T, aRot_Hz, rMomentFit, rMomentErr)

