from flask import Flask
from flask_sqlalchemy import SQLAlchemy

'''
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_DATABASE_URI'] = 'sqlite:///project.db'
    db.init_app(app)
    return app
'''

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def hello_world():
        return '<h1>Hello, World!</h1><p>Your Flask app is running.</p>'

    return app
