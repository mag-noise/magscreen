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

# Here's an example data file (with interleaved data)
#
# C ,Semantic-CSV v0.1, ,         ,         ,  ,        ,        ,        ,
#   ,         ,         ,         ,         ,  ,        ,        ,        ,
# G ,Title    ,"Magnetic Screening Test, Raw Data",,,,  ,        ,        ,
# G ,Host     ,Puter    ,         ,         ,  ,        ,        ,        ,
# G ,Part     ,doggy    ,         ,         ,  ,        ,        ,        ,
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


def _new_ds(sFile, nLine, iBeg, iEnd)
	try:
		iBeg = int(iBeg,10)
	except:
		iBeg = _toCol(iBeg)

	try:
		iBeg = int(iEnd,10)
	except:
		iBeg = _toCol(iEnd)	

	return {'bounds':(iBeg,iEnd),'props':[],'vars':[],'var_col':[],'units':[]}


def _parse_prop(dProps, row):
	if (len(row) < 3) or (len(row[1] == 0)): return
	dProps[row[1]] = [item for item in row[2:] if item] # Drop empty columns


def _parse_ds_cols(ds,row):
		
	


def read(sFile):
	"""Read a semantic CSV file and return a dictionary of global properties
	and datasets.
	"""

	dProps = {}
	lDs = [] 

	with open(sFile, 'r', newline='') as fIn:
		rdr = csv.reader(fIn)
		for row in rdr:

			# Already three level deep, haven't even written anything :(
			if len(row) < 1: continue

			# CSV reader returns empty strings not None, ignore empty rows
			if len(row) == row.count(''): continue

			if len(row[0].strip()) in ("","#","C"): continue
			
			# There are two ways to start off a dataset:
			#   1. Just have a P, H or D row (single dataset only)
			#   2. Have an F column which is a format statement

			if row[0] == 'G':
				_parse_prop(dProps, row)
				continue

			elif row[0] == 'F':
				if len(row) < 3:
					raise ParseError(sFile, rdr.line_num, "Short column count")
				if row[1] != 'Interleave':
					raise ParseError(sFile, rdr.line_num, "Expected 'Interleave' in 2nd column")
				
				if len(lDs) > 0:
					raise ParseError(sFile, rdr.line_num, 
						"Interleaved format must be specified before 'P'roperty or "+\
						"'H'eader or 'D'ata rows."
					)
				
				i = 2
				while i < len(row)
					if len(row[i].strip()) == 0: break
					l = row[i].split('-')
					if len(l) != 2:
						raise ParseError(sFile, rdr.line_num, "Bad column spec '%s'",%row[i])
					iBeg = l[0]
					iEnd = l[1]
					lDs.append( _new_ds(iBeg, iEnd))
			
			elif (row[0] in ('P','H','D')) and (len(lDs) == 0): # PhD, totally not planned
				lDs.append( _new_ds(0,1024) )
			else:
				ParseError(sFile, rdr.line_num, "Unknown row type '%s'"%row[0])

			# pull out columns and feed to each dataset object
			for ds in lDs:
				lSub = row[ ds['bounds'][0]:ds['bounds'][1] ]
				
				_parse_ds_cols(ds,lSub)

	
	return (dProps, lDs)
