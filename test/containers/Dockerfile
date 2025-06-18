#FROM python:3.13-alpine
FROM python:3.13

LABEL maintainer="Robin Wardle <robin.wardle@newcastle.ac.uk>"

WORKDIR /client

#RUN apk update
#RUN apk add git
RUN apt update && apt upgrade -y
RUN apt install git -y
RUN apt install postgresql-client -y

COPY requirements.txt .
COPY testdb-credentials.json .
COPY run-tests.py .

#RUN python3 -m venv .venv && source .venv/bin/activate

RUN pip install --upgrade pip
#RUN pip install -r requirements.txt
RUN pip install git+https://github.com/NewcastleRSE/data-warehouse-client.git@master

EXPOSE 8888
