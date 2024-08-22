#!/bin/bash

set -e

python manage.py migrate
python manage.py collectstatic --noinput

DEBUG=True python manage.py runserver 0.0.0.0:8000