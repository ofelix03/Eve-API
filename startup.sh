service nginx restart &
gunicorn --reload wsgi:app
