
# ENTITY: Database models and data persistence (maps to tables)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib, random

db = SQLAlchemy()

# The four fixed “User Accounts" used by admin listing logic
FIXED_ACCOUNTS = {
    ('User Admin', 'user_admin1'),
    ('CSR Representative', 'csr_user1'),
    ('Person in Need', 'pin_user1'),
    ('Platform Manager', 'pm_user1'),
}

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

    @classmethod
    def login(cls, role, username, password):
        # authenticate a user by role, username and password.
        # returns the User instance if credentials are valid and the user is active, otherwise returns None
        user = cls.query.filter_by(username=username, role=role).first()
        if user and user.is_active and user.check_password(password):
            return user
        return None
    @classmethod
    def create_with_profile(cls, role, username, password, active, full_name, email, phone):
        if cls.query.filter_by(username=username).first():
            return False, "Username exists."
        u = cls(role=role, username=username, is_active=active)
        u.set_password(password)
        db.session.add(u)
        db.session.flush()
        p = UserProfile(user_id=u.id, full_name=full_name, email=email, phone=phone)
        db.session.add(p)
        db.session.commit()
        return True, "User created."

    @classmethod
    def update_with_profile(cls, user_id, role, username, password, active, full_name, email, phone):
        u = cls.query.get(user_id)
        if not u:
            return False, "User not found."
        u.role = role
        u.username = username
        # prevents suspension on updating a user
        if active is not None:
            if isinstance(active, str):
                u.is_active = active.lower() in ('on', 'true', '1')
            else:
                u.is_active = bool(active)
        if password:
            u.set_password(password)
        if not u.profile:
            u.profile = UserProfile(user_id=u.id)
        u.profile.full_name = full_name
        u.profile.email = email
        u.profile.phone = phone
        db.session.commit()
        return True, "User updated."

    @classmethod
    def suspend_user(cls, user_id):
        u = cls.query.get(user_id)
        if u:
            u.is_active = False
            db.session.commit()

    @classmethod
    def activate_user(cls, user_id):
        u = cls.query.get(user_id)
        if u:
            u.is_active = True
            db.session.commit()

    @classmethod
    def search_users(cls, q: str = "", user_type: str = "accounts", page: int = 1, per_page: int = 20):
        # user_type: 'accounts' (only the four fixed accounts) or 'profiles' (everything else)
        query = cls.query
        # filter by type
        if user_type == 'accounts':
            ors = [ (cls.role == r) & (cls.username == u) for (r, u) in FIXED_ACCOUNTS ]
            f = ors[0]
            for cond in ors[1:]:
                f = f | cond
            query = query.filter(f)
        else:
            # profiles = NOT the four fixed accounts
            for (r, u) in FIXED_ACCOUNTS:
                query = query.filter(~((cls.role == r) & (cls.username == u)))

        # optional free-text search
        if q:
            like = f"%{q}%"
            query = query.join(UserProfile, isouter=True).filter(
                (cls.username.like(like)) |
                (cls.role.like(like)) |
                (UserProfile.full_name.like(like)) |
                (UserProfile.email.like(like))
            )

        query = query.order_by(cls.id.asc())
        pag = query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            "items": pag.items,
            "total": pag.total,
            "page": pag.page,
            "per_page": per_page,
            "pages": pag.pages,
        }

class UserProfile(db.Model):  # ENTITY
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    full_name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))

class Category(db.Model):  # ENTITY
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    @classmethod
    def get_all(cls):
        return cls.query.order_by(cls.name).all()

    @classmethod
    def search(cls, q):
        query = cls.query
        if q:
            query = query.filter(cls.name.like(f"%{q}%"))
        return query.order_by(cls.name).all()

    @classmethod
    def get_by_id(cls, cat_id):
    	# return the Category instance or None for the given id
        if cat_id is None:
            return None
        return cls.query.get(cat_id)

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

    @classmethod
    def list_open(cls, category_id=None):
        query = cls.query.filter_by(status='open')
        if category_id:
            query = query.filter_by(category_id=category_id)
        items = query.order_by(cls.created_at.desc()).all()
        # increment views_count for these items (approximate listing views)
        for r in items:
            r.views_count = (r.views_count or 0) + 1
        db.session.commit()
        return items

    @classmethod
    def paginate_open(cls, category_id=None, page=1, per_page=12):
        # return a paginated dict of open requests and increment views for the page's items
        # { items, total, page, per_page, pages }
        query = cls.query.filter_by(status='open')
        if category_id:
            query = query.filter_by(category_id=category_id)
        query = query.order_by(cls.created_at.desc())
        pag = query.paginate(page=page, per_page=per_page, error_out=False)
        items = pag.items
        # increase views for only the returned items
        for r in items:
            r.views_count = (r.views_count or 0) + 1
        db.session.commit()
        return {
            'items': items,
            'total': pag.total,
            'page': pag.page,
            'per_page': pag.per_page,
            'pages': pag.pages,
        }

    @classmethod
    def get_if_open(cls, req_id):
        # return the Request when it exists and is open, otherwise None
        r = cls.query.get(req_id)
        if not r or r.status != 'open':
            return None
        return r

    @classmethod
    def create_for_pin(cls, pin_id, title, description, category_id):
        r = cls(pin_id=pin_id, title=title, description=description, category_id=category_id, status='open')
        db.session.add(r)
        db.session.commit()
        return r

    @classmethod
    def update_by_id(cls, req_id, title, description, category_id, status):
        r = cls.query.get(req_id)
        if not r:
            return False
        r.title = title
        r.description = description
        r.category_id = category_id
        r.status = status
        db.session.commit()
        return True

    @classmethod
    def delete_by_id(cls, req_id):
        r = cls.query.get(req_id)
        if r:
            db.session.delete(r)
            db.session.commit()

    @classmethod
    def search_by_pin(cls, pin_id, q=None):
        query = cls.query.filter_by(pin_id=pin_id)
        if q:
            like = f"%{q}%"
            query = query.filter((cls.title.like(like)) | (cls.description.like(like)))
        return query.order_by(cls.created_at.desc()).all()

    @classmethod
    def get_for_pin(cls, req_id, pin_id):
        # return the request if it exists and belongs to pin_id, otherwise None
        r = cls.query.get(req_id)
        if not r or r.pin_id != pin_id:
            return None
        return r

