#!/usr/bin/env python
from __future__ import with_statement

"""
A collection of integration tests for the submission script.
"""

__author__ = "Marie Weeks"
__version__ = "1.0"

import os
import sys
import shutil
import argparse
import unittest
from contextlib import contextmanager
import SubmissionFix

class TestSubfixIntegration(unittest.TestCase):
	"""Integration tests for the submission fix script."""

	@classmethod
	def setUpClass(cls):
		with open('tests_log.txt', 'w+') as f:
			f.write('SubmissonFix Test Log\n\n')

	def test_pathExistsNoFlags(self):
		answer = self.pathTestSetup('Homework 0')
		with self.tempTestDir(['', 'testing_set1.zip'], 'Integration - Homework 0, No flags', answer, 'testing_set1.zip') as result:
			self.assertTrue(result)

	def test_pathExistsMove(self):
		answer = self.pathTestSetup()
		with self.tempTestDir(['', 'testing_set1.zip', '-m'], 'Integration - Homework 0, -move', answer, 'testing_set1.zip') as result:
			self.assertTrue(result)

	def test_pathExistsPath(self):
		answer = self.pathTestSetup(os.path.join('NewFolder','Homework 0'))
		with self.tempTestDir(['', 'testing_set1.zip', '-pNewFolder'], 'Integration - Homework 0, -path', answer, 'testing_set1.zip') as result:
			self.assertTrue(result)

	def test_pathExistsPathMove(self):
		answer = self.pathTestSetup('NewFolder')
		with self.tempTestDir(['', 'testing_set1.zip', '-pNewFolder', '-m'], 'Integration - Homework 0, -path -move', answer, 'testing_set1.zip') as result:
			self.assertTrue(result)

	def test_pathExistsNoFlagsParens(self):
		answer = self.pathTestSetup('Homework 0 (Malloc)')
		with self.tempTestDir(['', 'testing_set2.zip'], 'Integration - Homework 0, No flags', answer, 'testing_set2.zip') as result:
			self.assertTrue(result)

	def test_pathExistsMoveParens(self):
		answer = self.pathTestSetup()
		with self.tempTestDir(['', 'testing_set2.zip', '-m'], 'Integration - Homework 0, -move', answer, 'testing_set2.zip') as result:
			self.assertTrue(result)

	def test_pathExistsPathParens(self):
		answer = self.pathTestSetup(os.path.join('NewFolder','Homework 0 (Malloc)'))
		with self.tempTestDir(['', 'testing_set2.zip', '-pNewFolder'], 'Integration - Homework 0, -path', answer, 'testing_set2.zip') as result:
			self.assertTrue(result)

	def test_pathExistsPathMoveParens(self):
		answer = self.pathTestSetup('NewFolder')
		with self.tempTestDir(['', 'testing_set2.zip', '-pNewFolder', '-m'], 'Integration - Homework 0, -path -move', answer, 'testing_set2.zip') as result:
			self.assertTrue(result)


	def pathTestSetup(self, root=''):
		basePath = os.path.join(os.getcwd(), 'test_folder')
		if root:
			basePath = os.path.join(basePath, root)
		testsetNames = [('Anderson, Donald', '20f5d6b21d3d2b3685f2144bc2fc771d'), ('Baker, Kenneth', 'd30f7f7f153271e28c4b632db9fa0b01'),
						 ('Boss, Big', '41b1318bf1cce2d9a40761b02bab065e'), ('Campbell, Roy', '39b73fb441b1c611f3a50be2b8693f03'),
						 ('Emmerich, Hal', 'c664acb099c59b2a4940773012d9ca40'), ('Fox, Grey', 'f8049726520d8dc911a7014af736e302'),
						 ('Hunter, Naomi', 'd860291b770a7dadd23af116c5334caa'), ('Ling, Mei', '29eb03d07be7696caba2f608ac7b8a71'),
						 ('Mantis, Psycho', '04a6c6c02d714a17cdd6aab5107008e4'), ('Miller, Kazuhira', 'f5cd92c317cec73b96ede092a62adcfe'), 
						 ('Ocelot, Revolver', 'ef95ea7fbb72b57b38bd5aa7efcf8ca3'), ('Octopus, Decoy', '53a36da95a92702adfa25cb1e221a0d2'),
						 ('Raven, Vulcan', '8d6da48c03e4e95fad55843d1ed84211'), ('Romanenko, Nastasha', '6569a8e2f02a2611a34106bd2d77f941'), 
						 ('Sasaki, Johnny', '757c592a306b9dcfeaa6e34ccb752b4a'), ('Silverburgh, Meryl', '205105fa7784a73c91e1412cfc886f65'),
						 ('Snake, Liquid', 'e60a34764ec988f9d4597fe7825cdd63'), ('Snake, Solid', '437e86082822caa972544f09da5f1050'),
						 ('Snake, Solidus', 'de2caa5dd90df87e03cfe62780a58c94'), ('Wolf, Sniper', '4f4002d30d729c89bb7fca07bf693c2c')]
		testset0Paths = ['Text', '_submissionText.html', 'timestamp.txt', 'patriots.asm']
		answer = []
		for n in testsetNames:
			base = os.path.join(basePath, '{name}').format(name=n[0])
			answer.append(os.path.join(base, '{test}').format(test=testset0Paths[0]))
			answer.append(os.path.join(base, '{test}', '{name}({nhash}){sub}').format(test=testset0Paths[0],name=n[0],nhash=n[1],sub=testset0Paths[1]))
			answer.append(os.path.join(base, '{test}', '{time}').format(test=testset0Paths[0],time=testset0Paths[2]))
			answer.append(os.path.join(base, '{asm}').format(asm=testset0Paths[3]))
		return answer


	@contextmanager
	def tempTestDir(self, args, test, answer, testset):
		with self.tempDirectory() as path:
			with self.integrationContentsTest(args, path, test, answer, testset) as result:
				yield result
			
	@contextmanager
	def tempDirectory(self):
		path = os.path.abspath('test_folder')
		if not os.path.exists(path):
			os.makedirs(path)
		yield path
		shutil.rmtree(path)

	@contextmanager
	def suppressOutput(self):
		with open(os.devnull, 'w') as devnull:
			oldstdout = sys.stdout
			sys.stdout = devnull
			yield
			sys.stdout = oldstdout

	@contextmanager
	def integrationContentsTest(self, args, path, test, answer, testset):
		shutil.copy(os.path.abspath(testset), path)
		base = os.getcwd()
		os.chdir(path)
		with self.suppressOutput():
			SubmissionFix.main(args)
		yield self.existingPathsTest(base, test, answer)
		os.chdir(base)

	def existingPathsTest(self, base, test, paths):
		self.logTest(base, test, ['[{exists}]  {path}\n'.format(exists=str(os.path.exists(p)), path=p) for p in paths])
		return all([os.path.exists(p) for p in paths])	

	def logTest(self, base, name, results):
		temp = os.getcwd()
		os.chdir(base)
		with open('tests_log.txt', 'a') as f:
			header = "==================================\n{testname}\n==================================\n"
			f.write(header.format(testname=name))
			for r in results:
				f.write(r)
			f.write('\n')
		os.chdir(temp)


if __name__ == '__main__' :
	suite = unittest.TestLoader().loadTestsFromTestCase(TestSubfixIntegration)
	unittest.TextTestRunner(verbosity=2).run(suite)