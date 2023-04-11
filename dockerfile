
FROM python:3.7

WORKDIR /code

RUN apt update -y

RUN mkdir -p /var/log/sawtooth

COPY ./api /code/api
COPY ./requirements.txt /code/requirements.txt
COPY ./packaging /code/packaging
COPY ./setup.py  /code/setup.py

RUN python3 setup.py clean --all \
    && python3 setup.py build \
    && python3 setup.py install \
    && cp -r ./api /usr/local/lib/python3.7/site-packages/air_anchor_api