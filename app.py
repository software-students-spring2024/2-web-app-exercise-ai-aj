import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

import pymongo

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Setup MongoDB connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["userDB"]
users = db["users"]

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    user = users.find_one({'email': request.form['email']})

    if user and user['password'] == request.form['password']:
        return 'Logged in successfully'
    else:
        flash('Invalid email/password combination')
        return redirect(url_for('index'))

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        existing_user = users.find_one({'email': request.form['email']})

        if existing_user is None:
            users.insert_one({'name': request.form['username'], 'email': request.form['email'], 'password': request.form['password']})
            return redirect(url_for('index'))
        else:
            return 'That email already exists!'

@app.route('/change_email', methods=['POST'])
def change_email():
    result = users.find_one_and_update(
        {'email': request.form['old_email']},
        {'$set': {'email': request.form['new_email']}}
    )
    if result:
        return 'Email updated successfully'
    else:
        return 'Email update failed'

@app.route('/reset_password_request', methods=['GET'])
def reset_password_request():
    return render_template('reset_password.html')

@app.route('/reset_password', methods=['POST', 'GET'])
def reset_password():
    if request.method == 'GET':
        return render_template('reset_password.html')
    elif request.method == 'POST':
        result = users.find_one_and_update(
            {'email': request.form['email']},
            {'$set': {'password': request.form['new_password']}}
        )
        if result:
            return 'Password updated successfully'
        else:
            return 'Password reset failed'

if __name__ == '__main__':
    app.run(debug=True)