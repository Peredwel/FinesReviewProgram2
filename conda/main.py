import os
import csv
import operator
import pandas as pd
import openpyxl
from bs4 import UnicodeDammit

HEADERS = ['lender_institution', 'borrower_institution', 'full_name', 'user_email', 'expiry_date', 'remaining_amount', 'active_loan_count']

#This function checks the csv files provided in InputAFNFiles_csv and ensures they are, in fact, Analytics reports
#TODO: Ask Alex if we have to add a user input option to check graduation date (and ensure all the reports added ARE, in
# fact, for the set of users graduating that semester, etc.

def detect_encoding(file_path: str) -> str:
    encoding = ""
    with open(file_path, 'rb') as file:
        content = file.read()
    encoding = UnicodeDammit(content).original_encoding
    return encoding

def checkcsv(filename):
    myfile = './InputAFNFiles_csv/' + filename
    encoding = detect_encoding(myfile)
    df = pd.read_csv(myfile, delimiter= '\t', header=0, encoding=encoding)
    headers = df.columns.tolist()
    
    if headers != HEADERS: 
        error="The headers in this file (" + filename + ") do not match those of the expected analytics report.  Did you provide the correct file?" 
    else: 
        error=""
    return error

def convertcsvtoxlsx(filename):
    read_file = pd.read_excel('InputAFNFiles_csv/' + filename)
    newfilename = filename.split('.')[0] + ".csv"
    read_file.to_csv('InputAFNFiles_csv/'+ newfilename, index=None, header=True)
    #delete xlsx file
    os.remove('InputAFNFiles_csv/'+ filename)
    error = checkcsv(newfilename)
    return error

def checkFiles():
    errorfile = open("Logs/errorfile.txt", 'a')
    noErrorInAnyFile = True
    for file in os.listdir('InputAFNFiles_csv'):
        filename = os.fsdecode(file)
        filetype = checkFileExtension(filename)
        if filetype == 'csv':
            print(filename)
            errorInFile = checkcsv(filename)
        elif filetype == 'xlsx':
            errorInFile = convertcsvtoxlsx(filename)
        else:
            errorInFile = "The extension of " + filename + " does not match any accepted format.  Please provide a csv or xlsx file and try again"
        if errorInFile:
            print(errorInFile)
            errorfile.write(errorInFile)
            noErrorInAnyFile = False
    return noErrorInAnyFile

def checkFileExtension(filename):
    components = filename.split(".")
    filextension = ''
    if len(components) < 2:
        filextension = 'No file extension'
    else:
        filextension = components[1]
    return filextension

# This function creates empty report files for each school
# Returns a dictionary relating which file corresponds to which institution
def createReportFiles():
    filedict = {}
    with open('AFNSchools.csv', encoding='UTF-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            school = row[0]
            location = 'OutputFiles/' + school.strip().replace('/', '').replace(' ', '_') + '.csv'
            filedict[school] = location
    csv_file.close()
    return filedict

# Receives the filedict created in the first function
# Iterates through the input files and sorts all borrowers from one institution into that institution's file

def populateReport(filedict):
    for file in os.listdir('InputAFNFiles_csv'):
        filename = os.fsdecode(file)
        line_count = 0
        filepath = 'InputAFNFiles_csv/' + filename
        encoding = detect_encoding(filepath)
        with open(filepath, 'r', encoding=encoding) as csv_file1:
            csv_reader = csv.reader(csv_file1, delimiter='\t')
            for row in csv_reader:
                if line_count > 0:
                    lender = row[0]
                    borrower = row[1]
                    print(filedict)
                    # open appropriate write file:
                    if borrower != "":
                        with open(filedict[borrower], 'a', encoding='UTF-8', newline='\n') as writefile:
                            csv_writer = csv.writer(writefile, delimiter='\t')
                            csv_writer.writerow(row)
                        writefile.close()
                    else:
                        with open("OutputFiles/errors.csv", 'a', encoding='UTF-8', newline='\n') as writefile:
                            csv_writer = csv.writer(writefile, delimiter='\t')
                            csv_writer.writerow(row)
                        writefile.close()
                line_count += 1
            csv_file1.close()

# Goes through the reports in OutputFiles
def sortReportsByEmail():
    for file in os.listdir('OutputFiles'):
        filename = os.fsdecode(file)
        line_count = 0
        with open('OutputFiles/' + filename, "r", encoding='UTF-8') as csv_file1:
            csv_reader = csv.reader(csv_file1, delimiter='\t')
            with open('SortedFiles/' + filename, "w", newline='', encoding='UTF-8') as writefile:
                csv_writer = csv.writer(writefile, delimiter='\t')
                sorted_rows = sorted(csv_reader, key=operator.itemgetter(3))
                csv_writer.writerow(HEADERS)
                csv_writer.writerows(sorted_rows)

def main():
    noErrorInAnyFiles = checkFiles()
    if noErrorInAnyFiles:
        mapSchoolToFile = createReportFiles()
        populateReport(mapSchoolToFile)
        sortReportsByEmail()

main()
