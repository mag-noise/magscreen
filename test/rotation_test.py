#!/usr/bin/env python3

import math

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


	Note: For more efficient operations numpy arrays could (and probably
	      should) be used instead, though for 4 points it's not going
	      to matter.
	"""

	if len(lPts) < 2: return lPts  # "Rotating" a single point

	# Get centroid
	centroid = [0,0]
	for i in range(0,len(lPts)):
		centroid[0] += lPts[i][0]
		centroid[1] += lPts[i][1]

	centroid[0] = round( centroid[0] / len(lPts))
	centroid[1] = round( centroid[1] / len(lPts))

	# Subtract off centroid to center about zero
	lOut = [ [pt[0] - centroid[0], pt[1] - centroid[1]] for pt in lPts]

	# Calcutate rotation matrix.  Trig functions are expensive do them once

	rad = (degree * M.pi) / 180

	R = ( ( M.cos(rad), - M.sin(rad) ), (M.sin(rad), M.cos(rad) ) )

	# Now rotate
	lOut = [ 
		[pt[0]*R[0][0] - pt[1]*R[0][1], pt[0]*R[1][0] + pt[1]*R[1][1] ]  
		for pt in lOut 
	]

	# Now translate by negative the centroid
	lOut = [ [pt[0] + centroid[0], pt[1] + centroid[1] ] for pt in lOut ]

	return lOut


# Tests #################################################################### #

import unittest

class TestRotation(unittest.TestCase):


	def check(self, lRot, lExpect):
		epsilon = 1e-10
		for i in range(len(lRot)):
			self.assertTrue(abs(lRot[i][0] - lExpect[i][0]) < epsilon)
			self.assertTrue(abs(lRot[i][1] - lExpect[i][1]) < epsilon)

	def test_rotation_45ccw(self):
		"""
		Test rotation 45 degrees counter clockwise
		"""
		a = 1/math.sqrt(2)

		lOrig   = [(-1, 0), (1,0)]
		lExpect = [(-a,-a), (a,a)]
		lRot = screenRotate(lOrig, 45)
		
		self.check(lRot, lExpect)

	def test_rotation_45cw(self):
		"""
		Test rotation 45 degrees clockwise
		"""
		a = 1/math.sqrt(2)

		lOrig   = [(-1,0), (1, 0)]
		lExpect = [(-a,a), (a,-a)]

		lRot = screenRotate(lOrig, -45)
		
		self.check(lRot, lExpect)
		
	def test_rotation_45ccw_oc(self):
		"""Test rotation 45 count-clockwise, off center"""
		a = 1/math.sqrt(2)

		lOrig =    [(-1+1, 0+1), (1+1,0+1) ]
		lExpect =  [(-a+1,-a+1), (a+1,a+1) ]
		lRot  = screenRotate(lOrig, 45)

		self.check(lRot, lExpect)


if __name__ == '__main__':
	unittest.main()

