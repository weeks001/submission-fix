#!/usr/bin/env python
from __future__ import with_statement
from datetime import datetime, date

"""
This script extracts student submissions from both T-Square and Canvas bundled
bulk submissions. Depending on the submission manager being used there are 
different options for cleaning up the submissions. Both allow for extracting
only specific students and into a given directory. It automatically extracts 
zip, tar, and tar.gz files that students submit. 
"""

__author__ = "Marie Weeks"

import os
import sys
import csv
import struct
import shutil
import zipfile
import tarfile
import argparse
import re
import time


try :
    from pytz import timezone
    import pytz
    findTime = True
except ImportError :
    findTime = False

_student_file_patterns = tuple(map(re.compile, [
    r'^(?P<student>[^0-9]+)\d+_question_(\d+_){2}(?P<filename>.*)$',
    r'^(?P<student>[^_0-9]+)_(\d+_){2}(?P<filename>.*)$',
    r'^(?P<student>[^_0-9]+)_late_(\d+_){2}(?P<filename>.*)$'
]))

def requiredLength(nargs):
    """Checks that input arguments for given flag are of the specified number.

        Creates a custom action by extending Action and overriding the ___call__ method.

        Args:
            nargs: number of arguments for flag

        Returns:
            RequiredLength: custom action subclass
    """
    class RequiredLength(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            if not len(values) == nargs:
                msg = 'argument "{f}" requires {nargs} arguments'.format(f=self.dest, nargs=nargs)
                raise argparse.ArgumentTypeError(msg)
            setattr(args, self.dest, values)
    return RequiredLength

def extract(directory):
    """Extracts any zip or tar files in given directory

    Looks through files in the input directory, extracting every zip and tar file. Resulting 
    files appear alongside archive file in the directory. 

    Args:
        directory: directory to be searched for archive files
    """

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

    with zipfile.ZipFile(zippy) as zfile:
        for filename in zfile.namelist() :
            zfile.extract(filename, directory)
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

    try:
        tar = tarfile.open(tarry)
        tar.extractall(directory)
    except tarfile.ReadError:
        print ("Warning: Could not open tar file: " + tarry + 
                " The file could have been compressed as a another type and renamed.")
        return
    except struct.error:
        print "Warning: Could not extract tar properly: " + tarry


    # tar.extractall(directory)
    tar.close()
    os.remove(tarry)

def prepareTimeCheck(time):
    """Prepares user input timestamp for later use

    Takes in a timestamp in the format 'mm/dd/yy HH:MM' to be used as a due date for an assignment and
    converts it into a localized datetime object. This feature only works if the user has the pytz 
    module installed. 

    Args:
        time: duedate timestamp in format 'mm/dd/yy HH:MM'
    """
    if not findTime :
        print "\nModule pytz not found. To use the late submission checking feature, please install pytz.\n"
        return None

    duetime = datetime.strptime(time[0] + " " + time[1], "%m/%d/%y %H:%M")
    eastern = timezone('US/Eastern')
    duetime = eastern.localize(duetime)
    return duetime

class BadCSVError(RuntimeError):
    pass

class MismatchError(RuntimeError):
    pass

class AssignmentManager(object):
    """Manager to handle a given assignment submission and collection tool."""

    def extractBulk(self, zippy, students=[], directory=os.getcwd()):
        """Handle extraction of bulk submission zip file.

        Creates a list of paths out of the zip file. If a csv file was input, this list is shortened
        using a list from the csv file. All paths within the list are extracted into the given path.
        If no path is given, paths are extracted into the current working directory.
        
        Args:
            zippy: bulk submission zip file 
            students: list of student names to grade (optional)
            directory: directory to extract zip into (optional, default: working directory)

        Returns:
            Path of newly created directory with extracted files
        """

    def readCSV(self, csvfile):
        """Create a list of students to grade from input csv file.

        Reads through csv file and appends each student name to a list, creating a list of lists.
        List comprehension transforms this into a single list of student names and converts each
        name to uppercase. A delimiter of ';' is used to allow commas in students name (ex. Doe, John).

        Args:
            csvfile: csvfile with names of students to grade, delimited with ';'

        Returns:
            A list of student names to grade, all in uppercase.
        """

        students = []
        with open(csvfile, 'rb') as f :
            reader = csv.reader(f, delimiter=';')
            for row in reader :
                students.append(row)

        students = [s[0].rstrip() for s in students]

        return students

    def createPath(self, path):
        """Create the input path.

        As long as the entered path is not the current working directory, try to create the path. If 
        this fails, report error and handle collision.

        Args:
            path: path to be created (relative to cwd unless otherwise stated)
        """
        if os.path.abspath('.') != os.path.abspath(path):
            try:
                os.makedirs(path)
            except OSError:
                print "Error: Path already exists."
                self._handleCollision(path)

    def _handleCollision(self, path):
        """Poll user to overwrite path structure or cancel."""

        s = raw_input("Overwrite path structure for path: " + os.path.abspath(path) + " ? (Y/N) ")
        if s.upper() not in ['Y', 'YES']:
            sys.exit("User Abort. Collision on path: " + os.path.abspath(path))

        try:
            shutil.rmtree(path)
            os.makedirs(path)
        except OSError:
            sys.exit("Error: Unable to remove path: " + os.path.abspath(path))

class TSquare(AssignmentManager):
    """Manager to handle T-Square submissions."""

    @classmethod
    def execute(cls, zipfile, path, move, csv, time):
        """Run all neccessary fix up functions for T-Square submissions."""

        duetime = None
        if time:
            duetime = prepareTimeCheck(time)

        manager = cls(duetime)

        if csv :
            manager.students = manager.readCSV(csv)

        if path :
            manager.createPath(path)

        print "Extracting bulk submissions."
        directory = manager.extractBulk(zipfile, directory=path) 
        print "Renaming student folders" 
        manager.rename(directory)
        print "Moving submission files."
        late = manager.move(directory, move)

        if findTime and time and not late:
            print "\n\nNo Late Submissions \n "    
        if late :
            print "\n\nLate Submissions: "
            print '\n'.join(late)

    def __init__(self, duetime=None, students=None):
        self.duetime = duetime
        self.students = students

    def extractBulk(self, zippy, directory=None):
        """Handle extraction of bulk submission zip file."""

        directory = directory or os.getcwd()
        students = self.students or []

        zfile = zipfile.ZipFile(zippy)
        filelist = zfile.namelist()

        if students:
            filelist = self._findStudentsToExtract(filelist, students)

        for filename in filelist:
            zfile.extract(filename, directory)

        foldername, _ = filelist[0].split(os.sep, 1)
        return os.path.join(directory, foldername)
        
    def _findStudentsToExtract(self, filelist, students):
        """Given list of paths and students, return list of which paths to be extracted."""

        extractFiles = []
        for filename in filelist:
            student = filename.split(os.sep)[1].split('(')[0]
            if any([s.upper() == student.upper() for s in students]):
                extractFiles.append(filename)

        if not extractFiles:
            raise BadCSVError("Error: csv file matches no submissions.")
        return extractFiles

    def rename(self, directory):
        """Renames all student folders in directory to their names.

        Args:
            directory: directory with student submission folders
        """

        for fn in os.listdir(directory) :
            path = os.path.join(directory, fn)
            end = os.path.basename(os.path.normpath(path))
            new = str(os.path.dirname(path) + os.sep + end[:end.find('(')])
            os.rename(path, new)  

    def _getFilePaths(self, folder):
        """Returns file paths within a given folder."""

        for name in os.listdir(folder):
            if os.path.isfile(os.path.join(folder, name)):
                yield os.path.join(folder, name)

    def _checkTimeStamp(self, student, strayFiles):
        """Finds timestamp in student folder and returns the student and time if past given duedate."""

        if not self.duetime:
            return None

        for path in strayFiles:
            if os.path.basename(path) == 'timestamp.txt' :
                f = open(path, 'r')
                stamp = f.read()
                f.close()
                subtime = self.stripTime(stamp)

                if not subtime <= self.duetime :
                    fmt = '%m/%d/%Y  %H:%M'
                    return (subtime.strftime(fmt), student)
                return None
        print "Warning: No timestamp found for " + student

    def _moveFeedbackAttachments(self, source, dest):
        """Moves the Feedback Attachment(s) folder."""

        path = os.path.join(source, "Feedback Attachment(s)")
        if os.path.isdir(path):
            shutil.move(path, dest)      
  
    def _moveStrayFiles(self, source, strayFiles):
        """Creates a 'Text' directory and moves non-assignment files to it."""

        dest = os.path.join(source, "Text")
        if not os.path.exists(dest) :
            os.makedirs(dest)

        for path in strayFiles :
            shutil.move(path, dest)

        self._moveFeedbackAttachments(source, dest)

    def _extractSubmissionAttachments(self, studentFolder):
        """Moves assignment files out of Submission Attachment(s) folder, removes folder, and extracts files if needed."""
        
        source = os.path.join(studentFolder, "Submission attachment(s)")
        for files in os.listdir(source) :
            path = os.path.join(source, files)
            shutil.move(path, studentFolder)
        os.rmdir(source)
        extract(studentFolder)

    def _processStudentFolder(self, studentFolder):
        """Collects and moves stray files, checks for late status, and handles submission files."""
        
        strayFiles = list(self._getFilePaths(studentFolder))

        lateStatus = self._checkTimeStamp(os.path.basename(studentFolder), strayFiles)

        self._moveStrayFiles(studentFolder, strayFiles)
        self._extractSubmissionAttachments(studentFolder)

        return lateStatus

    def move(self, directory, out):
        """Processes each student folder.

        Goes through each folder in the given directory and processes it. If late status is being checked
        a list returned with the late students for that assignment. If out is specified, all student
        folders are moved outside of the base assignment directory. That directory is then removed.

        Args:
            directory: directory with student submission folders
            out: flag for moving the student folders out of the assignment directory

        Returns:
            late: list of students who submitted past the duedate. Empty if duetime is zero.
        """

        late = []
        for fn in os.listdir(directory) :
            studentFolder = os.path.join(directory, fn)
            if os.path.isdir(studentFolder) :
                lateStatus = self._processStudentFolder(studentFolder)
                if lateStatus:
                    late.append('  {timestamp}    {student}'.format(timestamp=lateStatus[0], student=(lateStatus[1])))

            if out :
                dest = os.path.dirname(directory)
                shutil.move(studentFolder, dest)
        if out :        
            os.rmdir(directory)

        return late

    def stripTime(self, stamp):
        """Converts the timestamp for the student's submission into a timezone aware time.

        Takes in the timestamp string and converts it into a datetime object. From there the
        datetime object is converted into a US/Eastern timezone aware time and returned. 

        Args:
            stamp: timestamp string of the format YYYYmmddHHMMsssss

        Returns:
            subtime: US/Eastern timezone aware submission time
        """
        rawtime = re.compile(r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})")
        timey = rawtime.search(stamp).groups()        # ('YYYY', 'mm', 'dd', 'HH', 'mm')
        timelist = list(timey)
        timey = '-'.join(timelist)
        timey = datetime.strptime(timey, "%Y-%m-%d-%H-%M")

        eastern = timezone('US/Eastern')
        subtime = timey.replace(tzinfo=pytz.utc).astimezone(eastern)
        subtime = eastern.normalize(subtime)
        return subtime

