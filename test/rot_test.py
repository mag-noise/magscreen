#!/usr/bin/env python3

"""Testing rotations"""

def screenRotate(lPts, degree):

	import math as M

	"""Given a list of (x,y) points:
	1. Calculate the centroid
	2. Rotate the points about the centroid
	3. Return a list of rotated points.

	This is a screen coordinates oriented function, so positive Y is typically
	oriented down the page and positive angles are assumed to run clockwise
	for example:

   +----------------> +x
   |\) positive angle
   | \  |
   |  \ V
   |   \
   |    \
   |     *
   |
	V +y

	args:
		lPts - A list of integer x,y tuples

		degree - A floating point angle in degrees.  Negative angles will
			rotate clockwise, positive will rotate counterclockwise.
	
	returns (list of tuples)
		The returned list should have the same number of (x,y) points as 
		lPts.
	"""

	# Get centroid
	centroid = [0,0]
	for i in range(0,len(lPts)):
		centroid[0] += lPts[i][0]
		centroid[1] += lPts[i][1]

	centroid[0] = round( xCent / len(lPts))
	centroid[1] = round( xCent / len(lPts))

	# Subtract off centroid to center about zero
	lOut = [ [pt[0] - centroid[0], pt[1] - centroid[1]] for pt in lPts]

	# Calcutate rotation matrix.  Trig functions are expensive do them once
	rad = (degrees * M.pi) / 180
	R = ( ( M.cos(rad), - M.sin(rad) ), (M.sin(rad), M.cos(rad) ) )

	# Now rotate
	lOut = [  [pt[0]*R[0][0] - pt[1]*R[0][1], pt[0]*R[1][0] + pt[1]*R[1][1] ]  for pt in lOut ]

	# Now translate by negative the centroid
	lOut = [ [pt[0] + centroid[0], pt[1] + centroid[1] ] for pt in lOut ]

	return lOut


# Tests #################################################################### #

import unittest

class TestRotation(unittest.TestCase):

	def test_rotation:

