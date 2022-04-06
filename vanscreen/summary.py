"""Handling mag screening summary data"""

import os
import sys
import argparse
from os.path import basename as bname
from os.path import dirname as dname

import vanscreen.common as common
import vanscreen.semcsv as semcsv
import vanscreen.calc as calc

perr = sys.stderr.write  # shorten a long function name

def _mkHeader(sAbsFile):
	if os.path.isfile(sAbsFile):
		raise IOError("Cowardly refusing to overwrite existing summary data")
	perr("INFO:  Creating file %s\n"%sAbsFile)
	fOut = open(sAbsFile, "w", newline='')
	fOut.write('"Part","Timestamp","Technician","Software","Dipole [N m T^-1]","Field @ 1 m [nT]","Result"\r\n')
	fOut.flush()
	fOut.close()


def append(sAbsFile, dProps, lDs):
	"""Append dataset summaries to a tracking file.

	Args:
	sAbsFile (str): The absolute path to the summary file.  The file is
		created if it does not exist.  Intermediate directories are 
		created as needed.

	dProps (dict): A dictionary of global properties for each test set.

	lDs (list of semcsv.Dataset): A list of all the datasets for a single
		test.
	"""

	sDir = dname(sAbsFile)
	if len(sDir) > 0: os.makedirs(sDir, exist_ok=True)

	if not os.path.isfile(sAbsFile):
		_mkHeader(sAbsFile)

	fOut = open(sAbsFile, "a", newline='') # Should auto seek(END)

	(dist, rate, Zangle, Xangle, Bdipole, moment, merror) = calc.dipole_from_rotation(lDs)
	(Bstray, BstrayErr, iStatus) = calc.stray_field_1m(moment, merror)

	fOut.write('"%s","%s","%s","%s",%.3e,%.3e,"%s"\r\n'%(
		dProps['Part'][0], dProps['Timestamp'][0], dProps['User'][0],
		dProps['Version'][0], moment, Bstray, calc.status_text[iStatus]
	))

	fOut.flush()
	fOut.close()

# ########################################################################## #
def main():
	psr = argparse.ArgumentParser(formatter_class=common.BreakFormatter)
	psr.description = '''\
	Read raw mag-screening data and append summary to a master result file
	'''

	psr.add_argument("TEST_DATA",help='A file containing magnetic screening test'+\
		' data in in Semantic CSV format')

	psr.add_argument("SUMMARY_FILE", help='A file to recive test summary information')

	opts = psr.parse_args()
	(dProps, lDatasets) = semcsv.read(opts.TEST_DATA)
	append(opts.SUMMARY_FILE, dProps, lDatasets)
	perr("INFO:  Summary appended to %s\n"%opts.SUMMARY_FILE)

	return 0

# Run the main function if this is a top level script
if __name__ == "__main__":
	sys.exit(main())
