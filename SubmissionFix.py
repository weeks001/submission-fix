#!/usr/bin/env python
from __future__ import with_statement
from datetime import datetime, date

"""
This is an awesome script to clean up the bulk submission zip file into a directory with 
nicely named, (mostly) unnested folders. If specified, it will only extract certain students'
submissions and/or extract submissions to a specified directory. Note, it will only extract 
into an empty directory. This way it won't accidently overwrite already extracted submissions.
"""

__author__ = "Marie Weeks"
__version__ = "1.9"

import os
import sys
import csv
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


#TODO: handle directory collisions by prompting user
#TODO: copy in grading files when extracting
#TODO: report no submissions (check if Submitted Files directory is empty)

#TODO: look into 7zip functionality
#TODO: collapse directories with only one folder inside and no files

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

    zfile = zipfile.ZipFile(zippy)
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

    tar = tarfile.open(tarry)
    tar.extractall(directory)
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

        students = [s[0] for s in students]

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

        s = raw_input("Overwrite path structure for path: " + os.path.abspath(path) + " ? (Y/N)")
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
            if any([s == student.upper() for s in students]):
                extractFiles.append(filename)
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
        "Creates a 'Text' directory and moves non-assignment files to it."

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
    def execute(cls, zipfile, roll, path, csv):
        """Run all neccessary fix up functions for Canvas submissions."""
        # rolldict = _createRollDict(roll)
        # manager = cls(rolldict)
        manager = cls(roll)
        directory = path or os.getcwd()

        if csv :
            manager.students = manager.readCSV(csv)

        if path :
            manager.createPath(path)

        print "Extracting bulk submissions."
        manager.extractBulk(zipfile, directory=path) 
        print "Moving and renaming submission files."
        folders = manager.move(directory)
        print "Decompressing any compressed files."
        manager._inspectFolders(directory, folders)

        
    def __init__(self, roll, students=None):
        self.roll = self._createRollDict(roll)
        self.students = students

    def _createRollDict(self, roll):
        """Create a dictionary of the roll, mapping formated names ('lastfirstmiddle') to names."""

        students = {}
        rolllist = self.readCSV(roll)

        for name in rolllist:
            squishedName = name.replace(',', '').replace(' ', '')    
            students[squishedName.upper()] = name

        return students

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
            student = self.roll[filename.split('_')[0].upper()] #[lastfirstmiddle] = first middle last
            if any([s.upper() == student.upper() for s in students]):
                extractFiles.append(filename)
        return extractFiles

    #TODO: change function
    def _processStudentFolder(self, studentFolder):
        """Collects and moves stray files, checks for late status, and handles submission files."""
        strayFiles = list(self._getFilePaths(studentFolder))

        lateStatus = self._checkTimeStamp(os.path.basename(studentFolder), strayFiles)

        self._moveStrayFiles(studentFolder, strayFiles)
        self._extractSubmissionAttachments(studentFolder)

        return lateStatus

    #TODO: change function
    def move(self, directory):
        """
        """

        createdFolders = set()
        for filename in os.listdir(directory):
            if filename.split('_')[0].upper() in self.roll.keys():
                student = self.roll[filename.split('_')[0].upper()]
                studentFolder = os.path.join(directory, student)

                if os.path.exists(studentFolder):
                    if studentFolder not in createdFolders:
                        shutil.rmtree(studentFolder)
                        os.makedirs(studentFolder)
                else:
                    os.makedirs(studentFolder)
                    
                createdFolders.add(studentFolder)


                _, newFilename = filename.rsplit('_', 1)
                tempfilename = re.split('-\d+\.', newFilename)
                if len(tempfilename) > 1:
                    newFilename = '.'.join(tempfilename)
                    # print newFilename

                newPath = os.path.join(studentFolder, newFilename)
                if os.path.exists(newPath):
                    print ("Warning: {student} has a filename collision on '{file}'."
                            " The student may have named files using the format 'file-1.txt' on purpose."
                            " Please manually check, move, and rename their files.".format(student=student, file=newFilename))
                    continue
                shutil.move(os.path.join(directory, filename), newPath)
        return createdFolders

    # def _renameFile(self, filename):
    #     """Renames a file in format 'lastfirstmiddle_0000_0000_file-1.txt' to 'file.txt'."""
    #     _, newFilename = filename.rsplit('_', 1)
    #     #look for -#.  "-\d+\."
    #     rawtime = re.compile(r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})")

    def _inspectFolders(self, path, folderList):
        """Looks through each student folder in the directory and decompresses any compressed files."""

        for folder in os.listdir(path):
            if os.path.isdir(folder) and " ".join(folder.split('_')) in folderList:
                extract(os.join.path(path, folder))


def main(sysargs):
    parser = argparse.ArgumentParser(description='Script to extract student submissions from bulk zip.')
    parser.add_argument('bulksubmission', help='bulk submissions zip file', metavar='submissions.zip')
    # parser.add_argument('manager', help='assignment manager submissions were downloaded from', choices=['tsquare', 'canvas'])
    # parser.add_argument('-c', '--csv', help='student list csv file (semicolon seperated)')
    # parser.add_argument('-p', '--path', help='extraction path for bulk submissions zip')
    # parser.add_argument('-m', '--move', help='move student folders out of archive root folder', action='store_true')
    # parser.add_argument('-t', '--time', help=('Flag late submissions past due date. Requires due date and time. '
    #                                           'Checks submissions using the US/Eastern timezone. Requires pytz to use. [TSqaure Only]'), 
    #                                     nargs='+', action=requiredLength(2), metavar=('mm/dd/yy', 'hh:mm'))
    
    subparsers = parser.add_subparsers(title='Submission Managers')

    t2 = subparsers.add_parser('tsquare', help='Submission files downloaded from T-Square')
    t2.add_argument('-c', '--csv', help='student list csv file (semicolon seperated)')
    t2.add_argument('-p', '--path', help='extraction path for bulk submissions zip')
    t2.add_argument('-m', '--move', help='move student folders out of archive root folder', action='store_true')
    t2.add_argument('-t', '--time', help=('Flag late submissions past due date. Requires due date and time. '
                                              'Checks submissions using the US/Eastern timezone. Requires pytz to use.'), 
                                        nargs='+', action=requiredLength(2), metavar=('mm/dd/yy', 'hh:mm'))
    t2.set_defaults(action='tsquare')

    canv = subparsers.add_parser('canvas', help='Submission files downloaded from Canvas')
    canv.add_argument('roll', help='csv file of class roll from Canvas (students only, semicolon seperated)')
    canv.add_argument('-c', '--csv', help='student list csv file (semicolon seperated)')
    canv.add_argument('-p', '--path', help='extraction path for bulk submissions zip')
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
        Canvas.execute(args.bulksubmission, args.roll, args.path, args.csv)

    print "\nDone"


if __name__ == '__main__' :
    main(sys.argv)