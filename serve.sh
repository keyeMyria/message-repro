#!/bin/bash

./manage.py collectstatic --no-input
./manage.py migrate

daphne app.asgi:application --bind 0.0.0.0 --port "$PORT"
