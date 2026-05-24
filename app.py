"""
Task Management System — Flask Application
Assignment: Python Development Internship
"""
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit
from models import db, User, Task
from analytics import get_task_analytics

# ── App Configuration ──────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = 'taskmanager_secret_2024'

# PostgreSQL connection string — update credentials if different
DB_USER     = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'admin123')
DB_HOST     = os.environ.get('DB_HOST', 'localhost')
DB_PORT     = os.environ.get('DB_PORT', '5432')
DB_NAME     = os.environ.get('DB_NAME', 'taskdb')

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ── Extensions ─────────────────────────────────────────────────────────────────
db.init_app(app)
bcrypt     = Bcrypt(app)
socketio   = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')
login_mgr  = LoginManager(app)
login_mgr.login_view = 'login'

@login_mgr.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ══════════════════════════════════════════════════════════════════════════════
#  AUTH ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user     = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid username or password.')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if User.query.filter_by(username=username).first():
            return render_template('login.html', reg_error='Username already taken.', tab='register')
        if User.query.filter_by(email=email).first():
            return render_template('login.html', reg_error='Email already registered.', tab='register')

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user  = User(username=username, email=email, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))

    return render_template('login.html', tab='register')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/dashboard')
@login_required
def dashboard():
    analytics = get_task_analytics(current_user.id)
    tasks     = Task.query.filter_by(user_id=current_user.id).order_by(Task.created_date.desc()).all()
    return render_template('dashboard.html', analytics=analytics, tasks=tasks)


# ══════════════════════════════════════════════════════════════════════════════
#  REST API — TASKS
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/tasks', methods=['GET'])
@login_required
def get_tasks():
    """GET all tasks for the current user."""
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.created_date.desc()).all()
    return jsonify([t.to_dict() for t in tasks]), 200


@app.route('/api/tasks', methods=['POST'])
@login_required
def add_task():
    """POST — create a new task."""
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400

    task = Task(
        title       = data['title'].strip(),
        description = data.get('description', '').strip(),
        priority    = data.get('priority', 'medium'),
        status      = data.get('status', 'pending'),
        user_id     = current_user.id,
    )
    db.session.add(task)
    db.session.commit()

    # Broadcast via WebSocket
    socketio.emit('task_added', task.to_dict(), to=None)
    return jsonify(task.to_dict()), 201


@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    """PUT — update an existing task."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    data = request.get_json()
    if 'title' in data:
        task.title = data['title'].strip()
    if 'description' in data:
        task.description = data['description'].strip()
    if 'priority' in data:
        task.priority = data['priority']
    if 'status' in data:
        task.status = data['status']

    db.session.commit()

    # Broadcast via WebSocket
    socketio.emit('task_updated', task.to_dict(), to=None)
    return jsonify(task.to_dict()), 200


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    """DELETE — remove a task."""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    task_data = task.to_dict()
    db.session.delete(task)
    db.session.commit()

    # Broadcast via WebSocket
    socketio.emit('task_deleted', {'id': task_id}, to=None)
    return jsonify({'message': 'Task deleted', 'task': task_data}), 200


@app.route('/api/analytics', methods=['GET'])
@login_required
def analytics_api():
    """GET analytics summary for the current user."""
    return jsonify(get_task_analytics(current_user.id)), 200


# ══════════════════════════════════════════════════════════════════════════════
#  WEBSOCKET EVENTS
# ══════════════════════════════════════════════════════════════════════════════

@socketio.on('connect')
def handle_connect():
    emit('connected', {'message': 'WebSocket connected successfully!'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
