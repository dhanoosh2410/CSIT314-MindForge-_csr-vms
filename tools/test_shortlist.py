from flask import Flask
from app.entity.models import db, User, Request, Shortlist, Category

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    # create roles
    csr = User(role='CSR Representative', username='csr_test', is_active=True)
    csr.set_password('pass')
    db.session.add(csr); db.session.flush()
    csr_p = User(role='Person in Need', username='pin_test', is_active=True)
    csr_p.set_password('pass')
    db.session.add(csr_p); db.session.flush()

    cat = Category(name='TestCat')
    db.session.add(cat); db.session.flush()

    r = Request(pin_id=csr_p.id, title='Need help', description='Test', category_id=cat.id)
    db.session.add(r); db.session.commit()

    print('Initial shortlist_count =', r.shortlist_count)

    # CSR adds shortlist
    Shortlist.add_if_not_exists(csr.id, r.id)
    r2 = Request.query.get(r.id)
    print('After one add, shortlist_count =', r2.shortlist_count)

    # Duplicate add should not increment
    Shortlist.add_if_not_exists(csr.id, r.id)
    r3 = Request.query.get(r.id)
    print('After duplicate add, shortlist_count =', r3.shortlist_count)

    # Another CSR adds
    csr2 = User(role='CSR Representative', username='csr_test2', is_active=True)
    csr2.set_password('pass')
    db.session.add(csr2); db.session.flush()
    Shortlist.add_if_not_exists(csr2.id, r.id)
    r4 = Request.query.get(r.id)
    print('After second csr add, shortlist_count =', r4.shortlist_count)

    # Remove one shortlist
    Shortlist.remove_if_exists(csr2.id, r.id)
    r5 = Request.query.get(r.id)
    print('After remove by second csr, shortlist_count =', r5.shortlist_count)

    # Remove non-existing should be safe
    removed = Shortlist.remove_if_exists(9999, r.id)
    print('Remove non-existing returned', removed, 'and count =', Request.query.get(r.id).shortlist_count)
