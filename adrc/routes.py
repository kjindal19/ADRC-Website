import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from adrc import app, db, bcrypt, mail
from adrc.forms import *
from adrc.models import User
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

@app.route("/")
@app.route("/home")
def home():
    '''
    Route for Homepage of the website
    :return:
    render_template(index.html)
    '''

    return "Index Page"