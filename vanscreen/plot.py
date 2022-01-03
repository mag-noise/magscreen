"""Plot collected mag screen data"""

import argparse
import re
import sys
import datetime
import math
import os.path
from os.path import dirname as dname
import numpy as np
import scipy.stats as stats
from scipy.constants import pi

# Plot stuff
from matplotlib.figure import Figure

# Our stuff
from common import CustomFormatter
import semcsv
import calc

perr = sys.stderr.write  # shorten a long function name

# ############################################################################ #
# Raw Data plots #

def _markMaxAmp(oAxis, aX, aY, sPre, sColor, iRow):
	"""Helper for raw_plot8, mark the max amplitude values

	Try to be smart about axis angles, if the Y point is above my text then use
	an up angle, otherwise a down angle.  This is not a good general function,
	it assumes the max value is on the right side of the plot.  Okay for mag
	screening, not so good otherwise.
	"""
	j = np.argmax(aY)
	axis_to_data = oAxis.transAxes + oAxis.transData.inverted()
	data_to_axis = axis_to_data.inverted()
	lMaxPos = data_to_axis.transform((aX[j],aY[j]))
	rTextPos = 0.97 - 0.08*iRow
	if lMaxPos[1] > rTextPos: nAngleB = -60
	else: nAngleB = 60
	oAxis.annotate(
		"%s_max=%.1f"%(sPre, aY[j]), xy=(aX[j], aY[j]), ha='right', va='top', 
		xycoords='data', textcoords='axes fraction', xytext=(0.98, rTextPos),
		fontsize=8, arrowprops={
			"arrowstyle":"->","connectionstyle":"angle,angleA=0,angleB=%d"%nAngleB,
			"color":sColor
		}
	)


def raw_plot3(dProps, lDs, tFigSz=(7.5, 10)):
	"""Plot the raw data from up to three different mag screening datasets
	(one from each sensor)

	Args:
		lDs (list[semcsv.Dataset]) : A list of datasets to plot.  The first 
			three of theses will be included in the returned fig.

		dProps (dict): Global properties that apply to all givendatasets

		tFigSz (2-tuple): The width and heigh in inches for the plot area

	Returns: figure
		A matplotlib figure object, that contains up to 6 subplots.  Suitable
		for output as a pdf or png.  
	"""

	fig = Figure(figsize=tFigSz)

	# Set X & Y axis ranges the same for all plots in a column.
	llAx = fig.subplots(nrows=3, ncols=2, sharex='col', sharey='col')
	fig.subplots_adjust(wspace=0.4, hspace=0.4, left=0.17)

	fig.suptitle('Mag Screen Raw Data for:\n%s\non %s'%(
		dProps['Part'][0], dProps['Timestamp'][0]
	))

	if len(lDs) == 0:  # Should I just return none here?
		return fig

	iDs = 0
	iRow = 0
	lColor = ['blue','orange','green']
	lComp  = ['Bx',  'By',    'Bz']
	while (iDs < len(lDs)) and (iRow < 3):
		ds = lDs[iDs]

		float(ds.props['Distance'][0])  # Save distance
				
		sDistUnits = ds.props['Distance'][1]
		if sDistUnits != '[cm]': 
			raise ValueError("Expect [cm] for distance units, not '%s'"%sDistUnits)

		axTime = llAx[iRow, 0]
		axFreq = llAx[iRow, 1]
		axTime.grid(True)
		axFreq.grid(True)

		# Loop over components from a single sensor make time series and freq plot
		# Save the frequency data for later annotation.  We need to plot everything
		# first or the plot limits are not determined!
		lXf = [None]*3
		lYf = [None]*3
		for i in range(3):
			#perr("plot dist: %s, component: %s\n"%(self.lDist[iDs], lComp[i]))
			aX = ds.vars['Offset'].data
			aY = ds.vars[lComp[i]].data
			sUnit = ds.vars[lComp[i]].units
			sComp = lComp[i]
			axTime.plot(
				aX, aY, "-", label="%s [%s]"%(sComp, sUnit), color="tab:%s"%lColor[i]
			)
					
			(aXf, aYf) = calc.spectrum(float(ds.props['Rate'][0]), ds.vars[sComp])
					
			axFreq.plot(aXf, aYf, 
				"-", label="%s Spectra [%s]"%(sComp, sUnit), color="tab:%s"%lColor[i]
			)
			lXf[i] = aXf
			lYf[i] = aYf
				
		for i in range(3):
			_markMaxAmp(axFreq, lXf[i], lYf[i], lComp[i], lColor[i], i)

		# Denote the sensor on the right, more room there.
		lSensor = ds.props['Sensor'][0].split()
		bbox = axFreq.get_position()
		axFreq.text(bbox.xmax + 0.03, (bbox.ymin + bbox.ymax)/2,
			'VMR %s on UART %s'%(lSensor[3], ds.props['UART'][2]),
			horizontalalignment='center', verticalalignment='center',
			rotation='vertical', transform=fig.transFigure, fontsize=9
		)

		axTime.set_xlabel('Time Offset [s]')
		axTime.set_ylabel('Magnetic Intensity [nT]')

		sTitle = 'At %s %s'%(ds.props['Distance'][0],ds.props['Distance'][1])

		axTime.set_title(sTitle)
		axFreq.set_xlabel('Frequency [Hz]')
		axFreq.set_ylabel('Periodic Amplitude [%s]'%(ds.vars['Bx'].units))  # assume same units
		axFreq.set_title(sTitle)

		# Now for the ledgend
		
		iDs += 1  # Next distance please
		iRow += 1 # Plot it on next row

	return fig

