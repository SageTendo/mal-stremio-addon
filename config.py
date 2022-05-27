import os


class Config:
    JSON_SORT_KEYS = False
    HOST = os.getenv('FLASK_RUN_HOST')
    PORT = os.getenv('FLASK_RUN_PORT')


class Prod(Config):
    DEBUG = False


class Dev(Config):
    DEBUG = True
