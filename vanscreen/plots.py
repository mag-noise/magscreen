"""Plot creation functions for magnetic screening"""

import scipy
import matplotlib

def psd_time_plot(lDs):
	"""Read a semcsv file containing 1-N Bx,By,Bz datasets and generat a
	panel of plots for the timeseries and PSD data.  Use's Welch's method.
	
	Args:
		lDs (list): A list of datasets as created from semcsv.read()  The
			datasets must contain the variables, Bx, By & Bz

	Return: (lDs, fig)
		lDs - The same list of datasets passed in, but each dataset that
			matched the selection criteria will contain the new variables:
			Bx_psd, By_psd, Bz_psd
		fig - A matplotlib fig object containing the plots of interest.
	"""
	

	# TODO: Start here after some sleep

	return None

	