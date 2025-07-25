import logging
from logging.handlers import SMTPHandler

from flask import Flask
from flask_moment import Moment

from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail

app = Flask(__name__)
app.config.from_object(Config)

login = LoginManager(app)
login.login_view = 'login'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

mail = Mail(app)

moment = Moment(app)

from app import routes, models, errors
