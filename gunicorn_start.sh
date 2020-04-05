#!/usr/bin/env bash

gunicorn --reload --log-file=/usr/src/api/api/wsgi.log wsgi:app