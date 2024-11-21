from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from database_setup import SessionLocal, User, Task
import forms
from flask import request
from datetime import datetime
from datetime import timedelta
from flask import request, redirect, url_for, render_template

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

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/profile', methods=['GET'])
@login_required
def user_profile():
    session = SessionLocal()
    
    # Calculate stats for the user
    user_stats = {
        "tasks_created": session.query(Task).filter_by(user_id=current_user.id).count(),
        "tasks_completed": session.query(Task).filter_by(user_id=current_user.id, is_complete=True).count(),
        "completion_rate": round(
            (session.query(Task).filter_by(user_id=current_user.id, is_complete=True).count() /
             max(session.query(Task).filter_by(user_id=current_user.id).count(), 1)) * 100, 2),
        
        "first_task_date": session.query(Task).filter_by(user_id=current_user.id).order_by(Task.created_at.asc()).first().created_at
    }
    
    session.close()  # Close the session
    return render_template('user_profile.html', stats=user_stats)


@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    # Update user details
    current_user.username = username
    current_user.email = email
    if password:  # Update password only if provided
        current_user.set_password(password)
    
    session = SessionLocal()  # Ensure session is created here
    session.commit()
    flash('Profile updated successfully!', 'success')
    session.close()  # Make sure to close the session after commit
    return redirect(url_for('user_profile'))




@app.route('/todays_tasks')
@login_required
def todays_tasks():
    session = SessionLocal()
    today = datetime.now().date()
    tasks_due_today = session.query(Task).filter_by(user_id=current_user.id).filter(Task.due_date == today).all()
    session.close()
    
    return render_template('todays_tasks.html', tasks=tasks_due_today)


# Route for displaying the list of tasks and adding a new task
@app.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    form = forms.TaskForm()
    session = SessionLocal()

    # Check if a new task is being submitted
    if form.validate_on_submit():
        new_task = Task(
            title=form.title.data,
            category=form.category.data,
            due_date=form.due_date.data,
            user_id=current_user.id
        )
        session.add(new_task)
        session.commit()
        
        return redirect(url_for('tasks'))

    # Get sorting parameters from the request arguments, defaulting to 'due_date' and 'asc'
    sort_by = request.args.get('sort_by', 'due_date')
    order = request.args.get('order', 'asc')

    # Determine the column to sort by based on the `sort_by` parameter
    if sort_by == 'title':
        order_column = Task.title
    elif sort_by == 'category':
        order_column = Task.category
    else:
        order_column = Task.due_date  # Default to sorting by due date

    # Apply ordering based on the `order` parameter
    if order == 'desc':
        order_column = order_column.desc()

    # Query the tasks with sorting applied
    user_tasks = session.query(Task).filter_by(user_id=current_user.id).order_by(order_column).all()

    # Calculate days until due for each task
    current_date = datetime.now().date()
    tasks_with_days_until_due = [
        {
            'task': task,
            'days_until_due': (task.due_date - current_date).days if task.due_date else None
        }
        for task in user_tasks
    ]

    # Close the session
    session.close()

    # Render the template with tasks, current sorting parameters, and days until due
    return render_template(
        'tasks.html',
        form=form,
        tasks=tasks_with_days_until_due,
        sort_by=sort_by,
        order=order)


# Route for editing an existing task
@app.route('/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    session = SessionLocal()
    task = session.query(Task).get(task_id)
    
    # If the task doesn't exist or belongs to another user, redirect
    if not task or task.user_id != current_user.id:
        return redirect(url_for('tasks'))

    # Populate the form with the task data
    form = forms.TaskForm(obj=task)
    
    if form.validate_on_submit():
        # Update task fields with the new data from the form
        task.title = form.title.data
        task.category = form.category.data
        task.due_date = form.due_date.data
        task.description = form.description.data  # Ensure description is updated
        
        session.commit()
        
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
            description=form.description.data,
            due_date=form.due_date.data,
            user_id=current_user.id
        )
        session.add(new_task)
        session.commit()
        session.close()
        
        return redirect(url_for('tasks'))
    return render_template('add_task.html', form=form)

@app.route('/toggle_task_completion/<int:task_id>', methods=['POST'])
@login_required
def toggle_task_completion(task_id):
    session = SessionLocal()
    task = session.query(Task).get(task_id)
    if task and task.user_id == current_user.id:
        task.is_complete = not task.is_complete
        session.commit()
    
    session.close()
    
    # Get the sorting parameters from the form
    sort_by = request.form.get('sort_by', 'title')
    order = request.form.get('order', 'asc')
    
    # Redirect back to tasks with sorting applied
    return redirect(url_for('tasks', sort_by=sort_by, order=order))

@app.route('/task/<int:task_id>')
@login_required
def task_detail(task_id):
    session = SessionLocal()
    task = session.query(Task).filter_by(id=task_id, user_id=current_user.id).first()
    session.close()
    
    if task is None:
        flash('Task not found.', 'danger')
        return redirect(url_for('tasks'))
    
    return render_template('task_detail.html', task=task)





if __name__ == '__main__':
    app.run(debug=True)