class Canvas(AssignmentManager):
    """Manager to handle Canvas submissions."""

    @classmethod
    def execute(cls, zipfile, roll, path, csv, section, move):
        """Run all neccessary fix up functions for Canvas submissions."""

        manager = cls(roll)
        directory = path or os.getcwd()

        if csv :
            manager.students = manager.readCSV(csv)
            print "Extracting students using list: {list}.".format(list=csv)

        if section:
            manager.students = manager.sections[section.upper()]
            print "Extracting only section {section}.".format(section=section.upper())

        if path :
            manager.createPath(path)

        tempPath = os.path.join(os.getcwd(), 'temp_extraction_folder')
        try:
            os.makedirs(tempPath)
        except OSError:
                print "Error: Temporary extraction path already exists."

        print "Extracting bulk submissions."
        manager.extractBulk(zipfile, directory=tempPath) 
        print "Moving and renaming submission files."
        folders = manager.move(tempPath, roll, zipfile, csv)
        print "Decompressing any compressed files."
        manager._inspectFolders(tempPath, folders, move)
        print "Moving submissions out of temporary folder."
        manager._moveAllFiles(directory, tempPath)
        shutil.rmtree(tempPath)
        
    def __init__(self, roll, students=None):
        self.roll, self.sections = self._createRollDict(roll)
        self.students = students

    def _createRollDict(self, roll):
        """Create a dictionary of the roll, mapping formated names ('lastfirstmiddle') to names."""

        roster = {}
        sections = {}
        with open(roll, 'rb') as f:
            reader = csv.reader(f, delimiter=',')
            reader.next()
            reader.next()
            for row in reader: 
                section = row[3].rsplit(' ', 1)[1].upper()
                squishedName = re.sub(r'\W+', '', row[0]).upper()
                sections.setdefault(section, list()).append(row[0])
                roster[squishedName] = row[0]

        return (roster, sections)

    def extractBulk(self, zippy, directory=None):
        """Handle extraction of bulk submissions zip file."""

        directory = directory or os.getcwd()
        students = self.students or []

        zfile = zipfile.ZipFile(zippy)
        filelist = zfile.namelist()

        if students:
            filelist = self._findStudentsToExtract(filelist, students)

        for filename in filelist:
            zfile.extract(filename, directory)

    def _findStudentsToExtract(self, filelist, students):
        """Given list of paths and students, return list of which paths to be extracted."""

        extractFiles = []
        for filename in filelist:
            squishedName, _ = self._parseFileName(filename)

            if squishedName.upper() in self.roll.keys():
                student = self.roll[squishedName.upper()] 
            else:
                print "Warning: {student} not found in roll. Skipping.".format(student=squishedName)
                continue

            if any([s.upper() == student.upper() for s in students]):
                extractFiles.append(filename)

        if not extractFiles:
            raise BadCSVError("Error: csv file matches no submissions.")
        return extractFiles

    def _processStudentFolder(self, studentFolder):
        """Collects and moves stray files, checks for late status, and handles submission files."""

        strayFiles = list(self._getFilePaths(studentFolder))

        lateStatus = self._checkTimeStamp(os.path.basename(studentFolder), strayFiles)

        self._moveStrayFiles(studentFolder, strayFiles)
        self._extractSubmissionAttachments(studentFolder)

        return lateStatus

    def move(self, directory, roster, submissions, csv):
        """Moves files into the correct student folder.

        Moves all files starting with a student's name into a folder of their name. Creates a student folder
        if there is not already one and overwrites the folder if there was one to begin with. Files are trimmed,
        removing student name and resubmission numbers. If a filename collision is detected, user is warned and
        must move that student's files manually.

        Args:
            directory: directory with student submission folders

        Returns:
            createdFolders: set of student folder names that were created
        """

        createdFolders = set()
        for filename in os.listdir(directory):
            if os.path.isdir(os.path.join(directory, filename)):
                continue

            studentName, studentFile = self._parseFileName(filename)
                       
            if studentName.upper() in self.roll.keys():
                student = self.roll[studentName.upper()]
                
                studentFolder = self._createStudentFolder(directory, student, createdFolders)
                newFilename = self._renameFile(studentFile)
                newPath = os.path.join(studentFolder, newFilename)

                if os.path.exists(newPath):
                    print ("Warning: {student} has a filename collision on '{file}'."
                            " The student may have named files using the format 'file-1.txt' on purpose."
                            " Please manually check, move, and rename their files.".format(student=student, file=newFilename))
                    continue
                shutil.move(os.path.join(directory, filename), newPath)

        return map(os.path.abspath, createdFolders)

    def _createStudentFolder(self, directory, student, createdFolders):
        """Creates a folder with student's name, overwriting it if the folder already exists."""

        studentFolder = os.path.join(directory, student)
        if os.path.exists(studentFolder):
            if studentFolder not in createdFolders:
                shutil.rmtree(studentFolder)
                os.makedirs(studentFolder)
        else:
            os.makedirs(studentFolder)
        createdFolders.add(studentFolder)
        return os.path.abspath(studentFolder)

    def _getMatch(self, student):
        """Try to match student string with pattern and stop when the pattern is found."""
        
        for p in _student_file_patterns:
            m = p.match(student)
            if m:
                return m

    def _parseFileName(self, filename):
        """Parse a Canvas filename into student name and submission filename."""

        match = self._getMatch(filename)
        if not match:
            raise MismatchError('Pattern not matched on: {filename}'.format(filename=filename))
        student = match.group('student').replace('_','')
        newFilename = match.group('filename')

        return (student, newFilename)

    def _renameFile(self, filename):
        """Rename file into correct format, discarding added '-#'s Canvas adds to resubmissions."""

        tempfilename = re.split('-\d+\.', filename)
        if len(tempfilename) > 1:
            filename = '.'.join(tempfilename)
        return filename

    def _inspectFolders(self, path, folderList, move):
        """Looks through each student folder in the directory and decompresses any compressed files."""

        for folder in os.listdir(path):
            folderPath = os.path.abspath(os.path.join(path, folder))
            if os.path.isdir(folderPath) and folderPath in folderList:
                extract(os.path.join(path, folder))
                if move == '1':
                    self._flattenOneLevel(folderPath)
                if move == 'all':
                    self._flattenAllLevels(folderPath)

    def _flattenOneLevel(self, source):
        """Flatten the source directory's structure by one level."""

        for directory in os.listdir(source):
            currentFolder = os.path.join(source, directory)
            if os.path.isdir(currentFolder):
                for file in os.listdir(currentFolder):
                    shutil.move(os.path.join(currentFolder, file), os.path.join(source, file))

                try:
                    shutil.rmtree(currentFolder)
                except OSError:
                    print "Error: Unable to remove path: " + os.path.abspath(path)

    def _flattenAllLevels(self, source):
        """Flatten the source directory's struture by all levels."""

        for root, directories, files in os.walk(source):
            for file in files:
                filePath = os.path.join(root, file)
                destination = os.path.join(source, file)
                if filePath != destination:
                    shutil.move(filePath, destination)

        for directory in os.listdir(source):
            if os.path.isdir(os.path.join(source, directory)):
                shutil.rmtree(os.path.join(source,directory))

    def _moveAllFiles(self, destination, source):
        """Moves every file in the source directory to the destination directory."""

        for directory in os.listdir(source):
            if os.path.isdir(os.path.join(source, directory)):
                destPath = os.path.join(destination, directory)
                shutil.move(os.path.join(source, directory), destPath)



