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
    FLASK_DEBUG = environ.get("FLASK_DEBUG")
    #FLASK_ENV = environ.get("FLASK_ENV")
    CSRF_ENABLED = True
    SECRET_KEY = environ.get("SECRET_KEY")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024




