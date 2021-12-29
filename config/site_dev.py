# Exemplary development configuration for a public site

import os


DEBUG = True

SECRET_KEY = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
SESSION_COOKIE_SECURE = False

SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://byceps:boioioing@127.0.0.1/byceps'

REDIS_URL = 'redis://127.0.0.1:6379/0'

APP_MODE = 'site'
SITE_ID = os.environ.get('SITE_ID')

MAIL_TRANSPORT = 'logging'

DEBUG_TOOLBAR_ENABLED = True
STYLE_GUIDE_ENABLED = True