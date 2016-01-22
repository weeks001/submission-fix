#!/usr/bin/env python
from __future__ import with_statement

"""
A collection of unit tests for the submission script.
"""
__author__ = "Marie Weeks"
__version__ = "1.0"

import unittest
import datetime
from contextlib import contextmanager
import SubmissionFix

try: 
	from pytz import timezone
	import pytz
	findTime = True
except ImportError:
	findTime = False

class TestSubfixMethods(unittest.TestCase):
	"""Unit tests for the submission fix script."""

	#readCSV
	def test_readCSVSubset(self):
		answer = ['SNAKE, SOLID', 'SNAKE, LIQUID', 'BOSS, BIG', 'OCELOT, REVOLVER', 
				  'SILVERBURGH, MERYL', 'HUNTER, NAOMI', 'CAMPBELL, ROY']
		self.assertEqual(SubmissionFix.TSquare().readCSV('testingcsv1.csv'), answer)

	def test_readCSVAll(self):
		answer = ['SNAKE, SOLID', 'SNAKE, LIQUID', 'SNAKE, SOLIDUS', 'BOSS, BIG', 
				  'FOX, GREY', 'OCELOT, REVOLVER', 'EMMERICH, HAL', 'HUNTER, NAOMI',
				  'SILVERBURGH, MERYL', 'WOLF, SNIPER', 'RAVEN, VULCAN', 'MANTIS, PSYCHO',
				  'OCTOPUS, DECOY', 'CAMPBELL, ROY', 'ANDERSON, DONALD', 'BAKER, KENNETH',
				  'MILLER, KAZUHIRA', 'LING, MEI', 'ROMANENKO, NASTASHA', 'SASAKI, JOHNNY']
		self.assertEqual(SubmissionFix.TSquare().readCSV('testingcsv2.csv'), answer)

	def test_readCSVOverlap(self):
		answer = ['SNAKE, SOLIDUS', 'SNAKE, SOLID']
		self.assertEqual(SubmissionFix.TSquare().readCSV('testingcsv3.csv'), answer)

	def test_readCSVOne(self):
		answer = ['FOX, GREY']
		self.assertEqual(SubmissionFix.TSquare().readCSV('testingcsv4.csv'), answer)

	#stripTime
	@unittest.skipIf(findTime is False, "pytz needed for this test")
	def test_stripTimeNormal(self):
		eastern = timezone('US/Eastern')
		answer = datetime.datetime(2005,02,28,17,15)  #should be 5 hours behind result?
		self.assertEqual(SubmissionFix.TSquare().stripTime('20050228221512345'), eastern.localize(answer))

	@unittest.skipIf(findTime is False, "pytz needed for this test")
	def test_stripTimeTimeZoneBehindDay(self):
		eastern = timezone('US/Eastern')
		answer = datetime.datetime(2005,02,27,22,30) 
		self.assertEqual(SubmissionFix.TSquare().stripTime('20050228033012345'), eastern.localize(answer))

if __name__ == '__main__' :
	suite = unittest.TestLoader().loadTestsFromTestCase(TestSubfixMethods)
	unittest.TextTestRunner(verbosity=2).run(suite)