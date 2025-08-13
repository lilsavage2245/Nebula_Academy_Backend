web: gunicorn nebula_backend.wsgi --log-file -
release: python manage.py migrate
web: gunicorn config.wsgi:application --log-file -
