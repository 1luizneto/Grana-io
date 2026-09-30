#!/bin/sh
# Subida do backend no modo de desenvolvimento: aplica as migrations antes de aceitar
# requisições (FR-004) e só então inicia o servidor.
set -e

python manage.py migrate --noinput
exec python manage.py runserver 0.0.0.0:8000
