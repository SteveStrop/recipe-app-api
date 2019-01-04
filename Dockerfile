FROM python:3.7-alpine
MAINTAINER Orella

ENV PYTHONUNBUFFERED 1

COPY requirements.txt /requirements.txt
RUN apk add --update --no-cache postgresql-client
# temp dependencies to install postgres
RUN apk add --update --no-cache --virtual .tmp-build-deps gcc libc-dev linux-headers postgresql-dev
RUN pip install -r /requirements.txt
# remove the temp dependencies to keep container as small as possible
RUN apk del .tmp-build-deps

RUN mkdir /app
WORKDIR /app
COPY ./app /app

RUN adduser -D user
USER user
