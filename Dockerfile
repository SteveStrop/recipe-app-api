FROM python:3.7-alpine
MAINTAINER Orella

ENV PYTHONUNBUFFERED 1

COPY requirements.txt /requirements.txt
# permenant dependencies jpg-dev needed by Pillow see PyPI
RUN apk add --update --no-cache postgresql-client jpeg-dev
# temp dependencies to install postgres
RUN apk add --update --no-cache --virtual .tmp-build-deps gcc libc-dev linux-headers postgresql-dev musl-dev zlib zlib-dev
RUN pip install -r /requirements.txt
# remove the temp dependencies to keep container as small as possible
RUN apk del .tmp-build-deps

RUN mkdir /app
WORKDIR /app
COPY ./app /app

RUN mkdir -p /vol/web/media
RUN mkdir -p /vol/web/static
RUN adduser -D user
RUN chown -R user:user /vol/
RUN chmod -R 755 /vol/web
USER user
