#!/bin/sh

echo "waiting for database"

while ! mysqladmin ping -h "db" -P "3306" --silent; do
    sleep 1;
done

sleep 3

echo "starting gunicorn"

gunicorn --config gunicorn_config.py web:app
