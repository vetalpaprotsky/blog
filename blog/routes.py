import os
import secrets
from PIL import Image
from blog import app, db, bcrypt
from flask import render_template, url_for, flash, redirect, request
from blog.forms import RegistrationForm, LoginForm, UpdateAccountForm
from blog.models import User
from flask_login import login_user, logout_user, current_user, login_required

posts = [
    {
        'author': 'Vitalii Paprotskyi',
        'title': 'Blog post 1',
        'content': 'First post content',
        'date_posted': 'April 20, 2018',
    },
    {
        'author': 'Foo Bar',
        'title': 'Blog post 2',
        'content': 'Second post content',
        'date_posted': 'April 21, 2018',
    },
]


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', posts=posts)


@app.route('/about')
def about():
    return render_template('about.html', title='About')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next', url_for('home'))
            return redirect(next_page)
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')

    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_image(form_image):
    random_hex = secrets.token_hex(8)
    _, image_ext = os.path.splitext(form_image.filename)
    image_filename = random_hex + image_ext
    image_path = os.path.join(app.root_path, 'static/profile_pics', image_filename)

    # Resize image and save it
    output_size = (128, 128)
    image = Image.open(form_image)
    image.thumbnail(output_size)
    image.save(image_path)

    # Save image as it is
    # form_image.save(image_path)

    return image_filename


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.image.data:
            image_filename = save_image(form.image.data)
            current_user.image_filename = image_filename
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_filename = url_for('static', filename='profile_pics/' + current_user.image_filename)
    return render_template(
        'account.html', title='Account', image_filename=image_filename, form=form
    )
