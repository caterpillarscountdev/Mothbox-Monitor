#!/bin/bash

flask --app mothmonitor db upgrade
gunicorn --config gunicorn_config.py 'mothmonitor:create_app()'
