import os
from dotenv import load_dotenv

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'top-secret!')
    ALCHEMICAL_DATABASE_URL = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'db.sqlite')
    ALCHEMICAL_ENGINE_OPTIONS = {'echo': bool(os.environ.get('SQL_ECHO'))}

    DISABLE_AUTH = bool(os.environ.get('DISABLE_AUTH'))
    ACCESS_TOKEN_MINUTES = int(os.environ.get('ACCESS_TOKEN_MINUTES', '15'))
    REFRESH_TOKEN_DAYS = int(os.environ.get('REFRESH_TOKEN_DAYS', '7'))
    RESET_TOKEN_MINUTES = int(os.environ.get('RESET_TOKEN_MINUTES', '15'))

    APIFAIRY_TITLE = 'Microblog API'
    APIFAIRY_VERSION = '1.0'
    APIFAIRY_UI = os.environ.get('DOCS_UI', 'elements')

    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '25'))
    MAIL_USE_TLS = bool(os.environ.get('MAIL_USE_TLS'))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER',
                                       'donotreply@microblog.example.com')

    CORS_SUPPORTS_CREDENTIALS = True
