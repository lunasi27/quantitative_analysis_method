import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # WEB DB
    MONGOALCHEMY_SERVER = 'localhost'
    MONGOALCHEMY_DATABASE = 'web'
    MONGOALCHEMY_PORT = 27017
    MONGOALCHEMY_USER = None
    MONGOALCHEMY_PASSWORD = None
    # DATA SOURCE
    SOURCE_SERVER = 'localhost'
    SOURCE_PORT = 27017
    SOURCE_DB = 'test'


class DevelopmentConfig(Config):
    DATABASE_URI = ''


class TestConfig(Config):
    DATABASE_URI = ''


class ProductionConfig(Config):
    DATABASE_URI = ''


config = {
    'development': DevelopmentConfig,
    'testing': TestConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
