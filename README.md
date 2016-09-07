# Submission Fix

Script for extracting and organizing student submissions. Works with 
both T-Square and Canvas. There are different options depending on the
submission manager your class is using. Both allow for extracting only
specific students and into a given directory. The script will 
automatically extract any zip, tar, and tar.gz files that students submit.

Originally for use in CS 2110 but should work for most CS classes at Georgia 
Tech.

## Getting Started

To use this script, all you need is Python 2.7 and the 
SubmissionFix.py file.

### Optional: Install pytz

Note that if your class is using T-Square, you have the option to 
automatically check for late submissions by providing a due time. To use 
this feature, the module `pytz` must be installed. The easiest way to do 
this is to use the `pip` package manager.

## Features

Available features differ for each submission manager based on how that 
manager holds student information. For both managers, the script is capable of
handling badly compressed files (student submits a zip file renamed to 
a tar extension or compresses a folder named "."). 

### T-Square

* Extract certain students only by providing a semicolon 
delimited csv file. The csv must list the students' names as they appear
on T-Square (ex. `Last, First`). This is useful for extracting only your 
section or students for demos.

* User can provide a particular path for submissions to be extracted to. 
If destination directory already exists, user will be prompted to overwrite
it. Else, the destination directory is created.

*  After extracting student submission files from any compressed files, the
directory structure for the student can be flattened by one or all levels. 

* Automatically check for late submissions by providing a due date and time.
A list of late submissions is printed to the terminal at the end of the script.

* Automatically check for no submissions. A list of students who did not submit
any files will be printed to the terminal at the end of the script.

### Canvas

* Extract both normal assignment files and quiz based submissions (the file 
name formats are different for each) into well organized student folders.

* Extract certain students only by providing a semicolon 
delimited csv file. The csv must list the students' names as they appear
on Canvas. If the student has multiple names listed on the roster all of these
must be included for the extraction to work (ex. `Last, First Middle`). This
is useful for extracting students for demos.

* User can provide a particular path for submissions to be extracted to. 
If destination directory already exists, user will be prompted to overwrite
it. Else, the destination directory is created.

* User can specify that only a specific section is extracted from the zip file.
Note that if, for some reason, a student is in two different sections then the 
student will be extracted if either section is entered. 

*  After extracting student submission files from any submitted archives, the
directory structure can be flattened by one or all levels.


## Usage and Process

For full usage help run `python SubmissionFix.py` or 
`python SubmissionFix.py -h`for condensed help dialog. Usage differs with 
each submission manager. As such, the submission manager must be specified
with each use.

### T-Square

General usage is:
```
python SubmissionFix.py submissions.zip tsquare [-c students.csv] 
[-p path/to/destination] [-m {1,all}] [-t mm/dd/yy hh:mm]
```
All arguments in square brackets are optional. The `submissions.zip` file is the 
submissions downloaded from T-Square and can be either the full class or your
section. The zip and the `tsquare` submission manager choice are required. 
All other arguments can be specified in any order and can all be used together.

#### Normal usage

If only the required arguments are used, the script will extract every student 
folder from the zip file into a temporary folder. Then it will rename the 
student folders, discarding the hash on each. Next it will go through each 
student folder and move any extra files that T-Square included in the 
download to a newly created "Text" folder. Any files the student submitted are 
moved out of T-Square's "Submission Attachment(s)" folder and into their base
folder. Next it extracts any compressed zip, tar, or tar.gz files. Finally, all
student folders are moved out of the temporary folder into the directory the 
script was run in (overwriting any student folders of the same name that already
exist). If there were any students that did not submit any files, they will be 
listed as "No Submissions" at the end.

#### -c CSV

When a csv is used, the script uses the same process as normal except that it will
compare the student folders in the submissions.zip to those listed in the csv 
file. It will only extract those students listed in the csv from the 
submissions.zip and then continue the script as normal.

#### -p PATH

When a path is specified, the script still makes a temporary folder for 
extractions but will move all student folders into the specified path at the end, 
instead of into the folder the script was run from. If the specified destination
folder exists, the script will prompt for overwrite. If not, it will create that
folder.

#### -m MOVE

**Possible options are: 1, all**

