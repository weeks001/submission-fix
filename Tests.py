#!/usr/bin/env python
from __future__ import with_statement

"""
A collection of tests for the submission script.
"""

import os
import sys
import shutil
import argparse
from contextlib import contextmanager
import SubmissionFix

__author__ = "Marie Weeks"
__version__ = "1.0"


def main():

	#unit tests
	#  stripTime
	#  untar
	#  unzip
	#  extract
	#  move [after broken up]
	#  rename
	#  extractBulk
	#  readCSV
	#  require

	#integration tests
	#  due date: 02/28/15 23:55
	#  basic extraction
	#  extraction with move
	#  extraction with path
	#  extraction with move and path

	# (bulksubmission='testing_set.zip', csv=None, move=False, path=None, time=None)
	# testSet1 = 'testing_set.zip'

	print "Test 1"
	with tempTestDir(['', 'testing_set.zip']):
		print "base"
	print "Done."

	

@contextmanager
def tempTestDir(args):
	with tempDirectory() as path:
		with integrationContentsTest(args, path):
			yield 
	#could add something here
		
@contextmanager
def tempDirectory():
	path = os.path.abspath('test_folder')
	if not os.path.exists(path):
		os.makedirs(path)
	yield path
	shutil.rmtree(path)

@contextmanager
def integrationContentsTest(args, path):
	# print "Integration Test [Content]: " + args + " 	Expected: " + answer
	print "Integration test."
	shutil.copy(os.path.abspath('testing_set.zip'), path)
	os.chdir(path)
	SubmissionFix.main(args)
	print os.getcwd()
	yield
	#test for correct directory structure
	for root, folders, files in os.walk(path):
		print "Root: " + root
		print "Folders: " + ', '.join(folders)
		print "Files: " + ', '.join(files)
		print '\n'
	# raise ValueError('Stopping because I said so.')
	# 	if not any([a == folders.upper() for a in answer]) :
	# 		print "Test failed. Folder should not exist: " + folders
	# 		break
	# print "Test passed."


# def integrationPrintTest(args, answer):
# 	print "Integration Test [Print]: " + args + "		Expected: " + answer
# 	SubmissionFix.main(args)
# 	yield
# 	#test for correctly printed information






if __name__ == '__main__' :
	main()