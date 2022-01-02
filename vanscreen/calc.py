"""Dataset calculations for Magnetic Cleanliness Screening"""

import numpy as np

from scipy import signal
from scipy.constants import pi
from scipy.constants import mu_0
from scipy.optimize import curve_fit
import scipy.stats as stats



def moment_to_mag(distance, moment):
	"""Given a distance from a point magnetic dipole source, determine the
	magnetic field strength at the point.

	Formerly called "func"

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
	return ((mu_0 * m) / (2*pi * distance**3))


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
	if len(var.data) < nSegLen: nSegLen = len(var.data)
	(aXf, aYf) = signal.welch(var.data, nperseg=nSegLen, scaling='spectrum')
	aYf = np.sqrt(aYf)

	return (aXf, aYf)


def dipole_moment(r_meters, mag_Tesla, angle):
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


def rms(vec):
	"""Get the root-mean squared valued of a 1-D vector"""

	return np.sqrt(  np.sum([n*n for n in vec])  )/len(vec)


def _angleZ(vec):
	"""Find angle between a 3-vector and the Z axis [0,0,1]
	Args:
		vec (array-like): A 3-vector, in the order X, Y, Z

	Returns:
		The angle between the vector and the Z axis in radians.
	"""
	if len(vec) != 3: raise ValueError("Expected a 3-vector")

	return np.arccos( np.dot(vec, np.array([0,0,1])) / rms(vec) )


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
			The adjusted field strength

	(Function called "ratio" in old sources )
	"""

	return reading * ( (reference + offset)**3 / reference**3 )


def stray_field(lDsRaw):
	"""
	Get the stray field at 1 meter from measurements made of a rotating object
	at various distances.

	Args:
		lDsRaw (list[semcsv.Dataset]): A list of raw datasets from three-axis
			magnetometers in the presence of a slowly rotating object.

			The datasets should have variables named: 
				Bx, By, Bz 
			which provide three-axis measurements in nanoTesla

			The datasets should have the following properties:

				Distance - distance from the center of the object to the front of
				   the magnetometer plastic packaging

				Offset_cm - Three component offsets from the external sensor
					casing to the center of each magnetometer, in centimeters.

			More datasets are better, but at a minimum of two are needed to
			project the object's effects out to a distance of one meter.

	Returns:
		(dist_m, Bmax_T, B_fit_T, B_err_T, Bstray_T, BstrayErr_T)
		dist_m - Array of sensor distances in meters
		Bmax_T - Array of maximum projection dipole values at each distance
		B_fit_T - The best-fit line point at each distance
		Bstray_T - The expected stray field value at 1 meter, in tesla
		BstrayErr_T - The error in the expected stray field value at 1 meter
	"""

	# 1. Since the object is rotating in the earths magnetic field, find out 
	#    how much it changes the field using by calculationg the magnetic 
	#    sepectral density.

	lDist   = []  # Distance to the center of the object in [m]
	lDipole = []  # Dipole in units of [N m T**-1]

	for dataset in lDsRaw:

		# Make sure all the component arrays are the same length
		if (len(dataset.vars['Bx']) != len(dataset.vars['By'])) or \
			(len(dataset.vars['Bx']) != len(dataset.vars['Bz'])) 
			raise ValueError("Field component arrays are not the same length")


		(freq_X, amp_X) = relative_spectrum(dataset.vars['Bx'].data)
		(freq_Y, amp_Y) = relative_spectrum(dataset.vars['By'].data)
		(freq_Z, amp_Z) = relative_spectrum(dataset.vars['Bz'].data)

		rDist = float(dataset.props['Distance'][0])
		if dataset.props['Distance'][1] == '[cm]':
			rDist_meters *= 0.01
		else:
			raise ValueError(
				"General unit handling not implemented, 'Distance' property is "=\
				"expected in units of centimeters [cm]."
			)

		# Normalize B components to front face of sensor, since we can measure
		# that in the real world with a ruler.
		lOffset_meters = [ float(sItem) for sItem in dProps['Offset_cm'] ]
		B_nT = [
			_dipole_adjust( amp_X.max(), lOffset_meters[0], rDist_meters )
			_dipole_adjust( amp_Y.max(), lOffset_meters[0], rDist_meters )
			_dipole_adjust( amp_Z.max(), lOffset_meters[0], rDist_meters )
		]

		lDist.append(rDist)

		# FIXME: This code appears incorrect.  It's a copy with reduction from
		# the fit() function.  The name has been changed from angle to angleZ
		# because the formal angle function did not look to be a general calculation

		lDipole.append( dipole_moment(rDist, rms(B_nT)*1e-9, _angleZ(B_nT)) )


	# FIXME: Just copying over code from mag_screen_gui.py at this point...

	dist_m = np.array(lDist)

	# axis is mangetic fields from strongest possible dipole orientation
	# (actually, I don't see how that is true.)

	Bmax_T = moment_to_mag(dist_m, abs(np.array(lDipole)))  # aka func()

	# Curve fitting best fit of the N magnetic fields measured
	B_fit_T, B_covariance = curve_fit(moment_to_mag, dist_m, Bmax_T)

	# estimated covariance of popt, aka one standard deviation errors on the
	# parameters
	B_err_T = np.sqrt(np.diag(B_covariance)) 

	# calculating stray field at 1 meter from strongest orientation best-fit
	# magnetic dipole moment
	#
	# Fixme: mu_0 times a moment givens units of mag field, what the heck does
	#        mu_0 times a field magnitude give?  Is there an error here?

	Bstray_T = (mu_0 * B_fit_T) / (2*pi*1**3) 
   
   #print("magnetic dipole moment m = %.16f" %popt, "+/- %.16f" %m_err) #printing best fit magnetic dipole moment
   #print("stray field B = %.4f nT" %(stray_B*1e9), "+/- %.4f" %(((mu_0 * m_err) / (4*pi))*1e9)) #printing stray magnetic field at 1 meter

   BstrayErr_T = ( (mu_0 * B_err_T) / (4*pi))

   return (dist_m, Bmax_T, B_fit, B_err_T, Bstray_T, BstrayErr_T)
