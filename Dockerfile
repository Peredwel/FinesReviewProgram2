#version of python
FROM python:3.8.2
# Files required to be added to current directory
ADD main.py AFNSchools.csv requirements.txt .
# More files to add to a newly created directory in the container, ./InputAFNFiles_csv
ADD InputAFNFiles_csv ./InputAFNFiles_csv
# Some extra files we need to create in the container directory for intermediate processing steps
RUN mkdir /OutputFiles
RUN mkdir /SortedFiles
RUN mkdir /Logs
# Get the dependencies loaded
RUN pip install -r requirements.txt
# The actual command and the program being run
CMD [ "python", "main.py"]