class Shortlist(db.Model):  # ENTITY
    id = db.Column(db.Integer, primary_key=True)
    csr_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    csr = db.relationship('User', foreign_keys=[csr_id])
    request = db.relationship('Request')

    @classmethod
    def add_if_not_exists(cls, csr_id, request_id):
        exists = cls.query.filter_by(csr_id=csr_id, request_id=request_id).first()
        if not exists:
            db.session.add(cls(csr_id=csr_id, request_id=request_id))
            # increase shortlist count on request
            r = Request.query.get(request_id)
            if r:
                r.shortlist_count = (r.shortlist_count or 0) + 1
            db.session.commit()

    @classmethod
    def exists(cls, csr_id, request_id):
        # return True if a shortlist record exists for csr_id/request_id
        return cls.query.filter_by(csr_id=csr_id, request_id=request_id).first() is not None

    @classmethod
    def for_csr(cls, csr_id):
        return cls.query.filter_by(csr_id=csr_id).order_by(cls.created_at.desc()).all()

    @classmethod
    def search_for_csr(cls, csr_id, q=None):
        query = cls.query.filter_by(csr_id=csr_id).join(Request)
        if q:
            like = f"%{q}%"
            query = query.filter((Request.title.like(like)) | (Request.description.like(like)))
        return query.order_by(cls.created_at.desc()).all()

    @classmethod
    def remove_if_exists(cls, csr_id, request_id):
        rec = cls.query.filter_by(csr_id=csr_id, request_id=request_id).first()
        if rec:
            r = Request.query.get(request_id)
            if r and (r.shortlist_count or 0) > 0:
                r.shortlist_count = (r.shortlist_count or 0) - 1
            db.session.delete(rec)
            db.session.commit()
            return True
        return False

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

    @classmethod
    def filter_history(cls, category_id=None, start=None, end=None):
        q = cls.query
        if category_id:
            q = q.filter_by(category_id=category_id)
        if start:
            q = q.filter(cls.date_completed >= start)
        if end:
            q = q.filter(cls.date_completed <= end)
        return q.order_by(cls.date_completed.desc()).all()

    @classmethod
    def filter_for_pin(cls, pin_id, category_id=None, start=None, end=None):
        # return completed matches for a specific PIN (pin_id) with optional filters
        q = cls.query.filter_by(pin_id=pin_id)
        if category_id:
            q = q.filter_by(category_id=category_id)
        if start:
            q = q.filter(cls.date_completed >= start)
        if end:
            q = q.filter(cls.date_completed <= end)
        return q.order_by(cls.date_completed.desc()).all()

    @classmethod
    def filter_for_csr(cls, csr_id, category_id=None, start=None, end=None):
        # return completed matches for a specific CSR (csr_id) with optional filters
        q = cls.query.filter_by(csr_id=csr_id)
        if category_id:
            q = q.filter_by(category_id=category_id)
        if start:
            q = q.filter(cls.date_completed >= start)
        if end:
            q = q.filter(cls.date_completed <= end)
        return q.order_by(cls.date_completed.desc()).all()

    @classmethod
    def paginate_for_csr(cls, csr_id, category_id=None, start=None, end=None, page=1, per_page=12):
        # return a paginated dict of completed matches for a specific CSR.
        # { items, total, page, per_page, pages }
        q = cls.query.filter_by(csr_id=csr_id)
        if category_id:
            q = q.filter_by(category_id=category_id)
        if start:
            q = q.filter(cls.date_completed >= start)
        if end:
            q = q.filter(cls.date_completed <= end)
        pag = q.order_by(cls.date_completed.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return {
            'items': pag.items,
            'total': pag.total,
            'page': pag.page,
            'per_page': pag.per_page,
            'pages': pag.pages,
        }

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
