"""Configuration de l'application Flask basée sur la class Config."""
from os import environ, path
from dotenv import load_dotenv
import sys

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, ".env"))

class Config:
    """Configuration à partir des variables définies dans .env"""

    # Application settings

    APP_NAME = environ.get("APP_NAME")

    # Flask settings
    FLASK_APP = environ.get("FLASK_APP")
    FLASK_ENV = environ.get("FLASK_ENV")
    #FLASK_DEBUG = False
    CSRF_ENABLED = True

    # Flask-SQLAlchemy settings
    SECRET_KEY = environ.get("SECRET_KEY")

    # Database
    SQLALCHEMY_DATABASE_URI = environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = environ.get("SQLALCHEMY_TRACK_MODIFICATIONS")
    SQLALCHEMY_POOL_RECYCLE = 250
    SQLALCHEMY_ECHO = False

    #UPLOAD
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
