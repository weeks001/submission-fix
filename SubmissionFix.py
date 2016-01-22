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
    if not findTime :
        print "\nModule pytz not found. To use the late submission checking feature, please install pytz.\n"
        return None

    duetime = datetime.strptime(time[0] + " " + time[1], "%m/%d/%y %H:%M")
    eastern = timezone('US/Eastern')
    duetime = eastern.localize(duetime)
    return duetime

class AssignmentManager(object):

    def extractBulk(self, zippy, students=[], directory=os.getcwd()):
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

    def readCSV(self, csvfile):
        """Create a list of students to grade from input csv file.

        Reads through csv file and appends each student name to a list, creating a list of lists.
        List comprehension transforms this into a single list of student names and converts each
        name to uppercase (since T-Square sometimes has student names in uppercase). 

        Args:
            csvfile: csvfile with names of students to grade

        Returns:
            A list of student names to grade, all in uppercase.
        """

        students = []
        with open(csvfile, 'rb') as f :
            reader = csv.reader(f, delimiter=';')
            for row in reader :
                students.append(row)

        #convert list[list[]] to list[], convert names to uppercase
        students = [s[0].upper() for s in students]

        return students

    def createPath(self, path):
        if os.path.abspath('.') != os.path.abspath(path):
            try:
                os.makedirs(path)
            except OSError:
                print "Error: Path already exists."
                self._handleCollision(path)

    def _handleCollision(self, path):
        #ask user to overwrite path, enter new path, or cancel
        s = raw_input("Overwrite path structure for path: " + os.path.abspath(path) + " ? (Y/N)")
        if s.upper() not in ['Y', 'YES']:
            sys.exit("User Abort. Collision on path: " + os.path.abspath(path))

        try:
            shutil.rmtree(path)
            os.makedirs(path)
        except OSError:
            sys.exit("Error: Unable to remove path: " + os.path.abspath(path))

