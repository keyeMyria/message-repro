FROM python:3-alpine3.7

# logging to the console breaks without this
ENV PYTHONUNBUFFERED 1
ENV PYTHONFAULTHANDLER 1

# so we can cache the installed python modules apart from the app files
COPY requirements.txt /app/

RUN \
  apk add --no-cache \
    bash \
    gettext \
    libffi \
    postgresql-client && \
  apk add --no-cache --virtual build-dependencies \
    build-base \
    git \
    libffi-dev \
    linux-headers \
    musl-dev \
    postgresql-dev && \
  cd /app && \
  pip3 install --upgrade pip setuptools && \
  pip3 install -r requirements.txt && \
  rm -rf /root/.cache && \
  apk del build-dependencies

RUN update-ca-certificates

COPY . /app/

WORKDIR /app/
