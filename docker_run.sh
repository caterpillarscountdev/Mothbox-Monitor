#!/bin/bash

flask --app mothbox db upgrade
gunicorn --config gunicorn_config.py 'mothmonitor:create_app()'
