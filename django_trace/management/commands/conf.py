# not regexes
GOOD_PRESETS = {
    'myproj': [
        'myproj',
        ],
    }

# not regexes
BAD_PRESETS = {
    'django': [
        'django_apps.common.routers',
        'django.db.',
        'django.template.',
        'django.conf',
        'django.utils',
        'django.management',
        'django.dispatch',
        ],
    }
