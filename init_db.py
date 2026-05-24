# -*- coding: utf-8 -*-
"""
Database initializer -- creates all tables and seeds a demo user.
Run this once after PostgreSQL is set up:  python init_db.py
"""
import warnings
warnings.filterwarnings('ignore')
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from app import app, bcrypt
from models import db, User, Task

with app.app_context():
    # Create all tables in PostgreSQL
    db.create_all()
    print("[OK] Tables created successfully in PostgreSQL!")

    # Seed a demo admin user if not already present
    if not User.query.filter_by(username='admin').first():
        demo_user = User(
            username='admin',
            email='admin@taskmanager.com',
            password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8')
        )
        db.session.add(demo_user)
        db.session.commit()

        # Seed some demo tasks
        demo_tasks = [
            Task(title='Set up Flask project',   description='Initialize Flask app with config', priority='high',   status='completed', user_id=demo_user.id),
            Task(title='Design database schema', description='Create User and Task models',       priority='high',   status='completed', user_id=demo_user.id),
            Task(title='Build REST API',         description='CRUD endpoints for tasks',          priority='high',   status='in_progress', user_id=demo_user.id),
            Task(title='Add WebSocket support',  description='Real-time task updates',            priority='medium', status='pending',  user_id=demo_user.id),
            Task(title='Create frontend UI',     description='Dashboard with HTML/CSS',           priority='medium', status='pending',  user_id=demo_user.id),
            Task(title='Write unit tests',       description='Test all API endpoints',            priority='low',    status='pending',  user_id=demo_user.id),
        ]
        db.session.bulk_save_objects(demo_tasks)
        db.session.commit()
        print("[OK] Demo user 'admin' created (password: admin123)")
        print("[OK] 6 sample tasks seeded!")
    else:
        print("[INFO] Admin user already exists -- skipping seed.")

print("\n[READY] Database ready! Run:  python app.py")