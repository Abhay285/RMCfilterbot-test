import os
from os import environ

API_ID = int(environ.get("API_ID", "29034951"))
API_HASH = environ.get("API_HASH", "cfc8448de6746a6ccf9dc1812cf1c8f7")
BOT_TOKEN = environ.get("BOT_TOKEN", "")
DATABASE_URI = environ.get("DATABASE_URI", "")
LOG_CHANNEL = int(environ.get("LOG_CHANNEL", "-1002423393168"))
ADMIN = int(environ.get("ADMIN", "1328531459"))
CHANNEL = environ.get("CHANNEL", "@RMCBACKUP")
