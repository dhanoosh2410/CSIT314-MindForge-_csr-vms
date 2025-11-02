# ENTITY + Use-case coordination in one place (per your lecture guidance)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import or_, text
from sqlalchemy.sql import func  # <-- added for PM reports
import hashlib, random
import random

db = SQLAlchemy()

# Fixed demo accounts (exactly these 4)
FIXED_ACCOUNTS = {
    ('User Admin', 'user_admin1'),
    ('CSR Representative', 'csr_user1'),
    ('Person in Need', 'pin_user1'),
    ('Platform Manager', 'pm_user1'),
}

# =========================
# Entity: User (logins)
# =========================
class User(db.Model):
    """
    Maps to 'user_accounts' table. Real authentication happens here.
    """
    __tablename__ = 'user_accounts'

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, raw: str):
        self.password_hash = hashlib.sha256(raw.encode()).hexdigest()

    def check_password(self, raw: str) -> bool:
        return self.password_hash == hashlib.sha256(raw.encode()).hexdigest()

    @classmethod
    def login(cls, role, username, password):
        u = cls.query.filter_by(username=username, role=role).first()
        if u and u.is_active and u.check_password(password):
            return u
        return None

    # Keep signatures used by boundary; profile args ignored (profiles are standalone now)
    @classmethod
    def create_with_profile(cls, role, username, password, active, full_name, email, phone):
        if cls.query.filter_by(username=username).first():
            return False, "Username exists."
        u = cls(role=role, username=username, is_active=bool(active))
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        return True, "User created."

    @classmethod
    def update_with_profile(cls, user_id, role, username, password, active, full_name, email, phone):
        u = cls.query.get(user_id)
        if not u:
            return False, "User not found."
        u.role = role
        u.username = username
        if active is not None:
            if isinstance(active, str):
                u.is_active = active.lower() in ('on','true','1')
            else:
                u.is_active = bool(active)
        if password:
            u.set_password(password)
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
    def search_accounts_fixed_four(cls, q: str = "", page: int = 1, per_page: int = 20):
        """
        Return ONLY the four fixed accounts from user_accounts.
        """
        query = cls.query
        ors = [ (cls.role == r) & (cls.username == u) for (r, u) in FIXED_ACCOUNTS ]
        f = ors[0]
        for cond in ors[1:]:
            f = f | cond
        query = query.filter(f)

        if q:
            like = f"%{q}%"
            query = query.filter((cls.username.like(like)) | (cls.role.like(like)))

        query = query.order_by(cls.id.asc())
        pag = query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            "items": pag.items,
            "total": pag.total,
            "page": pag.page,
            "per_page": per_page,
            "pages": pag.pages,
        }


