import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail




app = Flask(__name__)
app.config['SECRET_KEY'] = 'c61d0b0167fa2d8681a9f80c56b4bc2a'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://flask:Flask1234@localhost/adrc'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager =  LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
app.config['MAIL_SERVER'] = 'stmp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
mail = Mail(app)
app.app_context().push()


from adrc import routes