class TSquare(AssignmentManager):

    @classmethod
    def execute(cls, zipfile, path, move, csv, time):
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

        #print late submissions
        if findTime and time and not late:
            print "\n\nNo Late Submissions \n "    
        if late :
            print "\n\nLate Submissions: "
            print '\n'.join(late)

    def __init__(self, duetime=None, students=None):
        self.duetime = duetime
        self.students = students

    def extractBulk(self, zippy, directory=None):
        # print "subfix extract: " + os.getcwd()
        # print "subfix extract dir: " + directory
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
        #return list of files to extract
        extractFiles = []
        for filename in filelist:
            student = filename.split(os.sep)[1].split('(')[0]
            if any([s == student.upper() for s in students]):
                extractFiles.append(filename)
        return extractFiles

    def rename(self, directory):
        """Renames all student folders to their names

        Renames student folders in the given directory by removing the hashcode nonsense at the 
        end of the folder name. 

        Args:
            directory: directory with student submission folders
        """

        for fn in os.listdir(directory) :
            path = os.path.join(directory, fn)
            end = os.path.basename(os.path.normpath(path))
            new = str(os.path.dirname(path) + os.sep + end[:end.find('(')])
            os.rename(path, new)  

    def _getFilePaths(self, folder):
        for name in os.listdir(folder):
            if os.path.isfile(os.path.join(folder, name)):
                yield os.path.join(folder, name)

    def _checkTimeStamp(self, student, strayFiles):
        if not self.duetime:
            return None

        for path in strayFiles:
            #check to see if the student's submission was late
            if os.path.basename(path) == 'timestamp.txt' :
                f = open(path, 'r')
                stamp = f.read()
                f.close()
                subtime = self.stripTime(stamp)

                if not subtime <= self.duetime :
                    fmt = '%m/%d/%Y  %H:%M'
                    return " " + subtime.strftime(fmt) + "    " + student
        print "Warning: No timestamp found for " + student

    def _moveFeedbackAttachments(self, source, dest):
        path = os.path.join(source, "Feedback Attachment(s)")
        if os.path.isdir(path):
            shutil.move(path, dest)      
  
    def _moveStrayFiles(self, source, strayFiles):
        dest = os.path.join(source, "Text")
        if not os.path.exists(dest) :
            os.makedirs(dest)

        for path in strayFiles :
            shutil.move(path, dest)

        self._moveFeedbackAttachments(source, dest)

    def _extractSubmissionAttachments(self, studentFolder):
        #move submission attachments out of folder into student name folder and extract
        source = os.path.join(studentFolder, "Submission attachment(s)")
        #check if folder exists
        for files in os.listdir(source) :
            path = os.path.join(source, files)
            shutil.move(path, studentFolder)
        os.rmdir(source)
        extract(studentFolder)

    def _processStudentFolder(self, studentFolder):
        #move timey, comments, feedbackText, submissionText to Text folder
        strayFiles = list(self._getFilePaths(studentFolder))

        lateStatus = self._checkTimeStamp(os.path.basename(studentFolder), strayFiles)

        self._moveStrayFiles(studentFolder, strayFiles)
        self._extractSubmissionAttachments(studentFolder)

        return lateStatus

    def move(self, directory, out):
        """Moves all files in "Submission attachment(s)" up a level

        All files in student's main folder (timestamp.txt, comments.txt, etc) are moved to the 
        newly created directory Text. If duetime was set, the submission time in timestamp.txt 
        will be compared to the duetime. If the submission time is after the duetime, the 
        student's name and submission time will be added to the late list, to be returned at the
        end. "Feedback Attachment(s)" folder is also moved to Text. All files within "Submission 
        attachment(s)" are moved up to the student's main folder. Empty "Submission attachment(s)" 
        folder is deleted. extract() is called to extract any zip or tar files the student submitted. 
        If "out" is true, the student folders will be moved out the root arcive folder and up one 
        level in the directory tree. Useful for having fewer nested folders if you specify an 
        extraction folder.

        Args:
            directory: directory with student submission folders
            out: flag for moving the student folder out of the archive folder
            duetime: US/Eastern timezone aware due date time to compare submission times to

        Returns:
            late: list of students whose submissions where after the due date. Empty if duetime is zero.
        """

        late = []
        for fn in os.listdir(directory) :
            studentFolder = os.path.join(directory, fn)
            if os.path.isdir(studentFolder) :
                lateStatus = self._processStudentFolder(studentFolder)
                if lateStatus:
                    late.append(lateStatus)

            #move student folder out of the root archive folder
            if out :
                #check if directory has slash
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
        rawtime = re.compile(r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})")        #YYYYmmddHHMMsssss
        timey = rawtime.search(stamp).groups()        # ('YYYY', 'mm', 'dd', 'HH', 'mm')
        timelist = list(timey)
        timey = '-'.join(timelist)
        timey = datetime.strptime(timey, "%Y-%m-%d-%H-%M")

        eastern = timezone('US/Eastern')
        subtime = timey.replace(tzinfo=pytz.utc).astimezone(eastern)
        subtime = eastern.normalize(subtime)
        return subtime

def main(sysargs):
    parser = argparse.ArgumentParser(description='Script to extract student submissions from bulk zip.')
    parser.add_argument('bulksubmission', help='bulk zip of student submissions')
    parser.add_argument('-c', '--csv', help='student list csv file (semicolon seperated)')
    parser.add_argument('-p', '--path', help='extraction path for bulk submissions zip')
    parser.add_argument('-m', '--move', help='move student folders out of archive root folder', action='store_true')
    parser.add_argument('-t', '--time', help=('Flag late submissions past due date. Requires due date and time. '
                                              'Checks submissions using the US/Eastern timezone. Requires pytz to use.'), nargs='+', action=requiredLength(2), metavar=('mm/dd/yy', 'hh:mm'))
    # parser.add_argument('-f', '--files', help='copy grading files into students' submission', )

    if len(sysargs) == 1 :
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args(sysargs[1:])

    TSquare.execute(args.bulksubmission, args.path, args.move, args.csv, args.time)

    print "\nDone"


if __name__ == '__main__' :
    main(sys.argv)