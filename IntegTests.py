#!/usr/bin/env python
from __future__ import with_statement

"""
A collection of integration tests for the submission script.
"""

__author__ = "Marie Weeks"

import os
import sys
import shutil
import argparse
import unittest
from contextlib import contextmanager
from subprocess import Popen, PIPE
import SubmissionFix


def openLog():
	with open('tests_log.txt', 'w+') as f:
		f.write('SubmissonFix Test Log\n\n')


class TestIntegration(unittest.TestCase):
	"""Integration tests for the submission fix script."""

	@contextmanager
	def tempTestDir(self, args, test, answer, testset, roll=None):
		with self.tempDirectory() as path:
			self.assertTrue(self.integrationContentsTest(args, path, test, answer, testset, roll))

	@contextmanager
	def loadedTempTestDir(self, args, test, answer, testset, junkpath, files, roll=None, choice=None):
		with self.tempDirectory(junkpath, files) as path:
			if choice:
				self.assertTrue(self.integrationOverwriteTest(args, path, test, answer, testset, choice))
			else:
				self.assertTrue(self.integrationContentsTest(args, path, test, answer, testset, roll))

	@contextmanager
	def lateTempTestDir(self, args, test, testset, lateStudents):
		with self.tempDirectory() as path:
			self.assertTrue(self.integrationLateTest(args, path, test, testset, lateStudents))
			
	@contextmanager
	def exitTempTestDir(self, args, test, answer, testset, roll=None):
		with self.tempDirectory() as path:
			with self.assertRaises(SubmissionFix.BadCSVError):
				self.integrationContentsTest(args, path, test, answer, testset, roll)

	@contextmanager
	def tempDirectory(self, junkpath=None, files=None):
		path = os.path.abspath('test_folder')
		if not os.path.exists(path):
			os.makedirs(path)
			if junkpath and files:
				self._fillDirectory(junkpath, files)
		try:
			yield path
		finally:
			shutil.rmtree(path, ignore_errors=True)

	def _fillDirectory(self, path, files):
		path = os.path.abspath(path)
		if not os.path.exists(path):
			os.makedirs(path)
			for filepath in files:
				shutil.copy(filepath, os.path.abspath(path))

	@contextmanager
	def suppressOutput(self):
		with open(os.devnull, 'w') as devnull:
			oldstdout = sys.stdout
			sys.stdout = devnull
			try:
				yield
			finally: 
				sys.stdout = oldstdout

	@contextmanager
	def inDirectory(self, path):
		base = os.getcwd()
		os.chdir(path)
		try:
			yield
		finally:
			os.chdir(base)

	def integrationContentsTest(self, args, path, test, answer, testset, roll=None):
		shutil.copy(os.path.abspath(testset), path)
		if roll:
			shutil.copy(os.path.abspath(roll), path)
		with self.inDirectory(path):
			with self.suppressOutput():
				SubmissionFix.main(args)
		return self.existingPathsTest(os.getcwd(), test, answer)

	def integrationOverwriteTest(self, args, path, test, answer, testset, choice):
		shutil.copy(os.path.abspath(testset), path)
		submissionScript = os.path.abspath('SubmissionFix.py')
		with self.inDirectory(path):
			p = Popen(['python', submissionScript] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
			p.stdin.write(choice)
			p.wait()
		return self.existingPathsTest(os.getcwd(), test, answer)

	def integrationLateTest(self, args, path, test, testset, lateStudents):
		shutil.copy(os.path.abspath(testset), path)
		submissionScript = os.path.abspath('SubmissionFix.py')
		with self.inDirectory(path):
			p = Popen(['python', submissionScript] + args, stdout=PIPE, stderr=PIPE)
			out, err = p.communicate()
			p.wait()
		results = []
		for s in lateStudents:
			results.append('[{status}]  {student}\n'.format(status=any(s in out for s in lateStudents), student=s))
		self.logTest(os.getcwd(), test, results)
		return all(student in out for student in lateStudents)

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

	def addToSetup(self, names, files, setup, path=None):
		basePath = os.path.join(os.getcwd(), 'test_folder')
		if path:
			basePath = os.path.join(basePath, path)
		for name in names:
			base = os.path.join(basePath, '{name}').format(name=name)
			for f in files:
				setup.append(os.path.join(base, '{file}').format(file=f))
		return setup


class TestTSquareIntegration(TestIntegration, unittest.TestCase):
	"""Integration tests for the submission fix script."""

	#Normal tests
	def test_pathExistsNoFlags(self):
		answer = self.pathTestSetup('Homework 0')
		self.tempTestDir(['', 'testing_set1.zip', 'tsquare'], 'T-Square - Homework 0, No flags', answer, 'testing_set1.zip')

	def test_pathExistsMove(self):
		answer = self.pathTestSetup()
		self.tempTestDir(['', 'testing_set1.zip','tsquare', '-m'], 'T-Square - Homework 0, -move', answer, 'testing_set1.zip')

	def test_pathExistsPath(self):
		answer = self.pathTestSetup(os.path.join('NewFolder','Homework 0'))
		self.tempTestDir(['', 'testing_set1.zip','tsquare', '-pNewFolder'], 'T-Square - Homework 0, -path', answer, 'testing_set1.zip')

	def test_pathExistsPathConflictY(self):
		junkpath = os.path.join(os.getcwd(), 'test_folder', 'NewFolder')
		testfile = [os.path.abspath('testingtxt1.txt')]
		answer = self.pathTestSetup(os.path.join('NewFolder','Homework 0'))
		self.loadedTempTestDir(['testing_set1.zip','tsquare', '-pNewFolder'], 'T-Square - Homework 0, -path Conflict Y', answer, 'testing_set1.zip', junkpath, testfile, choice='y\n')

	def test_pathExistsPathConflictN(self):
		junkpath = os.path.join(os.getcwd(), 'test_folder', 'NewFolder')
		testfile = [os.path.abspath('testingtxt1.txt')]
		answer = [os.path.abspath('testingtxt1.txt')]
		self.loadedTempTestDir(['testing_set1.zip','tsquare', '-pNewFolder'], 'T-Square - Homework 0, -path Conflict N', answer, 'testing_set1.zip', junkpath, testfile, choice='n\n')

	def test_pathExistsPathMove(self):
		answer = self.pathTestSetup('NewFolder')
		self.tempTestDir(['', 'testing_set1.zip','tsquare', '-pNewFolder', '-m'], 'T-Square - Homework 0, -path -move', answer, 'testing_set1.zip')

	def test_pathExistsCSV(self):
		names = [('Boss, Big', '41b1318bf1cce2d9a40761b02bab065e'), ('Campbell, Roy', '39b73fb441b1c611f3a50be2b8693f03'),
				 ('Hunter, Naomi', 'd860291b770a7dadd23af116c5334caa'), ('Ocelot, Revolver', 'ef95ea7fbb72b57b38bd5aa7efcf8ca3'), 
				 ('Silverburgh, Meryl', '205105fa7784a73c91e1412cfc886f65'), ('Snake, Liquid', 'e60a34764ec988f9d4597fe7825cdd63'), 
				 ('Snake, Solid', '437e86082822caa972544f09da5f1050')]
		answer = self.pathTestSetup('Homework 0', names)
		csv = os.path.abspath('testingcsv1.csv')
		self.tempTestDir(['', 'testing_set1.zip','tsquare', '-c' + csv], 'T-Square - Homework 0, -csv', answer, 'testing_set1.zip')

	#Parens tests - (Malloc)
	def test_pathExistsNoFlagsParens(self):
		answer = self.pathTestSetup('Homework 0 (Malloc)')
		self.tempTestDir(['', 'testing_set2.zip', 'tsquare'], 'T-Square - Homework 0, No flags', answer, 'testing_set2.zip')

	def test_pathExistsMoveParens(self):
		answer = self.pathTestSetup()
		self.tempTestDir(['', 'testing_set2.zip','tsquare', '-m'], 'T-Square - Homework 0, -move', answer, 'testing_set2.zip')

	def test_pathExistsPathParens(self):
		answer = self.pathTestSetup(os.path.join('NewFolder','Homework 0 (Malloc)'))
		self.tempTestDir(['', 'testing_set2.zip','tsquare', '-pNewFolder'], 'T-Square - Homework 0, -path', answer, 'testing_set2.zip')

	def test_pathExistsPathMoveParens(self):
		answer = self.pathTestSetup('NewFolder')
		self.tempTestDir(['', 'testing_set2.zip','tsquare', '-pNewFolder', '-m'], 'T-Square - Homework 0, -path -move', answer, 'testing_set2.zip')

	#Other tests
	def test_lateStudentsListed(self):
		students = ['Fox, Grey', 'Ling, Mei']
		self.lateTempTestDir(['testing_set1.zip','tsquare', '-t', '02/28/05','23:55'], 'T-Square - Homework 0, -time', 'testing_set1.zip', students)

	def test_pathExistsCSVWrong(self):
		answer = self.pathTestSetup()
		csv = os.path.abspath('testingcsv5.csv')
		self.exitTempTestDir(['', 'testing_set1.zip','tsquare', '-c' + csv], 'T-Square - Homework 0, -csv Wrong', answer, 'testing_set1.zip')

	def test_pathExistsZip(self):
		files = [os.path.join('testingtxt1.txt'), os.path.join('patriots.asm')]
		names = [('Anderson, Donald', '20f5d6b21d3d2b3685f2144bc2fc771d'), ('Baker, Kenneth', 'd30f7f7f153271e28c4b632db9fa0b01'),
					 ('Boss, Big', '41b1318bf1cce2d9a40761b02bab065e'), ('Campbell, Roy', '39b73fb441b1c611f3a50be2b8693f03'),
					 ('Emmerich, Hal', 'c664acb099c59b2a4940773012d9ca40'), ('Fox, Grey', 'f8049726520d8dc911a7014af736e302'),
					 ('Hunter, Naomi', 'd860291b770a7dadd23af116c5334caa'), ('Ling, Mei', '29eb03d07be7696caba2f608ac7b8a71'),
					 ('Mantis, Psycho', '04a6c6c02d714a17cdd6aab5107008e4'), ('Miller, Kazuhira', 'f5cd92c317cec73b96ede092a62adcfe'), 
					 ('Ocelot, Revolver', 'ef95ea7fbb72b57b38bd5aa7efcf8ca3'), ('Octopus, Decoy', '53a36da95a92702adfa25cb1e221a0d2'),
					 ('Raven, Vulcan', '8d6da48c03e4e95fad55843d1ed84211'), ('Romanenko, Nastasha', '6569a8e2f02a2611a34106bd2d77f941'), 
					 ('Silverburgh, Meryl', '205105fa7784a73c91e1412cfc886f65'), ('Snake, Liquid', 'e60a34764ec988f9d4597fe7825cdd63'), 
					 ('Snake, Solid', '437e86082822caa972544f09da5f1050'), ('Snake, Solidus', 'de2caa5dd90df87e03cfe62780a58c94'), 
					 ('Wolf, Sniper', '4f4002d30d729c89bb7fca07bf693c2c')]
		answer = self.addToSetup(['Sasaki, Johnny'], files, self.pathTestSetup('Homework 0', testsetNames=names), 'Homework 0')
		self.tempTestDir(['', 'testing_set3.zip', 'tsquare'], 'T-Square - Homework 0, No Flags, Zip', answer, 'testing_set3.zip', 'testroll.csv')
	
	def test_pathExistsTargz(self):
		files = [os.path.join('testingtxt1.txt'), os.path.join('patriots.asm')]
		names = [('Anderson, Donald', '20f5d6b21d3d2b3685f2144bc2fc771d'), ('Baker, Kenneth', 'd30f7f7f153271e28c4b632db9fa0b01'),
					 ('Boss, Big', '41b1318bf1cce2d9a40761b02bab065e'), ('Campbell, Roy', '39b73fb441b1c611f3a50be2b8693f03'),
					 ('Emmerich, Hal', 'c664acb099c59b2a4940773012d9ca40'), ('Fox, Grey', 'f8049726520d8dc911a7014af736e302'),
					 ('Hunter, Naomi', 'd860291b770a7dadd23af116c5334caa'), ('Ling, Mei', '29eb03d07be7696caba2f608ac7b8a71'),
					 ('Mantis, Psycho', '04a6c6c02d714a17cdd6aab5107008e4'), ('Miller, Kazuhira', 'f5cd92c317cec73b96ede092a62adcfe'), 
					 ('Ocelot, Revolver', 'ef95ea7fbb72b57b38bd5aa7efcf8ca3'), ('Octopus, Decoy', '53a36da95a92702adfa25cb1e221a0d2'),
					 ('Raven, Vulcan', '8d6da48c03e4e95fad55843d1ed84211'), ('Romanenko, Nastasha', '6569a8e2f02a2611a34106bd2d77f941'), 
					 ('Silverburgh, Meryl', '205105fa7784a73c91e1412cfc886f65'), ('Snake, Liquid', 'e60a34764ec988f9d4597fe7825cdd63'), 
					 ('Snake, Solid', '437e86082822caa972544f09da5f1050'), ('Snake, Solidus', 'de2caa5dd90df87e03cfe62780a58c94'), 
					 ('Wolf, Sniper', '4f4002d30d729c89bb7fca07bf693c2c')]
		answer = self.addToSetup(['Sasaki, Johnny'], files, self.pathTestSetup('Homework 0', testsetNames=names), 'Homework 0')
		self.tempTestDir(['', 'testing_set4.zip', 'tsquare'], 'T-Square - Homework 0, No Flags, Tar.gz', answer, 'testing_set4.zip', 'testroll.csv')

	def test_pathExistsTargz(self):
		files = [os.path.join('testingtxt1.txt'), os.path.join('patriots.asm')]
		names = [('Anderson, Donald', '20f5d6b21d3d2b3685f2144bc2fc771d'), ('Baker, Kenneth', 'd30f7f7f153271e28c4b632db9fa0b01'),
					 ('Boss, Big', '41b1318bf1cce2d9a40761b02bab065e'), ('Campbell, Roy', '39b73fb441b1c611f3a50be2b8693f03'),
					 ('Emmerich, Hal', 'c664acb099c59b2a4940773012d9ca40'), ('Fox, Grey', 'f8049726520d8dc911a7014af736e302'),
					 ('Hunter, Naomi', 'd860291b770a7dadd23af116c5334caa'), ('Ling, Mei', '29eb03d07be7696caba2f608ac7b8a71'),
					 ('Mantis, Psycho', '04a6c6c02d714a17cdd6aab5107008e4'), ('Miller, Kazuhira', 'f5cd92c317cec73b96ede092a62adcfe'), 
					 ('Ocelot, Revolver', 'ef95ea7fbb72b57b38bd5aa7efcf8ca3'), ('Octopus, Decoy', '53a36da95a92702adfa25cb1e221a0d2'),
					 ('Raven, Vulcan', '8d6da48c03e4e95fad55843d1ed84211'), ('Romanenko, Nastasha', '6569a8e2f02a2611a34106bd2d77f941'), 
					 ('Silverburgh, Meryl', '205105fa7784a73c91e1412cfc886f65'), ('Snake, Liquid', 'e60a34764ec988f9d4597fe7825cdd63'), 
					 ('Snake, Solid', '437e86082822caa972544f09da5f1050'), ('Snake, Solidus', 'de2caa5dd90df87e03cfe62780a58c94'), 
					 ('Wolf, Sniper', '4f4002d30d729c89bb7fca07bf693c2c')]
		answer = self.addToSetup(['Sasaki, Johnny'], files, self.pathTestSetup('Homework 0', testsetNames=names), 'Homework 0')
		self.tempTestDir(['', 'testing_set5.zip', 'tsquare'], 'T-Square - Homework 0, No Flags, Tar', answer, 'testing_set5.zip', 'testroll.csv')



	#Testing functions and setup
	def pathTestSetup(self, root=None, testsetNames=None):
		basePath = os.path.join(os.getcwd(), 'test_folder')
		if root:
			basePath = os.path.join(basePath, root)
		nameList = [('Anderson, Donald', '20f5d6b21d3d2b3685f2144bc2fc771d'), ('Baker, Kenneth', 'd30f7f7f153271e28c4b632db9fa0b01'),
					 ('Boss, Big', '41b1318bf1cce2d9a40761b02bab065e'), ('Campbell, Roy', '39b73fb441b1c611f3a50be2b8693f03'),
					 ('Emmerich, Hal', 'c664acb099c59b2a4940773012d9ca40'), ('Fox, Grey', 'f8049726520d8dc911a7014af736e302'),
					 ('Hunter, Naomi', 'd860291b770a7dadd23af116c5334caa'), ('Ling, Mei', '29eb03d07be7696caba2f608ac7b8a71'),
					 ('Mantis, Psycho', '04a6c6c02d714a17cdd6aab5107008e4'), ('Miller, Kazuhira', 'f5cd92c317cec73b96ede092a62adcfe'), 
					 ('Ocelot, Revolver', 'ef95ea7fbb72b57b38bd5aa7efcf8ca3'), ('Octopus, Decoy', '53a36da95a92702adfa25cb1e221a0d2'),
					 ('Raven, Vulcan', '8d6da48c03e4e95fad55843d1ed84211'), ('Romanenko, Nastasha', '6569a8e2f02a2611a34106bd2d77f941'), 
					 ('Sasaki, Johnny', '757c592a306b9dcfeaa6e34ccb752b4a'), ('Silverburgh, Meryl', '205105fa7784a73c91e1412cfc886f65'),
					 ('Snake, Liquid', 'e60a34764ec988f9d4597fe7825cdd63'), ('Snake, Solid', '437e86082822caa972544f09da5f1050'),
					 ('Snake, Solidus', 'de2caa5dd90df87e03cfe62780a58c94'), ('Wolf, Sniper', '4f4002d30d729c89bb7fca07bf693c2c')]
		testsetNames = testsetNames or nameList
		testset0Paths = ['Text', '_submissionText.html', 'timestamp.txt', 'patriots.asm']
		answer = []
		for n in testsetNames:
			base = os.path.join(basePath, '{name}').format(name=n[0])
			answer.append(os.path.join(base, '{test}').format(test=testset0Paths[0]))
			answer.append(os.path.join(base, '{test}', '{name}({nhash}){sub}').format(test=testset0Paths[0],name=n[0],nhash=n[1],sub=testset0Paths[1]))
			answer.append(os.path.join(base, '{test}', '{time}').format(test=testset0Paths[0],time=testset0Paths[2]))
			answer.append(os.path.join(base, '{asm}').format(asm=testset0Paths[3]))
		return answer

class TestCanvasIntegration(TestIntegration, unittest.TestCase):
	"""Integration tests for the submission fix script."""

	#Normal tests
	def test_pathExistsNoFlags(self):
		answer = self.pathTestSetup()
		self.tempTestDir(['', 'testing_setc1.zip', 'canvas', 'testroll.csv'], 'Canvas - Homework 0, No flags', answer, 'testing_setc1.zip', 'testroll.csv')

	def test_pathExistsCSV(self):
		names = ['Boss, Big', 'Campbell, Roy', 'Hunter, Naomi', 'Ocelot, Revolver', 'Silverburgh, Meryl', 
				 'Snake, Liquid', 'Snake, Solid']
		answer = self.pathTestSetup(testsetNames=names)
		csv = os.path.abspath('testingcsv1.csv')
		self.tempTestDir(['', 'testing_setc1.zip','canvas', 'testroll.csv', '-c' + csv], 'Canvas - Homework 0, -csv', answer, 'testing_setc1.zip', 'testroll.csv')

	def test_pathExistsPath(self):
		answer = self.pathTestSetup('NewFolder')
		self.tempTestDir(['', 'testing_setc1.zip','canvas', 'testroll.csv', '-pNewFolder'], 'Canvas - Homework 0, -path', answer, 'testing_setc1.zip', 'testroll.csv')

	def test_pathExistsResubmit(self):
		answer = self.pathTestSetup()
		self.tempTestDir(['', 'testing_setc2.zip', 'canvas', 'testroll.csv'], 'Canvas - Homework 0, No Flags, Resubmitted files', answer, 'testing_setc2.zip', 'testroll.csv')

	def test_pathExistsBadNames(self):
		answer = self.pathTestSetup()
		self.tempTestDir(['', 'testing_setc3.zip', 'canvas', 'testroll.csv'], 'Canvas - Homework 0, No flags, Bad Names', answer, 'testing_setc3.zip', 'testroll.csv')

	def test_pathExistsFolderCollision(self):
		answer = self.pathTestSetup()
		junkpath = os.path.join(os.getcwd(), 'test_folder', 'Sasaki, Jonny')
		testfile = [os.path.abspath('testingtxt1.txt')]
		self.loadedTempTestDir(['', 'testing_setc1.zip', 'canvas', 'testroll.csv'], 'Canvas - Homework 0, No flags, Folder Collision', answer, 'testing_setc1.zip', junkpath, testfile, roll='testroll.csv')

	def test_pathExistsCSVWrong(self):
		answer = self.pathTestSetup()
		csv = os.path.abspath('testingcsv5.csv')
		self.exitTempTestDir(['', 'testing_setc1.zip','canvas', 'testroll.csv', '-c' + csv], 'Canvas - Homework 0, -csv Wrong', answer, 'testing_setc1.zip', 'testroll.csv')

	def test_pathExistsZip(self):
		files = [os.path.join('sasakijohnny_1111_1111_HW01','testingtxt1.txt'), os.path.join('sasakijohnny_1111_1111_HW01','patriots.asm')]
		names = ['Anderson, Donald', 'Baker, Kenneth','Boss, Big', 'Campbell, Roy', 'Emmerich, Hal', 'Fox, Grey',
					 'Hunter, Naomi', 'Ling, Mei', 'Mantis, Psycho', 'Miller, Kazuhira', 'Ocelot, Revolver', 'Octopus, Decoy', 
					 'Raven, Vulcan', 'Romanenko, Nastasha', 'Silverburgh, Meryl', 'Snake, Liquid', 
					 'Snake, Solid', 'Snake, Solidus', 'Wolf, Sniper']
		answer = self.addToSetup(['Sasaki, Johnny'], files, self.pathTestSetup(testsetNames=names))
		self.tempTestDir(['', 'testing_setc4.zip', 'canvas', 'testroll.csv'], 'Canvas - Homework 0, No Flags, Zip', answer, 'testing_setc4.zip', 'testroll.csv')

	def test_pathExistsTargz(self):
		files = [os.path.join('sasakijohnny_1111_1111_HW01','testingtxt1.txt'), os.path.join('sasakijohnny_1111_1111_HW01','patriots.asm')]
		names = ['Anderson, Donald', 'Baker, Kenneth','Boss, Big', 'Campbell, Roy', 'Emmerich, Hal', 'Fox, Grey',
					 'Hunter, Naomi', 'Ling, Mei', 'Mantis, Psycho', 'Miller, Kazuhira', 'Ocelot, Revolver', 'Octopus, Decoy', 
					 'Raven, Vulcan', 'Romanenko, Nastasha', 'Silverburgh, Meryl', 'Snake, Liquid', 
					 'Snake, Solid', 'Snake, Solidus', 'Wolf, Sniper']
		answer = self.addToSetup(['Sasaki, Johnny'], files, self.pathTestSetup(testsetNames=names))
		self.tempTestDir(['', 'testing_setc5.zip', 'canvas', 'testroll.csv'], 'Canvas - Homework 0, No Flags, Tar.gz', answer, 'testing_setc5.zip', 'testroll.csv')

	def test_pathExistsTar(self):
		files = [os.path.join('sasakijohnny_1111_1111_HW01','testingtxt1.txt'), os.path.join('sasakijohnny_1111_1111_HW01','patriots.asm')]
		names = ['Anderson, Donald', 'Baker, Kenneth','Boss, Big', 'Campbell, Roy', 'Emmerich, Hal', 'Fox, Grey',
					 'Hunter, Naomi', 'Ling, Mei', 'Mantis, Psycho', 'Miller, Kazuhira', 'Ocelot, Revolver', 'Octopus, Decoy', 
					 'Raven, Vulcan', 'Romanenko, Nastasha', 'Silverburgh, Meryl', 'Snake, Liquid', 
					 'Snake, Solid', 'Snake, Solidus', 'Wolf, Sniper']
		answer = self.addToSetup(['Sasaki, Johnny'], files, self.pathTestSetup(testsetNames=names))
		self.tempTestDir(['', 'testing_setc6.zip', 'canvas', 'testroll.csv'], 'Canvas - Homework 0, No Flags, Tar', answer, 'testing_setc6.zip', 'testroll.csv')

	def test_pathExistsZipPath(self):
		files = [os.path.join('sasakijohnny_1111_1111_HW01','testingtxt1.txt'), os.path.join('sasakijohnny_1111_1111_HW01','patriots.asm')]
		names = ['Anderson, Donald', 'Baker, Kenneth','Boss, Big', 'Campbell, Roy', 'Emmerich, Hal', 'Fox, Grey',
					 'Hunter, Naomi', 'Ling, Mei', 'Mantis, Psycho', 'Miller, Kazuhira', 'Ocelot, Revolver', 'Octopus, Decoy', 
					 'Raven, Vulcan', 'Romanenko, Nastasha', 'Silverburgh, Meryl', 'Snake, Liquid', 
					 'Snake, Solid', 'Snake, Solidus', 'Wolf, Sniper']
		answer = self.addToSetup(['Sasaki, Johnny'], files, self.pathTestSetup('NewFolder', testsetNames=names), 'NewFolder')
		self.tempTestDir(['', 'testing_setc4.zip', 'canvas', 'testroll.csv', '-pNewFolder'], 'Canvas - Homework 0, -path Zip', answer, 'testing_setc4.zip', 'testroll.csv')

	def test_pathExistsMultiFile(self):
		answer = self.addToSetup(['Sasaki, Johnny'], ['cipher.asm'], self.pathTestSetup())
		self.tempTestDir(['', 'testing_setc7.zip', 'canvas', 'testroll.csv'], 'Canvas - Homework 0, No flags, Multiple Files per Student', answer, 'testing_setc7.zip', 'testroll.csv')

	def test_pathExistsSection(self):
		names = ['Snake, Solid', 'Fox, Grey', 'Hunter, Naomi', 'Raven, Vulcan']
		answer = self.pathTestSetup(testsetNames=names)
		self.tempTestDir(['', 'testing_setc1.zip','canvas', 'testroll.csv', '-sa1'], 'Canvas - Homework 0, -s a1', answer, 'testing_setc1.zip', 'testroll.csv')

	def test_pathExistsQuizzes(self):
		answer = self.pathTestSetup()
		self.tempTestDir(['', 'testing_setc8.zip', 'canvas', 'testroll.csv'], 'Canvas - Homework 0, No flags, Quiz Based Submissions', answer, 'testing_setc8.zip', 'testroll.csv')

	def test_pathExistsQuizzesSection(self):
		names = ['Snake, Solid', 'Fox, Grey', 'Hunter, Naomi', 'Raven, Vulcan']
		answer = self.pathTestSetup(testsetNames=names)
		self.tempTestDir(['', 'testing_setc8.zip','canvas', 'testroll.csv', '-sa1'], 'Canvas - Homework 0 Quiz Based Submissions, -s a1', answer, 'testing_setc8.zip', 'testroll.csv')

	def test_pathExistsQuizzesCSV(self):
		names = ['Boss, Big', 'Campbell, Roy', 'Hunter, Naomi', 'Ocelot, Revolver', 'Silverburgh, Meryl', 
				 'Snake, Liquid', 'Snake, Solid']
		answer = self.pathTestSetup(testsetNames=names)
		csv = os.path.abspath('testingcsv1.csv')
		self.tempTestDir(['', 'testing_setc8.zip','canvas', 'testroll.csv', '-c' + csv], 'Canvas - Homework 0 Quiz Based Submissions, -csv', answer, 'testing_setc8.zip', 'testroll.csv')

	#New tests =====================================
	def test_pathExistsTarMove1(self):
		files = ['testingtxt1.txt','patriots.asm']
		names = ['Anderson, Donald', 'Baker, Kenneth','Boss, Big', 'Campbell, Roy', 'Emmerich, Hal', 'Fox, Grey',
					 'Hunter, Naomi', 'Ling, Mei', 'Mantis, Psycho', 'Miller, Kazuhira', 'Ocelot, Revolver', 'Octopus, Decoy', 
					 'Raven, Vulcan', 'Romanenko, Nastasha', 'Silverburgh, Meryl', 'Snake, Liquid', 
					 'Snake, Solid', 'Snake, Solidus', 'Wolf, Sniper']
		answer = self.addToSetup(['Sasaki, Johnny'], files, self.pathTestSetup(testsetNames=names))
		self.tempTestDir(['', 'testing_setc6.zip', 'canvas', 'testroll.csv', '-m1'], 'Canvas - Homework 0, -m 1, Tar', answer, 'testing_setc6.zip', 'testroll.csv')

	def test_pathExistsTarMove1Nested(self):
		files = [os.path.join('Texts','testingtxt1.txt'),'patriots.asm']
		names = ['Anderson, Donald', 'Baker, Kenneth','Boss, Big', 'Campbell, Roy', 'Emmerich, Hal', 'Fox, Grey',
					 'Hunter, Naomi', 'Ling, Mei', 'Mantis, Psycho', 'Miller, Kazuhira', 'Ocelot, Revolver', 'Octopus, Decoy', 
					 'Raven, Vulcan', 'Romanenko, Nastasha', 'Silverburgh, Meryl', 'Snake, Liquid', 
					 'Snake, Solid', 'Snake, Solidus', 'Wolf, Sniper']
		answer = self.addToSetup(['Sasaki, Johnny'], files, self.pathTestSetup(testsetNames=names))
		self.tempTestDir(['', 'testing_setc10.zip', 'canvas', 'testroll.csv', '-m1'], 'Canvas - Homework 0, -m 1, Tar', answer, 'testing_setc10.zip', 'testroll.csv')

	def test_pathExistsTarMoveAll(self):
		files = ['testingtxt1.txt','patriots.asm']
		names = ['Anderson, Donald', 'Baker, Kenneth','Boss, Big', 'Campbell, Roy', 'Emmerich, Hal', 'Fox, Grey',
					 'Hunter, Naomi', 'Ling, Mei', 'Mantis, Psycho', 'Miller, Kazuhira', 'Ocelot, Revolver', 'Octopus, Decoy', 
					 'Raven, Vulcan', 'Romanenko, Nastasha', 'Silverburgh, Meryl', 'Snake, Liquid', 
					 'Snake, Solid', 'Snake, Solidus', 'Wolf, Sniper']
		answer = self.addToSetup(['Sasaki, Johnny'], files, self.pathTestSetup(testsetNames=names))
		self.tempTestDir(['', 'testing_setc9.zip', 'canvas', 'testroll.csv', '-mall'], 'Canvas - Homework 0, -m all, Tar', answer, 'testing_setc9.zip', 'testroll.csv')

	def test_pathExistsTarMoveAllMultipleFolders(self):
		files = ['testingtxt1.txt','patriots.asm']
		names = ['Anderson, Donald', 'Baker, Kenneth','Boss, Big', 'Campbell, Roy', 'Emmerich, Hal', 'Fox, Grey',
					 'Hunter, Naomi', 'Ling, Mei', 'Mantis, Psycho', 'Miller, Kazuhira', 'Ocelot, Revolver', 'Octopus, Decoy', 
					 'Raven, Vulcan', 'Romanenko, Nastasha', 'Silverburgh, Meryl', 'Snake, Liquid', 
					 'Snake, Solid', 'Snake, Solidus', 'Wolf, Sniper']
		answer = self.addToSetup(['Sasaki, Johnny'], files, self.pathTestSetup(testsetNames=names))
		self.tempTestDir(['', 'testing_setc11.zip', 'canvas', 'testroll.csv', '-mall'], 'Canvas - Homework 0, -m all, Tar', answer, 'testing_setc11.zip', 'testroll.csv')

	#Testing functions and setup
	def pathTestSetup(self, root=None, testsetNames=None):
		basePath = os.path.join(os.getcwd(), 'test_folder')
		if root:
			basePath = os.path.join(basePath, root)
		nameList = ['Anderson, Donald', 'Baker, Kenneth','Boss, Big', 'Campbell, Roy', 'Emmerich, Hal', 'Fox, Grey',
					 'Hunter, Naomi', 'Ling, Mei', 'Mantis, Psycho', 'Miller, Kazuhira', 'Ocelot, Revolver', 'Octopus, Decoy', 
					 'Raven, Vulcan', 'Romanenko, Nastasha', 'Sasaki, Johnny', 'Silverburgh, Meryl', 'Snake, Liquid', 
					 'Snake, Solid', 'Snake, Solidus', 'Wolf, Sniper']
		testsetNames = testsetNames or nameList
		testsetPaths = ['patriots.asm']
		answer = []
		for n in testsetNames:
			base = os.path.join(basePath, '{name}').format(name=n)
			answer.append(os.path.join(base, '{asm}').format(asm=testsetPaths[0]))
		return answer

if __name__ == '__main__' :
	openLog()

	suite = unittest.TestLoader().loadTestsFromTestCase(TestTSquareIntegration)
	unittest.TextTestRunner(verbosity=2).run(suite)
	print '\n'
	suite = unittest.TestLoader().loadTestsFromTestCase(TestCanvasIntegration)
	unittest.TextTestRunner(verbosity=2).run(suite)