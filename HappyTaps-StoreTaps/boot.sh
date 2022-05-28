#!/bin/sh
source venv/bin/activate
exec gunicorn --bind :3000 --workers 1 --threads 8 --timeout 0 happytaps-storetaps:app
