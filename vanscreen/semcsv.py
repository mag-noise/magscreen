"""Semantic CSV Parser

People like CSV files, they are human readable, and most data handling
environments can read them.  However for long term archiving we need a
format that handles both data and metadata.  This parser adds a small
semantic layer over top of the base CSV file format to address this 
issue.  If more structure is needed then what this format can provide
then some higher level format such as CDF is recommended.

History:
   C. Piker 2021-12-21: Original v0.1
"""

import csv

def read(sFile):
	"""Read a semantic CSV file and return a dictionary of global properties
	and datasets.
	"""

	dProps = {}
	lDs = []

	with open(sFile, 'r', newline='') as fIn:
		for row in csv.reader(fIn):

			# Already three level deep, haven't even written anything :(
			if len(row) < 1: continue

			if len(row[0].strip()) in ("","#","C"): continue


