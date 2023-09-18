import json
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from src.logic import articles, auth

# Create a Blueprint instance for the auth routes
blueprint_auth = Blueprint('auth', __name__)

# Path to the JSON file storing user data
USERS_FILE = 'auth.json'

@blueprint_auth.context_processor
def inject_articles_functions():
    return dict(load_article=articles.load_article, parse_menu_content = articles.parse_menu_content)

# Define the login_required decorator
def login_required(view_func):
    @wraps(view_func)
    def login_wrapper(*args, **kwargs):
        if 'user' not in session:
            flash('You must log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return view_func(*args, **kwargs)
    return login_wrapper

# Define the admin_required decorator
def admin_required(view_func):
    @wraps(view_func)
    def admin_wrapper(*args, **kwargs):
        if 'user' not in session or session['user']['role'] != 'admin':
            flash('You are not authorized to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return view_func(*args, **kwargs)
    return admin_wrapper

# Authentication routes
@blueprint_auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = auth.load_users()

        user = next((user for user in users if user['username'] == username), None)
        if user and check_password_hash(user['password'], password):
            session['user'] = user
            flash('Login successful.', 'success')
            return redirect(url_for('articles.index'))
        else:
            flash('Invalid username or password. Please try again.', 'error')

    return render_template('login.html', load_article=articles.load_article)

@blueprint_auth.route('/logout')
@login_required
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@blueprint_auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = 'user'  # Assign a default role here

        users = auth.load_users()
        existing_user = next((user for user in users if user['username'] == username), None)
        if existing_user:
            flash('Username already exists. Please choose another.', 'error')
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(password, method='sha256')

        new_user = {
            "username": username,
            "password": hashed_password,
            "role": role
        }

        users.append(new_user)
        auth.save_users(users)

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

# Your other authentication routes go here
# ...
