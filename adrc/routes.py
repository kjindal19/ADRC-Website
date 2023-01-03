import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from adrc import app, db, bcrypt, mail
from adrc.forms import RegistrationForm, LoginForm, UpdateAccountForm, RequestResetForm, ResetPasswordForm
from adrc.models import User, Event
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

@app.route("/")
@app.route("/home")
def home():
    '''

    hashed_pass = bcrypt.generate_password_hash("admin@123").decode('utf-8')
    db.session.add(User(username='admin',email='admin@gmail.com',password=hashed_pass,urole='ADMIN'))
    db.session.commit()
    db.create_all()

    '''

    events = Event.query.all()

    return render_template('display/index.html', levent=events[0::2], revent=events[1::2])



@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            mobile=form.mobile.data,
            Gender=form.gender.data,
            city=form.city.data,
            college=form.college.data,
            course=form.course.data,
            semester=form.semester.data,
            urole="PARTICIPANT"
        )

        db.session.add(user)
        db.session.commit()
        flash(f'Your Have been Registered!, We will contact you soon.', 'success')
        return render_template('display/registered.html')
    return render_template('display/register.html', title='Register', form=form)


@login_required
@app.route("/newuser", methods=['GET', 'POST'])
def newuser():

    if not current_user.is_authenticated:
        return redirect(url_for('home'))

    elif current_user.urole !="ADMIN":
        return redirect('/dashboard')

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, urole="USER")
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created!, You can now login in', 'success')
        return redirect(url_for('dashboard'))

    return render_template('portal/register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/dashboard')
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(url_for('dashboard'))

        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('portal/login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path,
        'static/profile_pic', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.urole == "ADMIN":
        return render_template('portal/admin_dashboard.html')
    return render_template('portal/user_dashboard.html')


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file

        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your Account has been updated!", 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pic/' + current_user.image_file)
    return render_template('portal/account.html', title='Account', image_file=image_file,
        form=form)



@app.route("/user/<string:username>/delete", methods=['POST','GET'])
@login_required
def delete_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    if (user==current_user) or (current_user.urole=="ADMIN"):
        if anyevent(user):
            flash('Please delete Events First','danger')
            return redirect(url_for('dashboard'))
        else:
            db.session.delete(user)
            db.session.commit()
            flash("Your User has been deleted", "success")
            return redirect(url_for('dashboard'))
    else:
        abort(403)


@app.route("/user/<string:username>")
def user_events(username):
    if username != current_user.username:
        return redirect(url_for('home'))

    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    events = Event.query.filter_by(events=user)\
        .paginate(page=page, per_page=2)
    return render_template('user_events.html',
     events=events, user = user)



def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                   sender='noreply@demo.com',
                   recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be effected
'''
    mail.send(msg)




@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('Check your email for instructions to reset your password', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title="Reset Password", form=form)



@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash("That is an invalid or expired token", 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'Your password has been updated!, You are now able to log in', 'success')
        return redirect(url_for('login'))

    return render_template('reset_token.html', title='Reset Password', form=form)


