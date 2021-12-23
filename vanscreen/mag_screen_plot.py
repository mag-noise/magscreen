"""Plot collected mag screen data"""

import argparse
import re
import sys

# Math stuff
import numpy as np
from scipy.constants import pi
from scipy.constants import mu_0
from scipy.optimize import curve_fit
import scipy.stats as stats

from common import CustomFormatter
import semcsv

perr = sys.stderr.write  # shorten a long function name

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

# ########################################################################## #
def plot_mag_psd(dProps, lDs):
	pass



# ########################################################################## #
def main():

	psr = argparse.ArgumentParser(formatter_class=CustomFormatter)
	psr.description = '''\
	Read a single set of mag-screen data as generated by tlvmr.write_mag_vecs
	and generate raw data and projected stray field plots.
	'''
	psr.epilog = 'Authors: chris-piker@uiowa.edu, cole-dorman@uiowa.edu'

	psr.add_argument('-o','--out',dest='sOut',metavar='PDF_FILE',default=None,
		help='Set a specific output filename.  An absolute path may be given '+\
		'in which  case directories are created as needed.  By default the '+\
		'output filename is the same as the input file with the suffix '+\
		'changed to .pdf.'
	)

	psr.add_argument("sIn", metavar="CSV_FILE", help="The input filename. Should be a CSV file.")

	opts = psr.parse_args()

	if not opts.sIn.lower().endswith('.csv'):
		perr("ERROR: Expected a csv file for input")

	if not opts.sOut: 
		opts.sOut = re.sub(r'\.csv', r'\.pdf', opts.sIn, flags=re.IGNORECASE)

	(dProps, lDs) = semcsv.read(opts.sIn)

	perr('INFO:  Loaded %d global props, %d datasets, and %d variables from %s\n'%(
		len(dProps), len(lDs), sum( [len(ds['vars']) for ds in lDs]), opts.sIn
	))

	fig = plot_mag_psd(dProps, lDs)

	return 0


# Run the main function if this is a top level script
if __name__ == "__main__":
	sys.exit(main())
