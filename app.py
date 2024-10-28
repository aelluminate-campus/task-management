from flask import Flask, render_template, redirect, url_for, flash, session, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required  # Ensure login_user is imported
from flask_bcrypt import Bcrypt
from models import db, User, Task
from forms import RegistrationForm, LoginForm, TaskForm, ShareTaskForm
from config import Config
from functools import wraps
from datetime import datetime, date

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'key'  # Make sure to change this to a more secure key in production

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:  # Check if the user is already logged in
        return redirect(url_for('dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can log in now.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:  # Check if the user is already logged in
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Wrong details, please try again.', 'danger')
    return render_template('login.html', form=form)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:  # Check if user is authenticated
            flash('You need to log in to access this page.', 'warning')
            return redirect(url_for('login'))  # Redirect to login page
        return f(*args, **kwargs)
    return decorated_function

@app.route('/dashboard')
@login_required
def dashboard():
    users = User.query.all()
    return render_template('dashboard.html', users=users)

@app.route('/logout')
@login_required
def logout():
    logout_user()  # Use Flask-Login's logout_user function
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/task', methods=['GET', 'POST'])
@login_required
def task():
    form = TaskForm()
    is_admin = current_user.role == 'admin'  # Check if the current user is an admin

    if is_admin and form.validate_on_submit():
        new_task = Task(
            title=form.title.data,
            description=form.description.data,
            priority=form.priority.data,
            deadline=datetime(int(form.deadline_year.data), int(form.deadline_month.data), int(form.deadline_day.data)),
            user_id=current_user.id,
            status='To Do'
        )
        db.session.add(new_task)
        db.session.commit()
        flash('Task created successfully!', 'success')
        return redirect(url_for('task'))

    # Retrieve all tasks (visible to all users)
    tasks = Task.query.all()

    # Handle sorting
    sort_by = request.args.get('sort_by')
    sort_order = request.args.get('sort_order', 'asc')  # Default to ascending if not specified

    if sort_by:
        if sort_order == 'asc':
            tasks = sorted(tasks, key=lambda x: getattr(x, sort_by).lower() if isinstance(getattr(x, sort_by), str) else getattr(x, sort_by))
        else:
            tasks = sorted(tasks, key=lambda x: getattr(x, sort_by).lower() if isinstance(getattr(x, sort_by), str) else getattr(x, sort_by), reverse=True)

    return render_template('task.html', form=form, tasks=tasks, is_admin=is_admin)



@app.route('/task/<int:task_id>/in-progress', methods=['POST'])
@login_required
def mark_in_progress(task_id):
    task = Task.query.get_or_404(task_id)
    task.status = 'In Progress'
    db.session.commit()
    return redirect(url_for('task'))


@app.route('/task/<int:task_id>/done', methods=['POST'])
@login_required
def mark_done(task_id):
    task = Task.query.get_or_404(task_id)
    task.status = 'Done'
    db.session.commit()
    return redirect(url_for('task'))

@app.route('/task/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    if current_user.role != 'admin':  # Only admins can delete
        flash('Only admins can delete tasks.', 'danger')
        return redirect(url_for('task'))

    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('task'))

@app.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    if current_user.role != 'admin':  # Only admins can edit
        flash('Only admins can edit tasks.', 'danger')
        return redirect(url_for('task'))
    
    task = Task.query.get_or_404(task_id)
    form = TaskForm()
    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.priority = form.priority.data
        task.deadline = date(
            int(form.deadline_year.data), 
            int(form.deadline_month.data), 
            int(form.deadline_day.data)
        )
        db.session.commit()
        flash('Task updated successfully!', 'success')
        return redirect(url_for('task'))

    # Populate form with current task data
    form.title.data = task.title
    form.description.data = task.description
    form.priority.data = task.priority
    form.deadline_month.data = task.deadline.month
    form.deadline_day.data = task.deadline.day
    form.deadline_year.data = task.deadline.year

    return render_template('edit_task.html', form=form, task=task)


@app.route('/show_task')
@login_required
def show_task():
    tasks = Task.query.all()  # Retrieve all tasks, not just for the logged-in user
    return render_template('task.html', tasks=tasks)

# Decorator to restrict access to admins only
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/promote/<int:user_id>')
@login_required
def promote_user(user_id):
    if current_user.role != 'admin':  # Only admins can promote users
        abort(403)
    user = User.query.get_or_404(user_id)
    user.role = 'admin'
    db.session.commit()
    flash(f'{user.username} has been promoted to admin.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/demote/<int:user_id>')
@login_required
def demote_user(user_id):
    if current_user.role != 'admin':  # Only admins can demote users
        abort(403)
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':  # Ensure only admins are demoted
        user.role = 'user'
        db.session.commit()
        flash(f'{user.username} has been demoted to user.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/update_task/<int:task_id>', methods=['POST'])
@login_required
def update_task(task_id):
    task = Task.query.get(task_id)
    
    if task and task.user_id == current_user.id:  # Ensure user can only update their own tasks
        task.status = 'To Do'
        db.session.commit()
        flash('Task status updated to "To Do"!', 'success')
    else:
        flash('Task not found or you do not have permission to update it.', 'danger')

    return redirect(url_for('task'))

@app.route('/mark_todo/<int:task_id>', methods=['POST'])
def mark_todo(task_id):
    # Logic to update the task's status to "To Do"
    task = Task.query.get(task_id)  # Adjust this line according to your ORM
    if task:
        task.status = 'To Do'
        db.session.commit()  # Make sure to commit the changes
    return redirect(url_for('task'))  # Redirect back to the task page

from app import db, app
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
