
FROM python:3.7

WORKDIR /code

RUN apt update -y

RUN mkdir -p /var/log/sawtooth

COPY ./api /code/api
COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir -r /code/requirements.txt