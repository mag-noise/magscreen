"""Semantic CSV Parser

People like CSV files.  Humans can read them and most data plotting
packages can too.  However, for long term archiving we need a format
that has some structure so that software doesn't have to be re-written
every time datasets change structure.

This parser adds a small semantic layer over top of the base CSV file
format to address this issue.  If more structure is needed then what's
provided here, then then some more complete file format such as CDF
should be used instead.

I've named this format "Semantic CSV", the whole concept has probably
been invented independently 4,000 times before.

History:
   C. Piker 2021-12-21: Original v0.1
"""

import csv
import re
import math
import numpy as np

# Here's an example data file with interleaved data.  It consists of
# 
#  1. Global Properties  -- Rows that start with G
#  2. Comments           -- Rows that start with C
#  3. A format statement -- Rows that start with F
#  4. Dataset Properties -- Sections that start with P
#  5. Dataset Headers    -- Sections that start with H
#  6. Data values        -- Sections that start with D
#
#  The format is essentially line oriented, but lines can have chunks
#  of columns that should be loaded as separate datasets.  Datasets
#  may be of different lengths.  This is just handled by adding empty
#  columns as needed to pad out each row.
# 
# ---------
#
# C ,Semantic-CSV v0.1, ,         ,         ,  ,        ,        ,        ,
#   ,         ,         ,         ,         ,  ,        ,        ,        ,
# G ,Title    ,"Magnetic Screening Test, Raw Data",,,,  ,        ,        ,
# G ,Host     ,Puter    ,         ,         ,  ,        ,        ,        ,
# G ,Part     ,mark 1 hammer,     ,         ,  ,        ,        ,        ,
# G ,Timestamp,2021-12-21T18:51:01,,        ,  ,        ,        ,        ,
# G ,User     ,Chris    ,         ,         ,  ,        ,        ,        ,
# G ,Software ,vanscreen-0.2,     ,         ,  ,        ,        ,        ,
#   ,         ,         ,         ,         ,  ,        ,        ,        ,
# F ,Interleave,A-E     ,F-J      ,K-O      ,  ,        ,        ,        , <--(Splits Rows)
#   ,         ,         ,         ,         ,  ,        ,        ,        ,
# P ,Dataset  ,0        ,         ,         ,P ,Dataset ,1       ,        ,
# P ,Sensor   ,VMR N179 ,         ,         ,P ,Sensor  ,VMR N201,        ,
# P ,UART     ,0x0403   ,0x6015   ,6NYA     ,P ,UART    ,0x0403  ,0x6015  ,6M0A
# P ,Port     ,COM3     ,         ,         ,P ,Port    ,COM4    ,        ,
# P ,Distance ,10       ,[cm]     ,         ,P ,Distance,10      ,[cm]    ,
# P ,Epoch    ,18:50:39 ,         ,         ,P ,Epoch   ,18:50:39,        ,
#   ,         ,         ,         ,         ,  ,        ,        ,        ,
# H ,Off [s]  ,Bx [nT]  ,By [nT]  ,Bz [nT]  ,H ,off [s] ,Bx [nT] ,By [nT] ,Bz [nT]
# D ,1.126    ,-10307.6 ,-44336.4 ,-10196.9 ,D ,1.173   ,9480.6  ,39780.3 ,-12333.7
# D ,1.226    , -9935.5 ,-44681.0 ,-10650.4 ,D ,1.173   ,9417.2  ,39781.7 ,-12336.2
# D ,1.319    , -9765.2 ,-45763.8 ,-11839.3 ,D ,1.269   ,9334.5  ,39788.1 ,-12286.6
# D ,1.434    ,-10970.2 ,-46289.1 ,-12399.3 ,D ,1.369   ,9210.5  ,39801.8 ,-12137.9
# D ,1.529    ,-11469.1 ,-45177.1 ,-11290.6 ,D ,1.480   ,8997.4  ,39832.6 ,-11762.3
# D ,1.620    ,-11223.7 ,-44549.4 ,-10555.7 ,D ,1.579   ,8719.2  ,39910.7 ,-10740.1
# D ,1.721    ,-11001.2 ,-44351.6 ,-10275.5 ,D ,1.670   ,9353.5  ,40006.2 , -8674.5
#
# ---------

import csv

class ParseError(Exception):
	def __init__(self, sFile, nLine, sMsg):
		super().__init__(sMsg)
		self.sFile = sFile
		self.nLine = nLine

	def __str__():
		"%s, line %d: %s"%(self.sFile, self.nLine, super().__str__())
	

def _toCol(sFile, nLine, sCol):
	p = [1,26,26*26]
	l = [0,0,0]

	sUp = sCol.upper()
	if (len(sUp) < 1) or (len(sUp)>3):
		 raise ParseError(sFile, nLine, "Bad column spec '%s'"%sUp)
	for c in sUp:
		if not c.isalpha():
			raise ParseError(sFile, nLine, "Bad column spec '%s'"%sUp)
		l.append(1 + ord(c)-ord('A'))
	
	iCol = (l[0]*p[0] + l[1]*p[1] + l[2]*p[2]) - 1

	return iCol


