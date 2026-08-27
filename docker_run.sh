#!/bin/bash

flask --app mothmonitor db upgrade
flask --app mothmonitor rq worker &
gunicorn --config gunicorn_config.py 'mothmonitor:create_app()'
