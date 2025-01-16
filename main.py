import os
import csv
import operator
import re
import yaml
import smtplib
import ssl
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import datetime
from pathlib import Path

HEADERS = ['lender_institution', 'borrower_institution', 'full_name', 'user_email', 'expiry_date', 'remaining_amount', 'active_loan_count']
CONFIGFILE = "config.yaml"

def changeInputFile(oldfile):
    stringlist = oldfile.split("/")
    filename = stringlist[-1]
    newfile = "old_" + filename
    newabsfile = oldfile.replace(filename, newfile)
    os.rename(oldfile, newabsfile)
    logging.info(f"Renamed {oldfile} to {newabsfile}")

# Function to set up using YAML file:
# Returns dictionary
def setUpYaml(configfile):
    try:
        with open(configfile, 'r') as stream:
            data = yaml.safe_load(stream)
            return data
    except FileNotFoundError as e:
        logging.error(f"Config file '{configfile}' not found: {e}")
        return {"error": f"Config file '{configfile}' not found."}
    except yaml.YAMLError as e:
        logging.error(f"Error loading YAML from {configfile}: {e}")
        return {"error": f"Error loading YAML: {e}"}
    except Exception as e:
        logging.error(f"Error reading config file '{configfile}': {e}")
        return {"error": f"Error reading config file: {e}"}


# A function to create a list of matching files within a repository
# Returns a list of filenames with absolute paths that haven't been previously processed (ie. no old_ prefix).
def match(directory):
    matches = []
    pattern = re.compile("al-*")

    for root, dirnames, _ in os.walk(directory):
        for dirname in dirnames:
            if pattern.match(dirname):
                holdingdir = os.path.join(root, dirname)
                for root2, _, filenames2 in os.walk(holdingdir):
                    for filename2 in filenames2:
                        if not filename2.startswith("old_"):
                            matches.append(os.path.join(root2, filename2))
                            logging.info(f"Found matching file: {filename2}")

    logging.info(f"Total matching files: {len(matches)}")
    return matches

#This function checks the csv files output in match()
#Ask Alex if we have to add a user input option to check graduation date (and ensure all the reports added ARE, in
# fact, for the set of users graduating that semester, etc.
# Accept list of matches from match() and check to make sure they're actually the correct format, etc.
def checkFileHeaders(matcheslist):
    log_file_path = "Logs/errorfile.txt"
    correctfiles = []

    with open(log_file_path, 'a') as errorfile:
        for filename in matcheslist:
            filetype = os.path.splitext(filename)[-1].lower()

            if filetype == '.csv':
                try:
                    with open(filename, encoding='latin-1') as csv_file1:
                        csv_reader = csv.reader(csv_file1, delimiter=',')
                        headers = next(csv_reader)
                        headers[0] = headers[0].replace('ï»¿', '')  # Remove byte order mark

                        if headers != HEADERS:
                            errorfile.write(f"{filename}\t The headers do not match the expected format.\n")
                        else:
                            correctfiles.append(filename)
                            logging.info(f"File {filename} passed header check.")
                except Exception as e:
                    errorfile.write(f"{filename}\t Error reading file: {e}\n")
                    logging.error(f"Error reading file {filename}: {e}")
            else:
                errorfile.write(f"{filename}\t Incorrect file extension.\n")
                logging.warning(f"File {filename} has incorrect extension.")

    return correctfiles

# This function creates empty report files for each school
# Uses json file
def createReportFiles(filename="AFNSchools.json"):
    try:
        with open(filename, 'r') as file:
            datadict = json.load(file)

        for university, csv_file in datadict.items():
            os.makedirs(os.path.dirname(csv_file), exist_ok=True)
            with open(csv_file, 'w') as f:
                pass  # Just create the file
            logging.info(f"Created empty file: {csv_file}")
        return datadict
    except FileNotFoundError:
        logging.error(f"Error: File '{filename}' not found.")
        return None
    except json.JSONDecodeError:
        logging.error(f"Error: Failed to decode JSON from '{filename}'.")
        return None

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
    logging.info(f"Found {len(correctfiles)} files with correct headers in {directorypath}")

    for filename in correctfiles:
        logging.info(f"Processing file to populate report: {filename}")
        with open(filename, encoding='latin-1') as csv_file1:
            csv_reader = csv.reader(csv_file1, delimiter=',')
            next(csv_reader)
            for row in csv_reader:
                borrower = row[1]
                if borrower:
                    with open(filedict[borrower], 'a', encoding='latin-1', newline='\n') as writefile:
                        csv_writer = csv.writer(writefile, delimiter='\t')
                        csv_writer.writerow(insertZero(row))
                else:
                    with open("OutputFiles/errors.csv", 'a', encoding='latin-1', newline='\n') as writefile:
                        csv_writer = csv.writer(writefile, delimiter='\t')
                        csv_writer.writerow(insertZero(row))
                    logging.warning(f"Borrower missing in {filename}, added to errors.csv.")

# Goes through the reports in OutputFiles
def sortReportsByEmail(input_dir='OutputFiles', output_dir='SortedFiles'):
    try:
        os.makedirs(output_dir, exist_ok=True)

        for file in os.listdir(input_dir):
            filename = os.fsdecode(file)
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)

            with open(input_path, "r", encoding='latin-1') as csv_file1:
                csv_reader = csv.reader(csv_file1, delimiter='\t')
                sorted_rows = sorted(csv_reader, key=lambda row: row[3].lower())

                with open(output_path, "w", newline='', encoding='latin-1') as writefile:
                    csv_writer = csv.writer(writefile, delimiter='\t')
                    csv_writer.writerow(HEADERS)
                    csv_writer.writerows(sorted_rows)

            logging.info(f"Sorted file: {filename}")

    except Exception as e:
        logging.error(f"Error occurred while sorting reports: {e}", exc_info=True)

def sendEmail():
    data = setUpYaml(CONFIGFILE)

    email_subject = data["email_subject"]
    email_source = data["email_source"]
    email_message = data["message"]

    message = MIMEMultipart()
    message["From"] = email_source
    message["Subject"] = email_subject
    message.attach(MIMEText(email_message, "plain"))

    with smtplib.SMTP(data["smtpserver"], data["port"]) as server:
        server.starttls()

        if data["username"] and data["password"]:
            server.login(data["username"], data["password"])

        for receiver_email in data["email_recipients"]:
            message["To"] = receiver_email
            server.sendmail(email_source, receiver_email, message.as_string())
            logging.info(f"Sent email to {receiver_email}")

def setup_logger():
    # Create Logs directory if it doesn't exist
    log_dir = "Logs"
    os.makedirs(log_dir, exist_ok=True)

    # Define log file name based on current date and time
    log_filename = datetime.now().strftime("%Y-%m-%d_%H_%M.log")
    log_file_path = os.path.join(log_dir, log_filename)

    # Set up logging to console and file
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create file handler to log to file
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)

    # Create console handler to log to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Set log format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def main():
    setup_logger()

    try:
        logging.info("Creating report files...")
        mapSchoolToFile = createReportFiles()

        logging.info("Populating report...")
        populateReport(mapSchoolToFile)

        logging.info("Sorting reports by email address...")
        sortReportsByEmail()

        logging.info("Sending emails...")
        sendEmail()

        logging.info("Process completed successfully.")
    except Exception as e:
        logging.error("An error occurred: %s", e)
        logging.error("Full stack trace:", exc_info=True)

if __name__ == "__main__":
    main()
