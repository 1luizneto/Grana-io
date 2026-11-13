#!/bin/sh
# Subida do backend no modo de uso (specs/011-modo-de-uso, research R-02): aplica as migrations e
# inicia o Gunicorn, sem recarga automática.
set -e

python manage.py migrate --noinput
exec gunicorn config.wsgi --bind 0.0.0.0:8000 --workers 2 --access-logfile -
