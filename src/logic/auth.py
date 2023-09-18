import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, redirect, url_for

USERS_FILE = 'auth.json'

def load_users():
    with open(USERS_FILE, 'r') as f:
        users_data = json.load(f)
    return users_data['users']

def save_users(users):
    data = {'users': users}
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def register_user(username, password, role):
    users = load_users()
    hashed_password = generate_password_hash(password)
    users.append({
        "username": username,
        "password": hashed_password,
        "role": role
    })
    save_users(users)

def login_user(username, password):
    users = load_users()
    user = next((user for user in users if user['username'] == username), None)
    if user and check_password_hash(user['password'], password):
        session['user'] = user
        return True
    return False

def logout_user():
    session.pop('user', None)

# Define the login_required decorator
def login_required(view_func):
    def login_wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return login_wrapper

# Define the admin_required decorator
def admin_required(view_func):
    def admin_wrapper(*args, **kwargs):
        if 'user' not in session or session['user']['role'] != 'admin':
            return "Unauthorized", 403
        return view_func(*args, **kwargs)
    return admin_wrapper