def _new_ds(sFile, nLine, iBeg, iEnd):
	try:
		iBeg = int(iBeg,10)
	except:
		iBeg = _toCol(iBeg)

	try:
		iBeg = int(iEnd,10)
	except:
		iBeg = _toCol(iEnd)	

	return {'_bounds':(iBeg,iEnd),'props':{},'vars':{},'_var_col':{}}


def _parse_prop(dProps, row):
	if (len(row) < 3) or (len(row[1] == 0)): return
	dProps[row[1]] = [item for item in row[2:] if item] # Drop empty columns

def _parse_ds_cols(sFile, nLine, ds,row):
	"""
	Reminder, datasets have this format:
	{
		'_bounds': (iBeg,iEnd),  # internal only, drop before return
		'props':{},
		'vars':[],
		'_var_col':[],           # internal only, drop before return
		'units':[]
	}

	Line times: P - property, H - Header (makes variable), D - Data
	"""
	
	if len(row) < 2: return
	if len(row) == row.count(''): return
	if row[0] == 'C': return
	
	
	if row[0] in ('G','F'):
		raise ParseError(sFile, nLine,"'G'lobal and 'F'ormat rows must proceed dataset rows")
				
	if row[0] not in ('P','H','D'):
		raise ParseError(sFile, nLine, "Unknown row type '%s'"%row[0])

	if row[0] == 'P':
		_parse_props(ds['props'], row)
	elif row[0] == 'H':
		# Define new variables and units
		for i in range(1,len(row)):
			if len(row[i]) == 0: continue
			
			ds['vars'] = {'name':'','units':'','data':[]}

			match = re.match(r"^(.*)\[(.*)\].*$",row[i])
			if match:
				sName  = match.group(1).strip()
				sUnits = match.group(2).strip()
			else:
				sName = row[i].strip()
				sUnits = ''
			
			ds['vars'][sName] = {'units':sUnits, 'data':[]}
			ds['_var_col'][i] = sName

	elif row[0] == 'D':
		for i in range(1,len(row)):
			if i not in ds['_var_col']:
				raise ParseError(sFile, nLine, 
					"No variable is associated with column %d. Are headers missing?"%(
						i+ds['_bounds'][0])
				)
			sVar = ds['_var_col'][i]
			ds['vars'][sVar]['data'].append(row[i].strip())  # Convert to numpy array at export


def _ds_finalize(dDs):
	"""Try to convert data values to floats and remove all column mappings"""

	for sVar in dDs['vars']:
		dVar = dDs[sVar]
		# Try to convert float (with nan for ""), if that fails leave variable data
		# as a string
		lStr = dVar['data']
		try:
			lFlt = [float(s) if len(s) > 0 else math.nan for f in l]
			dVar['data'] = np.array(lFlt, dtype=np.float)
		except ValueError:
			dVar['data'] = np.array(lStr)  # Leave as string data

	dDs.pop('_var_col')
	ds.pop('_bounds')
	
			
def reader(sFile):
	"""Read a semantic CSV file and return a dictionary of global properties
	and datasets.
	"""

	dProps = {}
	lDs = [] 

	with open(sFile, 'r', newline='') as fIn:
		rdr = csv.reader(fIn)
		for row in rdr:

			# Already three level deep, haven't even written anything :(
			if len(row) < 2: continue

			# CSV reader returns empty strings not None, ignore empty rows
			if len(row) == row.count(''): continue
			
			# There are two major braches to the parser, normal and interleaved

			# There are two ways to start off a dataset:
			#   1. Just have a P, H or D row (single dataset only)
			#   2. Have an F column which is a format statement
			
			if len(lDs) == 0:
				if row[0] == 'G':
					_parse_prop(dProps, row)
					continue

				elif row[0] == 'F':
					if len(row) < 3:
						raise ParseError(sFile, rdr.line_num, "Short column count")
					if row[1] != 'Interleave':
						raise ParseError(sFile, rdr.line_num, "Expected 'Interleave' in 2nd column")
					
					i = 2
					while i < len(row):
						if len(row[i].strip()) == 0: break
						l = row[i].split('-')
						if len(l) != 2:
							raise ParseError(sFile, rdr.line_num, "Bad column spec '%s'"%row[i])
						iBeg = l[0]
						iEnd = l[1]
						lDs.append( _new_ds(iBeg, iEnd))
			
				elif (row[0] in ('P','H','D')) and (len(lDs) == 0): # PhD, totally not planned
					lDs = [ _new_ds(0,1024)  ]
					_parse_ds_cols(lDs, row)

				elif row[0] == 'C':
					continue
				else:
					raise ParseError(sFile, rdr.line_num, "Unknown row type '%s'"%row[0])
			else:
				# pull out columns and feed to each dataset object
				for ds in lDs:
					lSub = row[ ds['_bounds'][0]:ds['_bounds'][1] ]		
					_parse_ds_cols(ds,lSub)

	for ds in lDs:
		_ds_finalize(ds)  # Convert to numpy, drop internal column tracking

	return (dProps, lDs)