# ############################################################################ #
# Stray field plot #

def dipole_plot(dProps, lDs, tFigSz=(7.5, 10)):
	"""Calculate and plot the expected stray field at 1-meter

	Args:
		dProps (dict): Global properties such as the data timestamp

		lDs (list[semcsv.dataset]): A list of datasets from 3-axis magnetometers
			set around the rotating object an various distances

		tFigSz (2-tuple): The (width, height) of the figure to generate in inches
	"""

	fig = Figure(figsize=tFigSz)
	axDipole = fig.add_axes((0.15, 0.5, 0.75, 0.4))

	(dist, rate, Zangle, Bdipole, moment, merror) = calc.dipole_from_rotation(lDs)

	# Using the fitted moment value, provide the field magnitude at 1 meter.
	Bstray_T    = calc.bmag_from_moment(1, moment)
	BstrayErr_T = 0.5 * calc.bmag_from_moment(1, merror)

	aFitDist = np.linspace(dist[0], dist[-1], num=30)
	aFitPts = calc.bmag_from_moment(aFitDist,moment)

	axDipole.plot(dist*100, Bdipole*1e9, 'bo',      label='Calculated Dipole')
	axDipole.plot(aFitDist*100, aFitPts*1e9, 'r-', label='Best Fit Dipole')
	axDipole.set_title(
		'Magnetic Screening Dipole Field\n%s\non %s'%(
		dProps['Part'][0], dProps['Timestamp'][0]
	))
	axDipole.grid(True)

	axDipole.set_xlabel('Sensor Distance [cm]')
	axDipole.set_ylabel('Axial Dipole Magnitude [nT]')

	(Bstray, BstrayErr, iStatus) = calc.stray_field_1m(moment, merror)

	axDipole.set_title(
		'Mag Screen for: %s\nResult: %s'%(dProps['Part'][0],calc.status_text[iStatus])
	)
	axDipole.legend()

	# Calculate a couple other items put them on the plot
	# FIXME: Values look suspicious
	#(chi_sq, p_val) = stats.chisquare(
	#	f_obs=Bdipole, f_exp=calc.bmag_from_moment(dist,moment)
	#)


	lNotes = [
		'Timstamp:            %s'%(dProps['Timestamp'][0]),
		#'chi-squared = %0.3f'%chi_sq, 'p-value = %0.3f'%p_val,
		'Dipole Moment:    %.2e ± %0.2e [N m T^-1]'%(moment, merror),
		'Stray Field @ 1m: %0.2e ± %0.2e [nT]'%(Bstray*1e9, BstrayErr*1e9)
	]

	bbox = axDipole.get_position()
	axDipole.text(bbox.xmin, bbox.ymin - 0.1, '\n'.join(lNotes),
		horizontalalignment='left', verticalalignment='center',
		transform=fig.transFigure, fontsize=10
	)

	axRate = fig.add_axes((0.15, 0.1, 0.3, 0.2))

	axRate.plot(dist*100, rate/2.0, 'o')
	axRate.set_title('1/2 Peak Field Variation Rate\n(Object Rotation Rate)', fontsize=8)
	axRate.set_ylabel('[Hz]', fontsize=8)
	axRate.set_xlabel('Sensor Distance [cm]', fontsize=8)
	axRate.grid(True)

	axAngle = fig.add_axes((0.6, 0.1, 0.3, 0.2), ylim=(0,180))

	axAngle.plot(dist*100, Zangle*180/pi, 'go')
	axAngle.set_title('Angle between dipole axis and Z axis', fontsize=8)
	axAngle.set_ylabel('[degrees]', fontsize=8)
	axAngle.set_xlabel('Sensor Distance [cm]', fontsize=8)
	axAngle.grid(True)

	return fig

# ############################################################################ #
# Plot figure generator #

class Plotter:
	"""Generate 1 - N plot pages from magnetic screening data.
	This is a generator object intended for use in a loop.  The first N pages
	are all the raw sensor plots.  The last one is always the fit.
	"""
	def __init__(self, dProps, lDs, figsize=None):
		self.dProps = dProps
		self.lDs = lDs
		self.iPage = 0
		if figsize:
			self.tFigSize = figsize
		else:
			self.tFigSize = (7.5, 10) # width, height in inches
		self.nPages = math.ceil( len(lDs) / 3)
		
		# If there's any raw data to plot, add a fit as the last plot
		if self.nPages > 0: self.nPages += 1

	def __iter__(self):
		self.iPage = 0
		return self

	def __next__(self):
		return self.next()

	def next(self):
		"""Get the next figure"""
		if self.iPage >= self.nPages:
			raise StopIteration()

		# Raw plot, or fit plot?
		if self.iPage < (self.nPages - 1):
			fig = raw_plot3(self.dProps, self.lDs[self.iPage*3 : self.iPage*3+3])
		else:
			fig = dipole_plot(self.dProps, self.lDs)
			
		self.iPage += 1
		return fig

