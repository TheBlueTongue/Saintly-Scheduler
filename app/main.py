from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from .models import Task
from . import db
from .forms import TaskForm

# Initialize the Blueprint for the main routes
main = Blueprint('main', __name__)

# Route to display the list of tasks
@main.route('/tasks', methods=['GET', 'POST'])
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
        
        # Add the task to the database and commit
        db.session.add(task)
        db.session.commit()

        # Flash a success message and redirect to tasks page
        flash('Your task has been added!', 'success')
        return redirect(url_for('main.tasks'))
    
    # Query the database for the current user's tasks
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    
    # Render the tasks page with the task form and tasks list
    return render_template('task.html', form=form, tasks=tasks)

# Route to update a task (mark as complete or edit)
@main.route('/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)  # Fetch the task or return 404 if not found

    if task.user_id != current_user.id:
        flash('You cannot edit this task!', 'danger')
        return redirect(url_for('main.tasks'))

    form = TaskForm(obj=task)  # Pre-fill the form with the task's current data

    if form.validate_on_submit():
        # Update task fields
        task.title = form.title.data
        task.description = form.description.data
        task.category = form.category.data
        task.due_date = form.due_date.data

        db.session.commit()  # Commit the changes to the database

        flash('Your task has been updated!', 'success')
        return redirect(url_for('main.tasks'))
    
    # Render the task edit page with the existing form data
    return render_template('edit_task.html', form=form, task=task)

# Route to delete a task
@main.route('/tasks/delete/<int:task_id>', methods=['GET', 'POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)  # Fetch the task or return 404 if not found

    if task.user_id != current_user.id:
        flash('You cannot delete this task!', 'danger')
        return redirect(url_for('main.tasks'))

    db.session.delete(task)  # Delete the task from the database
    db.session.commit()

    flash('Your task has been deleted.', 'success')
    return redirect(url_for('main.tasks'))
