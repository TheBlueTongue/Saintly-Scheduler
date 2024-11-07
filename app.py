# app.py
from flask import Flask, Blueprint, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from datetime import datetime

# Initialize Flask app and database
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    tasks = db.relationship('Task', backref='owner', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    is_complete = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Forms
class TaskForm(FlaskForm):
    title = StringField('Task Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    category = StringField('Category', validators=[DataRequired()])
    due_date = DateField('Due Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Add Task')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Load user function for login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return redirect(url_for('tasks'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('tasks'))
        flash('Login failed. Check your credentials and try again.', 'danger')
    return render_template('login.html', form=form)

@app.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    form = TaskForm()  # Initialize the TaskForm
    if form.validate_on_submit():
        # Create a new task from the form data
        task = Task(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            due_date=form.due_date.data,
            user_id=current_user.id
        )
        db.session.add(task)
        db.session.commit()
        flash('Your task has been added!', 'success')
        return redirect(url_for('tasks'))
    
    # Query the database for the current user's tasks
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('task.html', form=form, tasks=tasks)

@app.route('/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('You cannot edit this task!', 'danger')
        return redirect(url_for('tasks'))

    form = TaskForm(obj=task)
    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.category = form.category.data
        task.due_date = form.due_date.data
        db.session.commit()
        flash('Your task has been updated!', 'success')
        return redirect(url_for('tasks'))

    return render_template('edit_task.html', form=form, task=task)

@app.route('/tasks/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        flash('You cannot delete this task!', 'danger')
        return redirect(url_for('tasks'))

    db.session.delete(task)
    db.session.commit()
    flash('Your task has been deleted.', 'success')
    return redirect(url_for('tasks'))

# Run the app
if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
