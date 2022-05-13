"""Utilities for magnetic screening, mostly using Twinleaf sensors"""
#
# Copyright 2022 Chris Piker, Cole Dorman
#
# This file is part of magscreen
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import argparse
import threading
import sys
import string
import time

perr = sys.stderr.write  # shorten a long function names

# Fix dubious help text output ############################################# #

class BreakFormatter(argparse.HelpFormatter):
	"""Allow for manual line breaks in description and epilog blocks of help text.
	To insert a line break use the vertical tab (\\v) character into a text block."""
	def _fill_text(self, text, width, indent):
		import textwrap
		l = []
		for s in text.split('\v'):
			s = self._whitespace_matcher.sub(' ', s).strip()
			l.append(textwrap.fill(
				s, width, initial_indent=indent, subsequent_indent=indent
			))
		return '\n'.join(l)

	def _split_lines(self, text, width):
		# add empty line if help ends with \n
		lines = super()._split_lines(text, width)
		if text.endswith('\n'):
			lines += ['']
		return lines

# Human Amusement Device ################################################### #

class Display(threading.Thread):
	"""This is a simple aliveness printer.  It outputs a single . once a 
	second to stdout.  You could customize it to do more interesting things
	if desire.
	"""
	def __init__(self, prefix=""):
		threading.Thread.__init__(self)
		self.prefix = prefix
		self.go = False

	def stop(self):
		self.go = False
	
	def run(self):
		# Write dot's to screen so folks know the program isn't dead.  For a
		# fancier display see:
		# https://github.com/twinleaf/tio-python/blob/master/examples/tio-monitor.py
		# specifically the update() function.
		self.go = True
		num_dots = 0
		while self.go:
			if num_dots == 0: perr(self.prefix)
 
			time.sleep(1) # Sleep for 1 second           
			if num_dots % 10 == 9:
				perr('%d'%(num_dots+1))
			else:
				perr('.')
			sys.stderr.flush()
			num_dots += 1


def safe_filename(sName):
	"""Translate characters not suitable for a file names on Linux, Windows and Mac
	and not suitable for scripting.
	"""
	sSafe = string.ascii_letters + string.digits + '_-.,'
	lOut = []
	for c in sName:
		if c in sSafe: lOut.append(c)
		else: lOut.append('_')

	return "".join(lOut)