# =========================
# Entity: UserProfile (standalone, no FK to User)
# =========================
class UserProfile(db.Model):
    """
    Standalone profiles table with NO user_id link.
    """
    __tablename__ = 'user_profiles'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))

    # NEW: allow suspending/activating profiles, as per user stories
    is_active = db.Column(db.Boolean, default=True)

    @classmethod
    def create_profile(cls, full_name: str, email: str, phone: str, active: bool = True):
        """
        Create a standalone profile (name/email/phone/active flag).
        """
        p = cls(
            full_name=(full_name or '').strip(),
            email=(email or '').strip(),
            phone=(phone or '').strip(),
            is_active=bool(active),
        )
        db.session.add(p)
        db.session.commit()
        return True, "Profile created."

    @classmethod
    def update_profile(cls, profile_id: int, full_name: str, email: str, phone: str, active=None):
        """
        Update profile fields. If `active` is provided, toggles profile status.
        """
        p = cls.query.get(profile_id)
        if not p:
            return False, "Profile not found."
        p.full_name = (full_name or '').strip()
        p.email = (email or '').strip()
        p.phone = (phone or '').strip()
        if active is not None:
            if isinstance(active, str):
                p.is_active = active.lower() in ('on', 'true', '1')
            else:
                p.is_active = bool(active)
        db.session.commit()
        return True, "Profile updated."

    @classmethod
    def suspend_profile(cls, profile_id: int) -> None:
        p = cls.query.get(profile_id)
        if p:
            p.is_active = False
            db.session.commit()

    @classmethod
    def activate_profile(cls, profile_id: int) -> None:
        p = cls.query.get(profile_id)
        if p:
            p.is_active = True
            db.session.commit()

    @classmethod
    def search_profiles(cls, q: str = "", page: int = 1, per_page: int = 20):
        query = cls.query
        if q:
            like = f"%{q}%"
            query = query.filter(
                (cls.full_name.like(like)) |
                (cls.email.like(like)) |
                (cls.phone.like(like))
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


# =========================
# Entity: Category
# =========================
class Category(db.Model):
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
        if cat_id is None:
            return None
        return cls.query.get(cat_id)


# =========================
# Entity: Request (+ helpers)
# =========================
class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # PIN owner (optional for demo rows)
    pin_id = db.Column(db.Integer, db.ForeignKey('user_accounts.id'), nullable=True)
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
        for r in items:
            r.views_count = (r.views_count or 0) + 1
        db.session.commit()
        return items

    @classmethod
    def paginate_open(cls, category_id=None, page=1, per_page=12):
        query = cls.query.filter_by(status='open')
        if category_id:
            query = query.filter_by(category_id=category_id)
        query = query.order_by(cls.created_at.desc())
        pag = query.paginate(page=page, per_page=per_page, error_out=False)
        items = pag.items
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
    def paginate_open_no_increment(cls, category_id=None, page=1, per_page=12):
        query = cls.query.filter_by(status='open')
        if category_id:
            query = query.filter_by(category_id=category_id)
        query = query.order_by(cls.created_at.desc())
        pag = query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            'items': pag.items,
            'total': pag.total,
            'page': pag.page,
            'per_page': pag.per_page,
            'pages': pag.pages,
        }

    @classmethod
    def get_if_open(cls, req_id):
        r = cls.query.get(req_id)
        if not r or r.status != 'open':
            return None
        return r

    @classmethod
    def increment_views(cls, req_id):
        r = cls.query.get(req_id)
        if not r:
            return
        r.views_count = (r.views_count or 0) + 1
        db.session.commit()

    @classmethod
    def increment_views_bulk(cls, req_ids):
        if not req_ids:
            return
        rows = cls.query.filter(cls.id.in_(req_ids)).all()
        for r in rows:
            r.views_count = (r.views_count or 0) + 1
        db.session.commit()

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
        prev_status = r.status
        r.title = title
        r.description = description
        r.category_id = category_id
        r.status = status
        try:
            if prev_status != 'completed' and status == 'completed':
                sh = ServiceHistory(pin_id=r.pin_id, csr_id=None, request_id=r.id, category_id=r.category_id)
                db.session.add(sh)
        except Exception:
            pass
        db.session.commit()
        return True

    @classmethod
    def delete_by_id(cls, req_id):
        r = cls.query.get(req_id)
        if r:
            try:
                Shortlist.query.filter_by(request_id=req_id).delete()
            except Exception:
                pass
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
    def paginate_for_pin(cls, pin_id, q=None, page=1, per_page=12):
        query = cls.query.filter_by(pin_id=pin_id)
        query = query.filter(cls.status != 'completed')
        if q:
            like = f"%{q}%"
            query = query.filter((cls.title.like(like)) | (cls.description.like(like)))
        pag = query.order_by(cls.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return {
            'items': pag.items,
            'total': pag.total,
            'page': pag.page,
            'per_page': pag.per_page,
            'pages': pag.pages,
        }

    @classmethod
    def get_for_pin(cls, req_id, pin_id):
        r = cls.query.get(req_id)
        if not r or r.pin_id != pin_id:
            return None
        if r.status == 'completed':
            return None
        return r


# =========================
# Entity: Shortlist
# =========================
class Shortlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    csr_id = db.Column(db.Integer, db.ForeignKey('user_accounts.id'))
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    csr = db.relationship('User', foreign_keys=[csr_id])
    request = db.relationship('Request')

    @classmethod
    def add_if_not_exists(cls, csr_id, request_id):
        exists = cls.query.filter_by(csr_id=csr_id, request_id=request_id).first()
        if not exists:
            db.session.add(cls(csr_id=csr_id, request_id=request_id))
            r = Request.query.get(request_id)
            if r:
                r.shortlist_count = (r.shortlist_count or 0) + 1
            db.session.commit()

    @classmethod
    def exists(cls, csr_id, request_id):
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


# =========================
# Entity: ServiceHistory
# =========================
class ServiceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    csr_id = db.Column(db.Integer, db.ForeignKey('user_accounts.id'))
    pin_id = db.Column(db.Integer, db.ForeignKey('user_accounts.id'))
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
    def filter_for_pin(cls, pin_id, category_id=None, start=None, end=None, q=None):
        qry = cls.query.filter_by(pin_id=pin_id)
        if category_id:
            qry = qry.filter_by(category_id=category_id)
        if start:
            qry = qry.filter(cls.date_completed >= start)
        if end:
            qry = qry.filter(cls.date_completed <= end)
        if q:
            like = f"%{q}%"
            qry = qry.join(cls.request, isouter=True).join(cls.category, isouter=True)
            qry = qry.filter(or_(
                User.username.like(like),
                Request.title.like(like),
                Category.name.like(like),
            ))
        return qry.order_by(cls.date_completed.desc()).all()

    @classmethod
    def filter_for_csr(cls, csr_id, category_id=None, start=None, end=None):
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

    # ------- Reports -------
    @staticmethod
    def generate_report(scope='daily'):
        """
        Aggregate counts of requests created and services completed
        grouped by day/week/month, using SQLite's strftime pattern.
        """
        if scope == 'weekly':
            fmt = '%Y-W%W'
        elif scope == 'monthly':
            fmt = '%Y-%m'
        else:
            fmt = '%Y-%m-%d'

        # Requests created per bucket
        reqs = (
            db.session.query(
                func.strftime(fmt, Request.created_at),
                func.count(Request.id)
            )
            .group_by(func.strftime(fmt, Request.created_at))
            .all()
        )

        # Completed services per bucket
        done = (
            db.session.query(
                func.strftime(fmt, ServiceHistory.date_completed),
                func.count(ServiceHistory.id)
            )
            .group_by(func.strftime(fmt, ServiceHistory.date_completed))
            .all()
        )

        return {'requests': reqs, 'completed': done}


# =========================
# Utilities: migration + seeding
# =========================
def reset_user_tables():
    """
    Drop legacy tables and keep schema clean for new design.
    Run once inside app context:
        >>> reset_user_tables(); db.create_all()
    """
    try:
        db.session.execute(text('DROP TABLE IF EXISTS user_profile'))
        db.session.execute(text('DROP TABLE IF EXISTS user'))
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def seed_database():
    # Ensure core tables exist
    db.create_all()

    # Seed categories if empty
    if not Category.query.first():
        for n in ['Medical Escort', 'Grocery Run', 'Wheelchair Repair', 'Tutoring', 'Home Maintenance']:
            db.session.add(Category(name=n))
        db.session.commit()

    # Clear and seed to exact counts:
    db.session.execute(text('DELETE FROM user_profiles'))
    db.session.execute(text('DELETE FROM user_accounts'))
    db.session.commit()

    # Four fixed accounts ONLY (no profiles for them)
    def createuser(role, username, pwd):
        u = User(role=role, username=username, is_active=True)
        u.set_password(pwd)
        db.session.add(u)
        db.session.flush()
        return u

    createuser('User Admin', 'user_admin1', 'user_admin1!')
    createuser('CSR Representative', 'csr_user1', 'csr_user1!')
    createuser('Person in Need', 'pin_user1', 'pin_user1!')
    createuser('Platform Manager', 'pm_user1', 'pm_user1!')
    db.session.commit()

    # Exactly 100 standalone demo profiles (no user_id)
    if UserProfile.query.count() > 0:
        print("Profiles already exist, skipping seeding.")
        return

    first_names = [
        "Aiden","Benjamin","Chloe","Daniel","Evelyn","Farhan","Grace","Hannah","Isaac","Janet",
        "Kevin","Lydia","Marcus","Nicole","Owen","Priya","Qistina","Rachel","Samuel","Tanvi",
        "Umar","Vanessa","William","Xin Yi","Yusuf","Aaron","Bella","Clarence","Daphne","Elias",
        "Fiona","Gavin","Hazel","Ian","Jia Hao","Kelly","Leon","Melissa","Nathan","Olivia",
        "Patrick","Qi Hui","Ryan","Sophia","Travis","Umairah","Vera","Winston","Xue Ying","Zara"
    ]
    last_names = ["Tan","Lee","Lim","Goh","Ong","Teo","Chong","Koh"]

    used_names = set()
    profiles = []
    idx = 0

    while len(profiles) < 100:
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        full = f"{fn} {ln}"
        if full in used_names:
            continue
        used_names.add(full)

        slug_fn = fn.lower().replace(" ", "")
        slug_ln = ln.lower().replace(" ", "")
        email = f"{slug_fn}.{slug_ln}{len(profiles)+1:02d}@example.com"
        phone = f"9{1230000 + (len(profiles)+1):07d}"
        profiles.append(UserProfile(full_name=full, email=email, phone=phone, is_active=True))
        idx += 1

    db.session.add_all(profiles)
    db.session.commit()
    print(f"Seeded {len(profiles)} unique user profiles.")

    # Additional seeding: create sample requests for the Person in Need user.
    pin_user = User.query.filter_by(username='pin_user1', role='Person in Need').first()
    if pin_user and not Request.query.filter_by(pin_id=pin_user.id).first():
        try:
            seed_pin_samples(pin_username='pin_user1', n_open=60, n_completed=40)
        except Exception:
            # swallow any errors during sample seeding to avoid breaking app start
            pass


def seed_pin_samples(pin_username: str = 'pin_user1', n_open: int = 60, n_completed: int = 40):
    """
    Create a number of sample request rows owned by the given Person-in-Need user.

    This helper makes it easy to populate the PIN dashboard for testing.  It
    creates `n_open` open requests and `n_completed` completed requests.  For
    each completed request, a corresponding ServiceHistory record is created.

    Only call this function inside an app context.  It will raise if the
    specified user or categories do not exist.
    """
    import random
    from datetime import datetime, timedelta

    # Fetch the PIN user
    pin = User.query.filter_by(username=pin_username, role='Person in Need').first()
    if not pin:
        raise RuntimeError(f"{pin_username!r} not found. Run seed_database() first.")

    # Retrieve available categories
    cats = Category.query.all()
    if not cats:
        raise RuntimeError("No categories found. Run seed_database() first.")

    # Attach a CSR for history rows where possible (CSR history pages need data)
    csr_user = User.query.filter_by(role='CSR Representative').first()

    # Helper to create random timestamps within the last 180 days
    now = datetime.utcnow()
    def random_ts():
        return now - timedelta(days=random.randint(0, 180), hours=random.randint(0, 23), minutes=random.randint(0, 59))

    # Helper to bump view/shortlist counters realistically
    def bump_counts(req_obj):
        req_obj.views_count = random.randint(0, 120)
        req_obj.shortlist_count = random.randint(0, 25)

    # Create open requests
    for i in range(n_open):
        cat = random.choice(cats)
        ts = random_ts()
        req = Request(
            pin_id=pin.id,
            title=f"{cat.name} help (open) #{i+1}",
            description="Sample open request for testing.",
            category_id=cat.id,
            status='open',
            created_at=ts,
            updated_at=ts
        )
        bump_counts(req)
        db.session.add(req)

    # Create completed requests and their history
    for i in range(n_completed):
        cat = random.choice(cats)
        created_ts = random_ts()
        completed_ts = created_ts + timedelta(days=random.randint(1, 15))
        req = Request(
            pin_id=pin.id,
            title=f"{cat.name} help (completed) #{i+1}",
            description="Sample completed request for testing.",
            category_id=cat.id,
            status='completed',
            created_at=created_ts,
            updated_at=completed_ts
        )
        bump_counts(req)
        db.session.add(req)
        db.session.flush()  # ensure req.id exists
        hist = ServiceHistory(
            csr_id=(csr_user.id if csr_user else None),  # <-- assign a real CSR if available
            pin_id=pin.id,
            request_id=req.id,
            category_id=cat.id,
            date_completed=completed_ts
        )
        db.session.add(hist)

    db.session.commit()
