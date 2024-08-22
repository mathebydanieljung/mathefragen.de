#!/bin/bash

set -e

echo "💾 Applying database migrations"
python manage.py migrate

echo "🗂️ Collecting static files"
python manage.py collectstatic --noinput

#echo "🚜️ Compressing static files"
#python manage.py compress

gunicorn -c gunicorn.conf.py mathefragen.wsgi