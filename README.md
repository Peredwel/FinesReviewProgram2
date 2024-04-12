# Alma Fines and Outstanding Loans Analytics Report Generation

When students graduate from a CF institution, they may have fines and outstanding loans for books borrowed through AFN from another institution.  Currently, there is no way in the Network Zone for a borrowing institution to see which of their graduating students are owing fines or about to abscond with books from AFN schools.

To overcome this problem, a standard analytics report has been created for all institutions to run at the end of each semester, located in the directory /shared/UTON Network 01OCUL_NETWORK/Reports/Geoff's reports/USR_FAF_FUL - AFN Users with Fines or Active Loans accessible via Alma Analytics.  This report provides information on the borrower, their institution (borrowing institution), the institution from which the resource was borrowed (lending institution), along with details on loans and fines.  Each borrowing institution will provide this report to a folder on the Scholars Portal servers.  The script provided here, main.py, will output a report to be delivered to each lending institution on outstanding loans and fees owed by their students to each of the AFN schools.

## Process / Steps

1. The script main.py will first generate an empty csv file to hold the report for each AFN School using the list of AFN schools in AFNSchools.csv .  These empty csv files are kept in a temporary folder in the Docker container, OutputFiles

2. main.py then iterates through each of the reports from lending institutions in the folder InputAFNFiles_csv, located in this project directory.  It identifies the borrowing institution of each borrower, copies the row of data on their outstanding loans and fines at the lending information, and appends that information to a tab-separated, Latin-1 encoded csv for the borrowing institution.

For example, on reading the report produced by lending institution uOttawa, main.py sees a line indicating 
University of Ottawa	Queen's University	Ezra Bridger	ezrabridger@queensuni.ca	2024-04-30	150	1

The script recognizes the borrower comes from Queen's, and places this row in the report to be handed to Queen's University.  Queen's University will read this file and discover Ezra Bridger is owing $150 and has one item outstanding at uOttawa.  They will ask Ezra to please give uOttawa back our book and pay his fines :)

3. After main.py sorts through all the reports and puts information on borrowers at all institutions into the files held in temporary folder OutputFiles, it sorts the borrowers in each borrowing institution report by email.  This is to make it easier for the borrowing institution to contact borrowers if a given borrower has outstanding loans and fines at multiple institutions.  The sorted files are put in the temporary folder SortedFiles.

4. The Docker container copies the contents of the temporary folder SortedFiles to a mounted file indicated in the docker-compose.yml or docker-compose-wsl.yml files under volumes.  Substitute the existing mount, /home/cs/Downloads/Output:/SortedFiles, for the folder where you'd like the sorted output files to end up.

## How to run / test

### General info

This whole process is done in a docker container, so you don't need to worry about setting up a python environment. You can install docker desktop from here: https://www.docker.com/products/docker-desktop. This is a one time job run a few times a year, so you could run from anywhere, and probably don't want to even put on a server.

This way, you don't need to know how to setup a python environment. Once docker is installed, ensure it's running.

This repository/project was built using Pycharm and text editors.

### Setup

1. Download and set up Docker Desktop
2. Download or clone the repository
3. Edit the docker-compose.yml or docker-compose-wsl.yml files to indicate the folder where the script output should be stored.
4. Download all your csv files from borrowing institutions into the InputAFNFiles_csv directory in this project, where the main.py script will find them.


#### Docker Compose commands

1. in the command line run the following to test and run the process: docker-compose up --build
2. to perform the process with the -wsl file (or another special case): docker-compose -f docker-compose-wsl.yml up --build (Note: I haven't tested this before)

