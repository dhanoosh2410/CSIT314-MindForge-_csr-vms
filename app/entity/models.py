
# ENTITY: Database models and data persistence (maps to tables)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib, random

db = SQLAlchemy()

class User(db.Model):  # ENTITY
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    profile = db.relationship('UserProfile', backref='user', uselist=False)

    def set_password(self, raw):
        self.password_hash = hashlib.sha256(raw.encode()).hexdigest()

    def check_password(self, raw):
        return self.password_hash == hashlib.sha256(raw.encode()).hexdigest()

class UserProfile(db.Model):  # ENTITY
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    full_name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))

class Category(db.Model):  # ENTITY
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

class Request(db.Model):  # ENTITY
    id = db.Column(db.Integer, primary_key=True)
    pin_id = db.Column(db.Integer, db.ForeignKey('user.id'))   # PIN owner
    title = db.Column(db.String(120))
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='open')  # open/completed
    views_count = db.Column(db.Integer, default=0)
    shortlist_count = db.Column(db.Integer, default=0)

    category = db.relationship('Category')
    pin = db.relationship('User', foreign_keys=[pin_id])

class Shortlist(db.Model):  # ENTITY
    id = db.Column(db.Integer, primary_key=True)
    csr_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    csr = db.relationship('User', foreign_keys=[csr_id])
    request = db.relationship('Request')

class ServiceHistory(db.Model):  # ENTITY
    id = db.Column(db.Integer, primary_key=True)
    csr_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    pin_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    date_completed = db.Column(db.DateTime, default=datetime.utcnow)
    csr = db.relationship('User', foreign_keys=[csr_id])
    pin = db.relationship('User', foreign_keys=[pin_id])
    request = db.relationship('Request')
    category = db.relationship('Category')

def seed_database():
    # Seed categories if empty
    if not Category.query.first():
        for n in ['Medical Escort','Grocery Run','Wheelchair Repair','Tutoring','Home Maintenance']:
            db.session.add(Category(name=n))
        db.session.commit()

    # Seed users (4 fixed + 100 random profiles) if empty
    if not User.query.first():
        def mk_user(role, username, pwd, active=True):
            u = User(role=role, username=username, is_active=active)
            u.set_password(pwd)
            db.session.add(u)
            db.session.flush()
            p = UserProfile(user_id=u.id, full_name=f'{role} {u.id}', email=f'{username}@example.com', phone='9999-0000')
            db.session.add(p)
            return u

        mk_user('User Admin', 'user_admin1', 'user_admin1!')
        mk_user('CSR Representative', 'csr_user1', 'csr_user1!')
        mk_user('Person in Need', 'pin_user1', 'pin_user1!')
        mk_user('Platform Manager', 'pm_user1', 'pm_user1!')

        roles = ['Person in Need','CSR Representative']
        for i in range(1, 101):
            role = random.choice(roles)
            u = User(role=role, username=f'{role.split()[0].lower()}{i}', is_active=True)
            u.set_password('pass'+str(i))
            db.session.add(u); db.session.flush()
            db.session.add(UserProfile(user_id=u.id, full_name=f'Test User {i}', email=f'user{i}@example.com', phone=f'9000{i:04d}'))
        db.session.commit()

    # Seed demo requests & histories if empty
    if not Request.query.first():
        pins = User.query.filter_by(role='Person in Need').all()
        cats = Category.query.all()
        for i in range(40):
            pin = random.choice(pins)
            cat = random.choice(cats)
            r = Request(pin_id=pin.id, title=f'{cat.name} help #{i+1}', description='Auto-seeded request', category_id=cat.id, status='open')
            db.session.add(r)
        db.session.commit()
