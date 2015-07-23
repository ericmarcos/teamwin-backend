web: gunicorn -k gevent -w 4 teamwin.wsgi
worker: celery -A teamwin worker -l info -P gevent -c 3