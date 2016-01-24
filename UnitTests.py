#!/usr/bin/env python
from __future__ import with_statement

"""
A collection of unit tests for the submission script.
"""
__author__ = "Marie Weeks"

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
        answer = ['Snake, Solid', 'Snake, Liquid', 'Boss, Big', 'Ocelot, Revolver', 
                  'Silverburgh, Meryl', 'Hunter, Naomi', 'Campbell, Roy']
        self.assertEqual(SubmissionFix.TSquare().readCSV('testingcsv1.csv'), answer)

    def test_readCSVAll(self):
        answer = ['Snake, Solid', 'Snake, Liquid', 'Snake, Solidus', 'Boss, Big', 
                  'Fox, Grey', 'Ocelot, Revolver', 'Emmerich, Hal', 'Hunter, Naomi',
                  'Silverburgh, Meryl', 'Wolf, Sniper', 'Raven, Vulcan', 'Mantis, Psycho',
                  'Octopus, Decoy', 'Campbell, Roy', 'Anderson, Donald', 'Baker, Kenneth',
                  'Miller, Kazuhira', 'Ling, Mei', 'Romanenko, Nastasha', 'Sasaki, Johnny']
        self.assertEqual(SubmissionFix.TSquare().readCSV('testingcsv2.csv'), answer)

    def test_readCSVOverlap(self):
        answer = ['Snake, Solidus', 'Snake, Solid']
        self.assertEqual(SubmissionFix.TSquare().readCSV('testingcsv3.csv'), answer)

    def test_readCSVOne(self):
        answer = ['Fox, Grey']
        self.assertEqual(SubmissionFix.TSquare().readCSV('testingcsv4.csv'), answer)

    #stripTime
    @unittest.skipIf(findTime is False, "pytz needed for this test")
    def test_stripTimeNormal(self):
        eastern = timezone('US/Eastern')
        answer = datetime.datetime(2005,02,28,17,15) 
        self.assertEqual(SubmissionFix.TSquare().stripTime('20050228221512345'), eastern.localize(answer))

    @unittest.skipIf(findTime is False, "pytz needed for this test")
    def test_stripTimeTimeZoneBehindDay(self):
        eastern = timezone('US/Eastern')
        answer = datetime.datetime(2005,02,27,22,30) 
        self.assertEqual(SubmissionFix.TSquare().stripTime('20050228033012345'), eastern.localize(answer))

    #_createRollDict
    def test_createRollDictNonLetter(self):
        answer = {'SILVERBURGHSASAKIMERYL': 'Silverburgh-Sasaki, Meryl',
                'NDRAMSOPHIE': 'N\'dram, Sophie'}
        roll, _ = SubmissionFix.Canvas('testingcsv6.csv')._createRollDict('testingcsv6.csv')
        self.assertEqual(roll, answer)


if __name__ == '__main__' :
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSubfixMethods)
    unittest.TextTestRunner(verbosity=2).run(suite)