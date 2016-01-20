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
		self.assertEqual(SubmissionFix.readCSV('testingcsv1.csv'), answer)

	def test_readCSVAll(self):
		answer = ['SNAKE, SOLID', 'SNAKE, LIQUID', 'SNAKE, SOLIDUS', 'BOSS, BIG', 
				  'FOX, GREY', 'OCELOT, REVOLVER', 'EMMERICH, HAL', 'HUNTER, NAOMI',
				  'SILVERBURGH, MERYL', 'WOLF, SNIPER', 'RAVEN, VULCAN', 'MANTIS, PSYCHO',
				  'OCTOPUS, DECOY', 'CAMPBELL, ROY', 'ANDERSON, DONALD', 'BAKER, KENNETH',
				  'MILLER, KAZUHIRA', 'LING, MEI', 'ROMANENKO, NASTASHA', 'SASAKI, JOHNNY']
		self.assertEqual(SubmissionFix.readCSV('testingcsv2.csv'), answer)

	def test_readCSVOverlap(self):
		answer = ['SNAKE, SOLIDUS', 'SNAKE, SOLID']
		self.assertEqual(SubmissionFix.readCSV('testingcsv3.csv'), answer)

	def test_readCSVOne(self):
		answer = ['FOX, GREY']
		self.assertEqual(SubmissionFix.readCSV('testingcsv4.csv'), answer)

	#stripTime
	@unittest.skipIf(findTime is False, "pytz needed for this test")
	def test_stripTimeNormal(self):
		eastern = timezone('US/Eastern')
		answer = datetime.datetime(2005,02,28,17,15)  #should be 5 hours behind result?
		self.assertEqual(SubmissionFix.stripTime('20050228221512345'), eastern.localize(answer))

	@unittest.skipIf(findTime is False, "pytz needed for this test")
	def test_stripTimeTimeZoneBehindDay(self):
		eastern = timezone('US/Eastern')
		answer = datetime.datetime(2005,02,27,22,30) 
		self.assertEqual(SubmissionFix.stripTime('20050228033012345'), eastern.localize(answer))

	#helper functions
	@contextmanager
	def suppressOutput(self):
		with open(os.devnull, 'w') as devnull:
			oldstdout = sys.stdout
			sys.stdout = devnull
			yield
			sys.stdout = oldstdout

	@contextmanager
	def tempTestDir(self, args, test, answer):
		with self.tempDirectory() as path:
			with self.integrationContentsTest(args, path, test, answer) as result:
				yield result
			
	@contextmanager
	def tempDirectory(self):
		path = os.path.abspath('test_folder')
		if not os.path.exists(path):
			os.makedirs(path)
		yield path
		shutil.rmtree(path)

	@contextmanager
	def integrationContentsTest(self, args, path, test, answer):
		shutil.copy(os.path.abspath('testing_set.zip'), path)
		base = os.getcwd()
		os.chdir(path)
		with self.suppressOutput():
			SubmissionFix.main(args)
		yield self.existingPathsTest(base, test, answer)
		os.chdir(base)

	def existingPathsTest(self, base, test, paths):
		self.logTest(base, test, ['[{exists}]  {path}\n'.format(exists=str(os.path.exists(p)), path=p) for p in paths])
		return all([os.path.exists(p) for p in paths])	


if __name__ == '__main__' :
	suite = unittest.TestLoader().loadTestsFromTestCase(TestSubfixMethods)
	unittest.TextTestRunner(verbosity=2).run(suite)