As mentioned in the Features section above, the move command will move each 
student's submitted files and flatten the directory structure within the student's folder by either by one level or all levels. The move argument will
not affect the created "Text" folder that stores extra files from T-Square.

For examples, look below.

#### -t TIME

**Note: This feature requires the `pytz` module.**

**Time format must be `mm/dd/yy hh:mm` where `hh:mm` is in military (24 hour) time.**

The time argument will create a datetime object out of the user given due date 
and compare it to each student's submission time stamp found in timestamp.txt.
The time stamp that T-Square creates does not inherently include timezone 
information. If you see a discrepancy between submission time posted on T-Square 
and the timestamp.txt T-Square creates for each student, this is why.
Because Python's normal time library cannot handle timezones well, 
pytz is used to convert the time stamp to a proper timezone aware time and compare
it to the due date. The rest of the script functions as normal and any late 
submissions are printed to the terminal at the end.

Be aware that a student will not have a timestamp.txt if they did not submit the
assignment. If you use the full class submissions.zip, this is likely to produce 
a warning for the TAs and Instructor (they may also show up under No Submissions). 


### Canvas

General usage is:
```
python SubmissionFix.py submissions.zip canvas roll.csv [-c students.csv] 
[-p path/to/destination] [-m {1,all}]
```
All arguments in square brackets are optional. The `submissions.zip` file is the 
submissions downloaded from Canvas while `roll.csv` is the comma 
separated roster csv from Canvas. These csv files and the `canvas` submission 
manager choice are required. All other arguments can be specified in any 
order and can all be used together.

#### Normal Usage

Because Canvas does not separate student submissions by folder like T-Square 
and instead renames the files, the roster must be used to compare each file
name to student names. Under normal usage with no extra arguments, the script
extracts all files to a temporary folder and then compares student names to
file names. It creates a student folder for all students who submitted files 
and moves their files into their respective folder (renaming each files to be
its submitted version, without all the junk Canvas tacked on). It then extracts
any compressed files a student submitted. Finally, it moves all student folders
out of the temporary extraction folder and into the directory the script was
run from. If any student folders of the same name already exist, they are 
overwritten.

#### -c CSV

When a csv is used, the script uses the same process as normal except that it will
only extract files from students whose names correspond to those listed in the given
csv file. Only these student folders will be created and no others. Also, if a student
on the list did not submit the assignment, their folder will not be created (same as
the normal scenario).

#### -p PATH

When a path is specified, the script still makes a temporary folder for 
extractions but will move all student folders into the specified path at the end, 
instead of into the folder the script was run from. If the specified destination
folder exists, the script will prompt for overwrite. If not, it will create that
folder.

#### -m MOVE

**Possible options are: 1, all**

As mentioned in the Features section above, the move command will move each 
student's submitted files and flatten the directory structure within the student's folder by either by one level or all levels. 

For examples, see below.

## Examples

### -m MOVE
Let's say a student submits a zip file with the following directory structure:
```
HW01.zip
  - Homework 1 (folder)
      - hw1.asm
      - Assignment Resources (folder)
          - HW1.pdf
          - hw1.txt
```
Normally, the files would be extracted into the student folder as:
```
Homework 1 (folder)
  - hw1.asm
  - Assignment Resources (folder)
      - HW1.pdf
      - hw1.txt
```
When the directory structure is flattened once, it looks like this:
```
hw1.asm
Assignment Resources (folder)
  - HW1.pdf
  - hw1.txt
```
When the directory structure is flattened completely, it looks like this:
```
hw1.asm
HW1.pdf
hw1.txt
```
Flattening the structure once is useful for students that compress a folder
instead of just the files within the folder. Flattening the structure 
completely can be useful for assignments with lots of scattered files that
need to be in the same folder (such as Game Boy Advance homeworks).

## Running Tests

Tests are provided for checking functionality of the script. Most tests are integration
tests that set up a particular file structure for the tests to run in. A few are unit 
tests. To run the tests, make sure that the SubmissionFix.py file and all associated 
testing resources (the various testing_sets) are in the same folder as IntegTests.py and
UnitTests.py. 

For Integration Tests, run `python IntegTests.py`.

Notice that the T-Square tests and Canvas tests are run separately from each other.

For Unit Tests, run `python UnitTests.py`.

Tests that use pytz and the time modules will take slightly longer than most other
tests.