import os
from flask import Config, Flask
from app.routes import main as main_blueprint
from flask_socketio import SocketIO

socketio = SocketIO()
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    socketio.init_app(app)
    app.register_blueprint(main_blueprint)

    from app import events
    return app