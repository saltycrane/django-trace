Install
-------
 - `pip install -e git://github.com/saltycrane/django-trace.git#egg=django_trace`
 - Add `'django_trace'` to `INSTALLED_APPS` in `settings.py`

Usage
-----

    ./manage.py trace --help

    ./manage.py trace --bad=django,SocketServer --calls-only runserver
