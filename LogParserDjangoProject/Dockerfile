# The first instruction is what image we want to base our container on
# We Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# The enviroment variable ensures that the python output is set straight
# to the terminal with out buffering it first
ENV PYTHONUNBUFFERED 1
ENV PORT "8080"




# create root directory for our project in the container
RUN mkdir /LogParserDjangoProject

# Set the working directory to /LogParserDjangoProject
WORKDIR /LogParserDjangoProject

# Copy the current directory contents into the container at /LogParserDjangoProject
ADD . /LogParserDjangoProject/

# Set the working directory to /LogParserDjangoProject
WORKDIR /LogParserDjangoProject

# Install any needed packages specified in requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt


CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]