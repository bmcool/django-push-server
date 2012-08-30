import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pushserver.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
