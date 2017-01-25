from flask import Flask


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object('mym.settings')
    #app.config.from_pyfile('settings.cfg', silent=True)

    from mym.build import build
    app.register_blueprint(build)

    return app
