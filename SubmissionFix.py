#!/usr/bin/env python
from __future__ import with_statement

"""
This is an awesome script to clean up the bulk submission zip file into a directory with 
nicely named, (mostly) unnested folders. If specified, it will only extract certain students'
submissions and/or extract submissions to a specified directory.
"""

__author__ = "Marie Weeks"
__version__ = "1.5"

import os
import sys
import csv
import shutil
import zipfile
import tarfile
import argparse

#TODO: add progress bar! :D
#TODO: check for compressed files inside compressed files (in student submissions)

def main():
	parser = argparse.ArgumentParser(description='Script to extract student submissions from bulk zip.')
	parser.add_argument('bulksubmission', help='bulk zip of student submissions')
	parser.add_argument('-c', '--csv', help='student list csv file')
	parser.add_argument('-p', '--path', help='extraction path for bulk submissions zip')
	parser.add_argument('-m', '--move', help='move student folders out of archive root folder', action='store_true')

	if len(sys.argv) == 1 :
		parser.print_help()
		sys.exit(1)

	args = parser.parse_args()

	zippy = args.bulksubmission

	#csv file input
	if args.csv :
		students = readCSV(args.csv)
		if args.path :		#csv and extraction path input
			if not os.path.exists(args.path) :
				os.makedirs(args.path)
				args.path += '/'
			if not args.path.endswith('/') :
				args.path += '/'
			directory = extractBulk(zippy, students, args.path)
		else :
			directory = extractBulk(zippy, students)

	#extraction path input
	elif args.path :
		if not os.path.exists(args.path) :
			os.makedirs(args.path)
			args.path += '/'
		if not args.path.endswith('/') :
			args.path += '/'
		directory = extractBulk(zippy, directory=args.path)
	else :
		directory = extractBulk(zippy)

	rename(directory)	
	move(directory, args.move)
	print "Done"


def readCSV(csvfile):
	"""Create a list of students to grade from input csv file.

	Reads through csv file and appends each student name to a list, creating a list of lists.
	List comprehension transforms this into a single list of student names and converts each
	name to uppercase (since T-Square sometimes has student names in uppercase). 

	Args:
		csvfile: csvfile with names of students to grade

	Returns:
		A list of student names to grade, all in uppercase.
	"""

	print "Reading spreadsheet..."
	students = []
	with open(csvfile, 'rb') as f :
		reader = csv.reader(f, delimiter=':')
		for row in reader :
			students.append(row)

	#convert list[list[]] to list[], convert names to uppercase
	students = [s[0].upper() for s in students]

	return students



def extractBulk(zippy, students=[], directory='.'):
	"""Extracts the bulk submission download.

	By default, extracts the bulk submission zip to the working directory. If a directory to 
	extract to is input, the zip with extract to that directory. If a csv file of student names 
	is input, the zip will only extract those students' submissions.
	
	Args:
		zippy: bulk submission zip file 
		students: list of student names to grade (optional)
		directory: directory to extract zip to (optional, default: working directory)

	Returns:
		Path of newly created directory with extracted files
	"""

	print "Decompressing " + zippy
	zfile = zipfile.ZipFile(zippy)

	for name in zfile.namelist() :
		#check if student list csv file was input
		if students :
			#check if any student in students is in the dirname string
			if not any([s in name.upper() for s in students]) :
				continue

		dirname = directory		#set directory for extraction
		if not os.path.exists(dirname) :
			os.makedirs(dirname)
		zfile.extract(name, dirname)

	if directory == '.' :
		directory = name[:name.find(os.sep)]
	else :
		directory += name[:name.find(os.sep)]

	return directory

def rename(directory):
	"""Renames all student folders to their names

	Renames student folders in the given directory by removing the hashcode nonsense at the 
	end of the folder name. 

	Args:
		directory: directory with student submission folders
	"""

	print "Renaming files..."
	for fn in os.listdir(directory) :
		path = os.path.join(directory, fn)
		os.rename(path, path[:path.find('(')])	

def move(directory, out):
	"""Moves all files in "Submission attachment(s)" up a level

	All files in student's main folder (timestamp.txt, comments.txt, etc) are moved to the 
	newly created directory Text. "Feedback Attachment(s)" folder is also moved to Text. All 
	files within "Submission attachment(s)" are moved up to the student's main folder. Empty 
	"Submission attachment(s)" folder is deleted. extract() is called to extract any zip or 
	tar files the student submitted. If "out" is true, the student folders will be moved out
	the root arcive folder and up one level in the directory tree. Useful for having fewer 
	nested folders if you specify an extraction folder.

	Args:
		directory: directory with student submission folders
	"""

	for fn in os.listdir(directory) :
		if os.path.isdir(os.path.join(directory, fn)) :
			#move timestamp, comments, feedbackText, submissionText to Text folder
			source = os.path.join(directory, fn)
			dest = os.path.join(source, "Text")

			if not os.path.exists(dest) :
				os.makedirs(dest)

			for files in os.listdir(source) :
				if os.path.isfile(os.path.join(source, files)) :
					path = os.path.join(source, files)
					shutil.move(path, dest)
			path = os.path.join(source, "Feedback Attachment(s)")
			if os.path.isdir(path) :
				shutil.move(path, dest)

			#move submission attachments out of folder into student name folder and extract
			dest = os.path.join(directory, fn)
			source = os.path.join(dest, "Submission attachment(s)")
			for files in os.listdir(source) :
				path = os.path.join(source, files)
				shutil.move(path, dest)
			os.rmdir(source)
			extract(dest)

		#move student folder out of the root archive folder
		if out :
			source = directory
			dest, extra = os.path.split(directory)
			path = os.path.join(source, fn)
			shutil.move(path, dest)
	if out :		
		os.rmdir(source)


def extract(directory):
	"""Extracts any zip or tar files in given directory

	Looks through files in the input directory, extracting every zip and tar file. Resulting 
	files appear alongside archive file in the directory. 

	Args:
		directory: directory to be searched for archive files
	"""
	print "Looking for compressed files..."
	for fn in os.listdir(directory) :
		if fn.endswith('.zip') :
			unzip(directory, os.path.join(directory, fn))
		if fn.find('.tar') >= 0 :
			untar(directory, os.path.join(directory, fn))


def unzip(directory, zippy):
	"""Unzips a given zip file into the given directory

	Takes in a zip file and extracts its contents to the given directory. Afterwards, the
	zip file is removed.

	Args:
		directory: directory where files will be extracted to
		zippy: zip file to unzip
	"""
	print "Unzipping " + zippy
	zfile = zipfile.ZipFile(zippy)
	for name in zfile.namelist() :
		dirname = directory
		zfile.extract(name, dirname)
	os.remove(zippy)


def untar(directory, tarry):
	"""Extracts a given tar file into the given directory

	Takes in a tar file and extracts its contents to the given directory. Afterwards, the
	tar file is removed.

	Args:
		directory: directory where files will be extracted to
		tarry: tar file to extract

	Tested on .tar.gz. Unsure if this will work on other tar files. 
	"""
	print "Extracting " + tarry
	tar = tarfile.open(tarry)
	tar.extractall(directory)
	tar.close()
	os.remove(tarry)

main()