import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
import pymongo
from bson.objectid import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Setup MongoDB connection using environment variables
client = pymongo.MongoClient(os.getenv('MONGO_URI'))
db = client.get_default_database()  # Automatically get the database specified in the URI
users = db["users"]
tasks = db["tasks"]

bcrypt = Bcrypt(app)

@app.route('/')
def index():
    if 'user_id' in session:
        user_tasks = tasks.find({'user_id': ObjectId(session['user_id'])})
        return render_template('index.html', tasks=list(user_tasks))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    user = users.find_one({'email': request.form['email']})
    if user and bcrypt.check_password_hash(user['password'], request.form['password']):
        session['user_id'] = str(user['_id'])  # Store user ID in session
        return redirect(url_for('index'))
    else:
        flash('Invalid email/password combination')
        return redirect(url_for('index'))

@app.route('/logout', methods=['GET','POST'])
def logout():
    session.pop('user_id', None)  # Remove user_id from session
    return redirect(url_for('index'))

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        existing_user = users.find_one({'email': request.form['email']})

        if not existing_user:
            hashed_password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
            users.insert_one({'name': request.form['username'], 'email': request.form['email'], 'password': hashed_password})
            return redirect(url_for('index'))
        else:
            flash('That email already exists!')
            return redirect(url_for('register'))

@app.route('/add_task', methods=['POST', 'GET'])
def add_task():
    if request.method == 'GET':
        return render_template('addtask.html')
    elif request.method == 'POST':
        new_task = {
            "title": request.form['title'],
            "description": request.form.get('description', ''),
            "priority": int(request.form.get('priority', 1)),
            "deadline": datetime.strptime(request.form['deadline'], '%Y-%m-%d') if 'deadline' in request.form else None,
            "status": request.form.get('status', 'pending'),
            "completed": False,  # Set completed to False for new tasks
            "user_id": ObjectId(session['user_id'])
        }
        tasks.insert_one(new_task)
        flash('Task added successfully')
        return redirect(url_for('index'))

#marking task as completed
@app.route('/complete_task/<task_id>', methods=['POST'])
def complete_task(task_id):
    task = tasks.find_one({"_id": ObjectId(task_id)})
    new_status = not task.get('completed', False)
    tasks.update_one({"_id": ObjectId(task_id)}, {"$set": {"completed": new_status}})
    return redirect(request.referrer or url_for('index'))


@app.route('/edit_task/<task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    task_to_edit = tasks.find_one({"_id": ObjectId(task_id)})
    if request.method == 'GET':
        # Pass task details to template, converting deadline to string if it exists
        return render_template('edittask.html', task=task_to_edit, task_id=task_id)
    elif request.method == 'POST':
        updates = {
            "title": request.form['title'],
            "description": request.form.get('description', ''),
            "priority": int(request.form.get('priority', 1)),
            "status": request.form.get('status', 'pending'),
        }
        # Handle deadline separately to convert from string to datetime
        if 'deadline' in request.form and request.form['deadline']:
            updates["deadline"] = datetime.strptime(request.form['deadline'], '%Y-%m-%d')
        tasks.update_one({"_id": ObjectId(task_id)}, {"$set": updates})
        flash('Task updated successfully')
        return redirect(url_for('index'))

@app.route('/delete_task/<task_id>', methods=['POST'])
def delete_task(task_id):
    tasks.delete_one({"_id": ObjectId(task_id)})
    flash('Task deleted successfully')
    return redirect(url_for('index'))

@app.route('/reset_password', methods=['POST', 'GET'])
def reset_password():
    if request.method == 'GET':
        return render_template('resetpassword.html')
    elif request.method == 'POST':
        hashed_new_password = bcrypt.generate_password_hash(request.form['new_password']).decode('utf-8')
        result = users.find_one_and_update(
            {'email': request.form['email']},
            {'$set': {'password': hashed_new_password}}
        )
        if result:
            flash('Password updated successfully')
        else:
            flash('Password reset failed')
        return redirect(url_for('index'))
    
@app.route('/tasks')
def view_tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_tasks = tasks.find({'user_id': ObjectId(session['user_id'])})
    return render_template('tasks.html', tasks=list(user_tasks))

@app.route('/summary')
def summary():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    now = datetime.now()
    past_due_completed = tasks.find({'user_id': ObjectId(session['user_id']), 'deadline': {'$lt': now}, 'completed': True})
    past_due_incomplete = tasks.find({'user_id': ObjectId(session['user_id']), 'deadline': {'$lt': now}, 'completed': False})

    return render_template('summary.html', past_due_completed=list(past_due_completed), past_due_incomplete=list(past_due_incomplete))

@app.route('/update_task_status', methods=['POST'])
def update_task_status():
    task_id = request.form['task_id']
    completed_status = 'completed' in request.form
    tasks.update_one({'_id': ObjectId(task_id)}, {'$set': {'completed': completed_status}})
    return redirect(url_for('index'))

@app.route('/account')
def account():
    if 'user_id' in session:
        user = users.find_one({'_id': ObjectId(session['user_id'])})
        if user:
            # Use the email from the session if available, otherwise use the one from the database
            email = session.get('email', user['email'])
            return render_template('account.html', username=user['name'], email=email)
        else:
            flash('User not found.')
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/change_email')
def change_email_page():
    if 'user_id' in session:
        return render_template('changeemail.html')
    else:
        return redirect(url_for('login'))

@app.route('/change_email', methods=['POST'])
def change_email():
    username = request.form.get('username')
    old_email = request.form.get('old_email')
    password = request.form.get('password')
    new_email = request.form.get('new_email')
    
    # Fetch user from the database
    user = users.find_one({'username': username, 'email': old_email})
    # Verify password and update email if correct
    if user and bcrypt.check_password_hash(user['password'], password):
        # Update the database with the new email
        users.update_one({'_id': user['_id']}, {'$set': {'email': new_email}})
        # Update the email in session
        session['email'] = new_email
        flash('Email address updated successfully.')
        return redirect(url_for('account'))
    else:
        flash('Invalid credentials.')
        return redirect(url_for('account'))
    


if __name__ == '__main__':
    app.run(debug=True, port=5001)
