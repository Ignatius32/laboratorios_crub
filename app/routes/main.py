from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.rol == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('tecnicos.dashboard'))
    return render_template('index.html', title='Inicio')

@main.route('/about')
def about():
    return render_template('about.html', title='Acerca de')