def main(sysargs):
    parser = argparse.ArgumentParser(description='Script to extract student submissions from a bulk submissions zip.'
                                    ' The submission manager must be chosen (TSquare, Canvas). If using Canvas, the class'
                                    ' roster (from Canvas) must be included as well. Note that with Canvas only csv or'
                                    ' section may be used at a time. If both are used, section will override csv.')
    parser.add_argument('bulksubmission', help='bulk submissions zip file', metavar='submissions.zip')

    subparsers = parser.add_subparsers(title='Submission Managers')

    t2 = subparsers.add_parser('tsquare', help='Submission files downloaded from T-Square')
    t2.add_argument('-c', '--csv', help='csv file of particular students to extract (semicolon seperated)')
    t2.add_argument('-p', '--path', help='extraction path for bulk submissions zip')
    t2.add_argument('-m', '--move', help='move student folders out of archive root folder', action='store_true')
    t2.add_argument('-t', '--time', help=('Flag late submissions past due date. '
                                          'Checks submissions using the US/Eastern timezone. Requires pytz to use.'), 
                                        nargs='+', action=requiredLength(2), metavar=('mm/dd/yy', 'hh:mm'))
    t2.set_defaults(action='tsquare')

    canv = subparsers.add_parser('canvas', help='Submission files downloaded from Canvas')
    canv.add_argument('roll', help='csv file of class roll from Canvas (comma seperated)')
    canv.add_argument('-c', '--csv', help='csv file of particular students to extract (semicolon seperated)')
    canv.add_argument('-p', '--path', help='extraction path for bulk submissions zip')
    canv.add_argument('-s', '--section', help='grading section to extract from submissions')
    canv.add_argument('-m', '--move', help=('move extracted files within student folder out' 
                    ' one level or all levels (completely collapse directory structure)'), 
                    choices=['1', 'all'])
    canv.set_defaults(action='canvas')

    if len(sysargs) == 1 :
        parser.print_help()
       
        ## Source: http://stackoverflow.com/questions/20094215/argparse-subparser-monolithic-help-output
        # retrieve subparsers from parser
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)]
        # there will probably only be one subparser_action,
        # but better save than sorry
        for subparsers_action in subparsers_actions:
            # get all subparsers and print help
            for choice, subparser in subparsers_action.choices.items():
                print("\nSubmission Manager '{}'".format(choice))
                print(subparser.format_help())
        ##
        sys.exit(1)

    args = parser.parse_args(sysargs[1:])

    if args.action == "tsquare":
        TSquare.execute(args.bulksubmission, args.path, args.move, args.csv, args.time)
    elif args.action == "canvas":
        Canvas.execute(args.bulksubmission, args.roll, args.path, args.csv, args.section, args.move)

    print "\nDone"


if __name__ == '__main__' :
    main(sys.argv)