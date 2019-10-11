from flask import Flask
from app.views import init_blueprint
from app.config import config
from app.services import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(config.get('default'))
    # app.config['MONGOALCHEMY_DATABASE'] = 'test'
    # app.debug = True
    init_blueprint(app)
    db.init_app(app)
    return app
