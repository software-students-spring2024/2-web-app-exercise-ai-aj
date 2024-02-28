import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
import hashlib

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

    # Hash the input password to compare
    input_password = request.form['password'].encode('utf-8')
    hashed_input_password = hashlib.sha256(input_password).hexdigest()

    if user and user['password'] == hashed_input_password:
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
            # Hash the password before storing it
            password = request.form['password'].encode('utf-8')
            hashed_password = hashlib.sha256(password).hexdigest()

            users.insert_one({'name': request.form['username'], 'email': request.form['email'], 'password': hashed_password})
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
    return render_template('resetpassword.html')

@app.route('/reset_password', methods=['POST', 'GET'])
def reset_password():
    if request.method == 'GET':
        return render_template('resetpassword.html')
    elif request.method == 'POST':
        # Hash the new password before storing it
        new_password = request.form['new_password'].encode('utf-8')
        hashed_new_password = hashlib.sha256(new_password).hexdigest()

        result = users.find_one_and_update(
            {'email': request.form['email']},
            {'$set': {'password': hashed_new_password}}
        )
        if result:
            return 'Password updated successfully'
        else:
            return 'Password reset failed'

if __name__ == '__main__':
    app.run(debug=True, port=5001)

    # set password to helloworld1