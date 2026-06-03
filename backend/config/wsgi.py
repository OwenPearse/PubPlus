import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Use base module directly so deploy works even if settings/__init__.py is missing from image.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

application = get_wsgi_application()
