import os
import sys

# FIXME Hardcoded paths
path = '/var/www/plebia'
if path not in sys.path:
    sys.path.append(path)
    sys.path.append(path+'/plebia')

os.environ['DJANGO_SETTINGS_MODULE'] = 'plebia.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

