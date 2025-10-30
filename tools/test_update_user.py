from flask import Flask
from app.entity.models import db, User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    ok, msg = User.create_with_profile('Person in Need', 'testuser', 'pass', True, 'Test User', 'test@example.com', '1234')
    u = User.query.filter_by(username='testuser').first()
    print('created:', u.username, 'is_active=', u.is_active)

    # Update with active=None -> should NOT change is_active
    res = User.update_with_profile(u.id, u.role, u.username, '', None, 'New Name', 'new@example.com', '5555')
    u2 = User.query.get(u.id)
    print('after update with active=None -> is_active=', u2.is_active)

    # Update with active='off' -> should set is_active False
    res2 = User.update_with_profile(u.id, u.role, u.username, '', 'off', 'New Name', 'new@example.com', '5555')
    u3 = User.query.get(u.id)
    print('after update with active="off" -> is_active=', u3.is_active)
