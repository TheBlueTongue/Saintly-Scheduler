from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from database_setup import SessionLocal, User, Task
import forms

# Set up Flask app and login manager
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a real secret key

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login page if user is not authenticated

# Route for the welcome page
@app.route('/')
def welcome():
    return render_template('welcome.html')

# Session management function
@login_manager.user_loader
def load_user(user_id):
    session = SessionLocal()
    user = session.query(User).get(int(user_id))
    session.close()
    return user

# Route for registering a new user
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        session = SessionLocal()
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(username=form.username.data, password=hashed_password)
        session.add(new_user)
        try:
            session.commit()
            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            session.rollback()
            flash('Username already exists. Please choose a different one.', 'danger')
        finally:
            session.close()
    return render_template('register.html', form=form)

# Route for logging in an existing user
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        session = SessionLocal()
        user = session.query(User).filter_by(username=form.username.data).first()
        session.close()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('tasks'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

# Route for logging out
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

# Route for displaying the list of tasks and adding a new task
@app.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    form = forms.TaskForm()
    session = SessionLocal()
    if form.validate_on_submit():
        new_task = Task(
            title=form.title.data,
            category=form.category.data,
            due_date=form.due_date.data,
            user_id=current_user.id
        )
        session.add(new_task)
        session.commit()
        flash('Task added successfully!', 'success')
        return redirect(url_for('tasks'))
    
    user_tasks = session.query(Task).filter_by(user_id=current_user.id).all()
    session.close()
    return render_template('tasks.html', form=form, tasks=user_tasks)

# Route for editing an existing task
@app.route('/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    session = SessionLocal()
    task = session.query(Task).get(task_id)
    if not task or task.user_id != current_user.id:
        flash('Task not found or access denied', 'danger')
        return redirect(url_for('tasks'))

    form = forms.TaskForm(obj=task)
    if form.validate_on_submit():
        task.title = form.title.data
        task.category = form.category.data
        task.due_date = form.due_date.data
        session.commit()
        flash('Task updated successfully!', 'success')
        return redirect(url_for('tasks'))
    
    session.close()
    return render_template('edit_task.html', form=form, task=task)

# Route for deleting a task
@app.route('/tasks/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    session = SessionLocal()
    task = session.query(Task).get(task_id)
    if task and task.user_id == current_user.id:
        session.delete(task)
        session.commit()
        flash('Task deleted successfully', 'success')
    else:
        flash('Task not found or access denied', 'danger')
    
    session.close()
    return redirect(url_for('tasks'))

@app.route('/tasks/add', methods=['GET', 'POST'])
@login_required
def add_task():
    form = forms.TaskForm()
    if form.validate_on_submit():
        session = SessionLocal()
        new_task = Task(
            title=form.title.data,
            category=form.category.data,
            due_date=form.due_date.data,
            user_id=current_user.id
        )
        session.add(new_task)
        session.commit()
        session.close()
        flash('Task added successfully!', 'success')
        return redirect(url_for('tasks'))
    return render_template('add_task.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)