# ########################################################################## #
# Plot file generators #

def _to_time(sISO):
	"""It took until python 3.7 to get ISO time string parsing... wow.  Since
	we have to be compatable with python 3.6 just hack something up for now.
	"""
	return datetime.datetime(int(sISO[:4]), int(sISO[5:7]), int(sISO[8:10]))

def screen_plot_png(dProps, lDs, sOutFile):
	
	import matplotlib.backends.backend_agg as backend

	sDir = dname(sOutFile)
	if not os.path.isdir(sDir):
		os.makedirs(sDir, 0o755, exist_ok=True)
	
	dMeta = {'Software': 'vanscreen 0.2'}
	if 'Title' in dProps: dMeta['Title'] = dProps['Title'][0]
	if 'User' in dProps: dMeta['Author'] = dProps['User'][0]
	if 'Note' in dProps: dMeta['Description'] = dProps['Note'][0]
	if 'Timestamp' in dProps: dMeta['Creation Time'] = _to_time(dProps['Timestamp'][0])
		
	for ds in lDs:
		lSource = []
		if 'Sensor' in ds.props:
			lSource.append(ds.props['Sensor'][0])
		dMeta['Source'] = ', '.join(lSource)

	i = 1
	for fig in Plotter(dProps, lDs):
		canvas = backend.FigureCanvas(fig)
		sFile = "%s.p%d.png"%(sOutFile[:-4], i)
		perr("INFO:  Writing %s\n"%sFile)
		canvas.print_png(sFile, metadata=dMeta)
		i += 1

def screen_plot_pdf(dProps, lDs, sOutFile):

	import matplotlib.backends.backend_pdf as backend

	sDir = dname(sOutFile)
	if not os.path.isdir(sDir):
		os.makedirs(sDir, 0o755, exist_ok=True)

	perr("INFO:  Writing %s\n"%sOutFile)
	with backend.PdfPages(sOutFile, keep_empty=False) as pdf:

		for fig in Plotter(dProps, lDs):
			pdf.savefig(fig)

		dPdf = pdf.infodict()
		#perr('Infodict: %s\n\n'%dProps)
		if 'Title' in dProps: dPdf['Title'] = dProps['Title'][0]
		if 'User' in dProps: dPdf['Author'] = dProps['User'][0]
		if 'Note' in dProps: dPdf['Subject'] = dProps['Note'][0]
		dPdf['Keywords'] = 'Magnetic Cleanliness Stray-Field dipole raw-data'
		if 'Timestamp' in dProps: 
			dPdf['CreationDate'] = _to_time(dProps['Timestamp'][0])
			dPdf['ModDate'] = datetime.datetime.today()


# ########################################################################## #
def main():

	psr = argparse.ArgumentParser(formatter_class=CustomFormatter)
	psr.description = '''\
	Read a single set of mag-screen data as generated by tlvmr.write_mag_vecs
	and generate raw data and projected stray field plots.
	'''
	psr.epilog = 'Authors: chris-piker@uiowa.edu, cole-dorman@uiowa.edu'

	psr.add_argument('-o','--out',dest='sOut',metavar='OUT_FILE',default=None,
		help='Set a specific output filename.  An absolute path may be given '+\
		'in which  case directories are created as needed.  By default the '+\
		'output filename is the same as the input file with the suffix '+\
		'changed to .pdf'
	)

	psr.add_argument('-f','--format',dest='sFmt',metavar='FORMAT',default=None,
		help='Instead of determining the output type by the output file extension '+\
		"explicitly set the format.  Understood values are 'png' and 'pdf', "+\
		"(without the quotes)."
	)

	psr.add_argument("sIn", metavar="CSV_FILE", help="The input filename. Should be a CSV file.")

	opts = psr.parse_args()

	if not opts.sIn.lower().endswith('.csv'):
		perr("ERROR: Expected a csv file for input")

	if not opts.sOut: 
		opts.sOut = re.sub(r'.csv', r'.pdf', opts.sIn, flags=re.IGNORECASE)

	(dProps, lDs) = semcsv.read(opts.sIn)

	perr('INFO:  Loaded %d global props, %d datasets, and %d variables from %s\n'%(
		len(dProps), len(lDs), sum( [len(ds.vars) for ds in lDs]), opts.sIn
	))
	
	sExt = opts.sOut.lower()[-4:]

	if opts.sFmt:
		sExt = '.'+opts.sFmt.lower()

	if sExt == '.pdf':
		screen_plot_pdf(dProps, lDs, opts.sOut)
	elif sExt == '.png':
		screen_plot_png(dProps, lDs, opts.sOut)
	else:
		perr("ERROR: Unknown output type '%s'\n"%sExt)

	return 0


# Run the main function if this is a top level script
if __name__ == "__main__":
	sys.exit(main())
