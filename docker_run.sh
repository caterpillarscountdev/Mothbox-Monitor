#!/bin/bash

flask db upgrade
gunicorn --config gunicorn_config.py 'mothmonitor:create_app()'
