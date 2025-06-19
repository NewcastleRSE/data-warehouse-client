FROM python:3.13

LABEL maintainer="Robin Wardle <robin.wardle@newcastle.ac.uk>"

WORKDIR /client
RUN mkdir outputs

RUN apt update && apt upgrade -y
RUN apt install git -y
RUN apt install postgresql-client -y

COPY requirements.txt .
COPY testdb-credentials.json .
COPY run-tests.sh .
COPY tests ./tests

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 8888
