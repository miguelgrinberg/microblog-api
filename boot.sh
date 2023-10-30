#!/bin/sh
alembic upgrade head
exec gunicorn -b :5000 --access-logfile - --error-logfile - microblog:app
