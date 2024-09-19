from flask import flash, render_template, request, redirect, url_for, Flask
from flask_login import login_required, current_user
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_really_secret_key'  # Заменить на уникальный и секретный ключ
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    confirmed_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<User {self.email}>'


@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        user_exist = User.query.filter_by(email=email).first()
        if user_exist:
            flash('Пользователь с таким email уже существует.', 'error')
            print('Пользователь с таким email уже существует! Авторизуйтесь.')
            return redirect(url_for('login'))

        if password != confirm_password:
            print('Пароли не совпадают')
            flash("Пароли не совпадают", "error")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(name=name, last_name=last_name, email=email, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Вы успешно зарегистрировались!", "success")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            print(f"Error occurred while adding user: {e}")
            flash(f"Ошибка при регистрации: {e}", "error")
            return redirect(url_for('register'))

    return render_template('register.html')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Вы успешно авторизовались!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверный адрес электронной почты или пароль.', 'error')
            return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/logout')
def logout():
    logout_user()
    flash('Вы успешно вышли из системы', 'success')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)


@app.route('/update_profile', methods=['POST'])
def update_profile():
    name = request.form.get('name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')

    existing_user = User.query.filter_by(email=email).first()
    if existing_user and existing_user.id != current_user.id:
        flash('Этот Email уже зарегистрирован.', 'error')
        return redirect(url_for('dashboard'))

    user = current_user
    user.name = name
    user.last_name = last_name
    user.email = email
    try:
        db.session.commit()
        flash('Профиль успешно обновлен!', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении профиля: {e}', 'error')
    return render_template('dashboard.html', user=current_user)


@app.route('/change_password', methods=['POST'])
def change_password():
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')

    if check_password_hash(current_user.password, old_password):
        current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()
        flash('Пароль успешно заменен', 'success')
        return render_template('dashboard.html', user=current_user)
    else:
        flash('Введен не верный пароль', 'error')
        return render_template('dashboard.html', user=current_user)


@app.route('/delete_profile', methods=['POST'])
def delete_profile():
    accept_password = request.form.get('accept_password')
    if check_password_hash(current_user.password, accept_password):
        user_id = current_user.id
        try:
            user = User.query.get(user_id)
            db.session.delete(user)
            db.session.commit()

            logout_user()
            flash('Ваш профиль был успешно удален.', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при удалении профиля: {e}', 'error')
            return redirect(url_for('dashboard'))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
