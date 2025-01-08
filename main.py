#Edited January 8, 2024 to insert zeroes in place of blanks in output of report.

import os
import csv
import operator
import re
import yaml
import smtplib, ssl
import json

HEADERS = ['lender_institution', 'borrower_institution', 'full_name', 'user_email', 'expiry_date', 'remaining_amount', 'active_loan_count']
CONFIGFILE = "config.yaml"

def changeInputFile(oldfile):
    stringlist = oldfile.split("/")
    filename = stringlist[-1]
    newfile = "old_" + filename
    newabsfile = oldfile.replace(filename, newfile)
    os.rename(oldfile, newabsfile)
    return

# Function to set up using YAML file:
# Returns dictionary
def setUpYaml(configfile):
    data = {"error": "Something went horribly wrong with your config file"}
    with open(configfile) as stream:
        try:
            #print(yaml.safe_load(stream))
            data = yaml.safe_load(stream)
            #print(data['email_subject'])
        except yaml.YAMLError as exc:
            print(exc)
    return data


# A function to create a list of matching files within a repository
# Returns a list of filenames with absolute paths that haven't been previously processed (ie. no
# old_ prefix.
def match(directory):
    matches = []
    # Step 1: Obtain all directories matching the pattern:
    for root, dirnames, filenames in os.walk(directory):
        for dirname in dirnames:
            pattern = re.compile("al-*")
            if pattern.match(dirname):
                # print(dirname)
                # print(root)
                # print(root + '/' + dirname)
                holdingdir = root + '/' + dirname
                # Step 2: Grab all the files in this directory and shove them in the matches list.
                for root2, dirnames2, filenames2 in os.walk(holdingdir):
                    #print(filenames2)
                    #print(root2)
                    for filename2 in filenames2:
                        print(filename2)
                        pattern = re.compile("old_*")
                        if not pattern.match(filename2):
                            matches.append(root2 + '/' + filename2)
    print(matches)
    return matches

#This function checks the csv files output in match()
#Ask Alex if we have to add a user input option to check graduation date (and ensure all the reports added ARE, in
# fact, for the set of users graduating that semester, etc.
# Accept list of matches from match() and check to make sure they're actually the correct format, etc.
def checkFileHeaders(matcheslist):
    errorfile = open("Logs/errorfile.txt", 'a')
    #print(matcheslist)
    correctfiles = []
    for filename in matcheslist:
        filetype = os.path.splitext(filename)[-1]
        #print(filetype)
        if filetype == '.csv':
            with open(filename, encoding='latin-1') as csv_file1:
                csv_reader = csv.reader(csv_file1, delimiter=',')
                headers = next(csv_reader)
                headers[0] = headers[0].replace('ï»¿','') #remove byte order mark
                if headers != HEADERS:
                    errorfile.write(filename + "\t The headers in this file do not match those of the expected analytics report.  Did you provide the correct file?\n")
                   # TODO: add conversion option from xlsx
                correctfiles.append(filename)
            csv_file1.close()
        else:
            errorfile.write(filename + "\t The extension of this file is not as expected.  Did you provide the correct file?\n")
    errorfile.close()
    #print(correctfiles)
    return correctfiles

# This function creates empty report files for each school
# Uses file containing university names
# Returns a dictionary relating which file corresponds to which institution
def createReportFiles():
    filedict = {}
    with open('AFNSchools.csv', encoding='latin-1') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            school = row[0]
            location = 'OutputFiles/' + school.strip().replace('/', '').replace(' ', '_') + '.csv'
            filedict[school] = location
    csv_file.close()
    #print(filedict)
    return filedict

# This function creates empty report files for each school
# Uses json file
def createReportFiles2():
    file = open("AFNSchools.json")
    datadict = json.load(file)
    print(datadict)
    return datadict

# Replaces empty spaces in input with zeroes where appropriate (entries 4 & 5)
# @row  A row of data from the original csv
def insertZero(row):
    if row[5] == "":
        row[5] = 0
    if row[6] == "":
        row[6] = "0"
    return row


# Receives the filedict created in the first function
# Iterates through the input files and sorts all borrowers from one institution into that institution's file
# Also receives the list of matches created in match(directory)
def populateReport(filedict):
    data = setUpYaml(CONFIGFILE)
    directorypath = data["scriptpath"]
    correctfiles = checkFileHeaders(match(directorypath))
    #print(correctfiles)
    for filename in correctfiles: # provides string filename as absolute path
        line_count = 0
        with open(filename, encoding='latin-1') as csv_file1:
            csv_reader = csv.reader(csv_file1, delimiter=',')
            for row in csv_reader:
                if line_count > 0:
                    lender = row[0]
                    borrower = row[1]
                    # open appropriate write file:
                    if borrower != "":
                        with open(filedict[borrower], 'a', encoding='latin-1', newline='\n') as writefile:
                            csv_writer = csv.writer(writefile, delimiter='\t')
                            # 01/08/24: Edit the row being written to csv_writer here:
                            csv_writer.writerow(insertZero(row))
                        writefile.close()
                    else:
                        with open("OutputFiles/errors.csv", 'a', encoding='latin-1', newline='\n') as writefile:
                            csv_writer = csv.writer(writefile, delimiter='\t')
                            csv_writer.writerow(row)
                        writefile.close()
                line_count += 1
            csv_file1.close()
        #print(filename)
        #changeInputFile(filename)

# Goes through the reports in OutputFiles
def sortReportsByEmail():
    for file in os.listdir('OutputFiles'):
        filename = os.fsdecode(file)
        line_count = 0
        with open('OutputFiles/' + filename, "r", encoding='latin-1') as csv_file1:
            csv_reader = csv.reader(csv_file1, delimiter='\t')
            with open('SortedFiles/' + filename, "w", newline='', encoding='latin-1') as writefile:
                csv_writer = csv.writer(writefile, delimiter='\t')
                # headers = next(csv_reader)
                # blank = next(csv_reader)
                sorted_rows = sorted(csv_reader, key=operator.itemgetter(3))
                csv_writer.writerow(["lender_institution","borrower_institution","full_name","user_email","expiry_date","remaining_amount","active_loan_count"])
                csv_writer.writerows(sorted_rows)

# This function is essentially copied verbatim from https://realpython.com/python-send-email/#option-2-setting-up-a-local-smtp-server
# https://mailtrap.io/blog/python-send-email/
def sendEmail():
    data = setUpYaml(CONFIGFILE)
    with smtplib.SMTP(data["smtpserver"], data["port"]) as server:
        mailinglist = data["email_recipients"]
        server.starttls()
        server.login(data["username"], data["password"])
        for receiver_email in mailinglist:
            server.sendmail(data["email_source"], receiver_email, data["message"])
            #print(receiver_email)

def main():
    mapSchoolToFile = createReportFiles2()
    populateReport(mapSchoolToFile)
    sortReportsByEmail()
    sendEmail()


main()




