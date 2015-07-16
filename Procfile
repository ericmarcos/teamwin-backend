web: gunicorn -k gevent -w 4 dareyoo2.wsgi
worker: celery -A dareyoo2 worker -l info -P gevent -c 3