# ENTITY + Use-case coordination in one place (per your lecture guidance)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta
from sqlalchemy import or_, text
from sqlalchemy.sql import func  # <-- added for PM reports
import hashlib
from sqlalchemy.orm import joinedload
import random

db = SQLAlchemy()

# =========================
# Entity: UserAccount (logins)
# =========================
class UserAccount(db.Model):
    """
    Maps to 'user_accounts' table. Real authentication happens here.
    """
    __tablename__ = 'user_accounts'

    id = db.Column(db.Integer, primary_key=True)
    # link to the canonical profile/role (nullable until an admin assigns one)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profiles.id'), nullable=True)
    profile = db.relationship('UserProfile')

    # account fields (personal info)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))

    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, raw: str):
        self.password_hash = hashlib.sha256(raw.encode()).hexdigest()

    def check_password(self, raw: str) -> bool:
        return self.password_hash == hashlib.sha256(raw.encode()).hexdigest()

    @classmethod
    def login(cls, role, username, password):
        # role is the profile name selected on the login form. Users without
        # an assigned profile cannot log in to a role until an admin assigns one.
        prof = UserProfile.query.filter_by(name=role).first()
        if not prof:
            return None
        # if the profile itself is suspended, deny login regardless of user state
        if not prof.is_active:
            return None
        u = cls.query.filter_by(username=username, profile_id=prof.id).first()
        if u and u.is_active and u.check_password(password):
            return u
        return None

    # Keep signatures used by boundary; profile args ignored (profiles are standalone now)
    @classmethod
    def create_account(cls, first_name, last_name, email, phone, username, password, profile_name: str = None):
        # prevent duplicate usernames
        if cls.query.filter_by(username=username).first():
            return False, "Username exists."

        u = cls(first_name=(first_name or '').strip(), last_name=(last_name or '').strip(), email=(email or '').strip(), phone=(phone or '').strip(), username=username, is_active=True)
        if password:
            u.set_password(password)

        if profile_name:
            prof = UserProfile.query.filter_by(name=profile_name).first()
            if prof:
                u.profile_id = prof.id

        db.session.add(u)
        db.session.commit()
        return True, "User account created."

    @classmethod
    def update_with_profile(cls, user_id, profile_name, username, password, active, first_name, last_name, email, phone):
        u = cls.query.get(user_id)
        if not u:
            return False, "User not found."
        # resolve profile by name (may be None or empty to unassign)
        if profile_name:
            prof = UserProfile.query.filter_by(name=profile_name).first()
            u.profile_id = prof.id if prof else None
        else:
            u.profile_id = None

        u.username = username
        u.first_name = (first_name or '').strip()
        u.last_name = (last_name or '').strip()
        u.email = (email or '').strip()
        u.phone = (phone or '').strip()

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
    def get_by_id(cls, user_id):
        return cls.query.get(user_id)

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
    def search_user_account(cls, q: str = "", page: int = 1, per_page: int = 20):        # Return users who have an assigned profile (profiles are driven by DB)
        query = cls.query.options(joinedload(cls.profile)).join(UserProfile, isouter=True)
        query = query.filter(UserProfile.id.isnot(None))

        if q:
            like = f"%{q}%"
            query = query.filter((cls.username.like(like)) | (UserProfile.name.like(like)) )

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
    __tablename__ = 'user_profiles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    @classmethod
    def create_profile(cls, name: str, active: bool = True):
        if cls.query.filter_by(name=name).first():
            return False, "Profile exists."
        p = cls(name=(name or '').strip(), is_active=bool(active))
        db.session.add(p)
        db.session.commit()
        return True, "Profile created."

    @classmethod
    def update_profile(cls, profile_id: int, name: str, active=None):
        p = cls.query.get(profile_id)
        if not p:
            return False, "Profile not found."
        p.name = (name or '').strip()
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
            query = query.filter(cls.name.like(like))
        query = query.order_by(cls.id.asc())
        pag = query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            "items": pag.items,
            "total": pag.total,
            "page": pag.page,
            "per_page": per_page,
            "pages": pag.pages,
        }

    @classmethod
    def get_by_id(cls, profile_id: int):
        """Return a UserProfile by id or None."""
        if profile_id is None:
            return None
        return cls.query.get(profile_id)

    @classmethod
    def get_active_profiles(cls):
        """Return all active profiles ordered by name."""
        return cls.query.filter_by(is_active=True).order_by(cls.name).all()


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

    # --- CRUD helpers for controllers to call ---
    @classmethod
    def create(cls, name):
        if not name or not name.strip():
            return False, "Category name required."
        name = name.strip()
        if cls.query.filter_by(name=name).first():
            return False, "Category exists."
        c = cls(name=name)
        db.session.add(c)
        db.session.commit()
        return True, "Category created."

    @classmethod
    def update(cls, cat_id, name):
        c = cls.query.get(cat_id)
        if not c:
            return False, "Category not found."
        if not name or not name.strip():
            return False, "Category name required."
        name = name.strip()
        # ensure uniqueness if changing
        existing = cls.query.filter(cls.name == name, cls.id != cat_id).first()
        if existing:
            return False, "Another category with that name exists."
        c.name = name
        db.session.commit()
        return True, "Category updated."

    @classmethod
    def delete(cls, cat_id):
        c = cls.query.get(cat_id)
        if not c:
            return False, "Category not found."
        db.session.delete(c)
        db.session.commit()
        return True, "Category deleted."


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
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), default='open')  # open/completed
    # if a CSR explicitly accepts a request, record who and when here. Nullable
    accepted_csr_id = db.Column(db.Integer, db.ForeignKey('user_accounts.id'), nullable=True)
    accepted_at = db.Column(db.DateTime, nullable=True)
    views_count = db.Column(db.Integer, default=0)
    shortlist_count = db.Column(db.Integer, default=0)

    category = db.relationship('Category')
    pin = db.relationship('UserAccount', foreign_keys=[pin_id])
    accepted_csr = db.relationship('UserAccount', foreign_keys=[accepted_csr_id])

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
    def paginate_open_no_increment(cls, category_id=None, q: str = None, page=1, per_page=12):
        """Return paginated open requests without incrementing views.

        Supports optional filtering by category_id and text search q against
        title and description.
        """
        query = cls.query.filter_by(status='open')
        if category_id:
            query = query.filter_by(category_id=category_id)
        # support optional text search against title/description
        if q:
            like = f"%{q}%"
            query = query.filter((cls.title.like(like)) | (cls.description.like(like)))
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
                csr_id_val = None
                try:
                    if getattr(r, 'accepted_csr_id', None):
                        csr_id_val = r.accepted_csr_id
                    else:
                        recent_short = Shortlist.query.filter_by(request_id=r.id).order_by(Shortlist.created_at.desc()).first()
                        csr_id_val = recent_short.csr_id if recent_short else None
                except Exception:
                    csr_id_val = None
                sh = ServiceHistory(pin_id=r.pin_id, csr_id=csr_id_val, request_id=r.id, category_id=r.category_id)
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
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    csr = db.relationship('UserAccount', foreign_keys=[csr_id])
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
    def search_for_csr(cls, csr_id, q=None, category_id=None):
        """Search shortlist items for a CSR, optionally filtering by text q and category_id."""
        query = cls.query.filter_by(csr_id=csr_id).join(Request)
        if category_id:
            query = query.filter(Request.category_id == category_id)
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
    date_completed = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    csr = db.relationship('UserAccount', foreign_keys=[csr_id])
    pin = db.relationship('UserAccount', foreign_keys=[pin_id])
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
                UserAccount.username.like(like),
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
    try:
        conn = db.engine.connect()
        def table_columns(table_name):
            res = conn.execute(text(f"PRAGMA table_info('{table_name}')"))
            return {row['name'] for row in res}

        up_cols = set()
        try:
            up_cols = table_columns('user_profiles')
        except Exception:
            up_cols = set()

        if 'name' not in up_cols:
            try:
                conn.execute(text("ALTER TABLE user_profiles ADD COLUMN name VARCHAR(80)"))
            except Exception:
                pass
            if 'full_name' in up_cols:
                try:
                    conn.execute(text("UPDATE user_profiles SET name = full_name WHERE name IS NULL OR name = ''"))
                except Exception:
                    pass

        ua_cols = set()
        try:
            ua_cols = table_columns('user_accounts')
        except Exception:
            ua_cols = set()

        added = False
        if 'first_name' not in ua_cols:
            try:
                conn.execute(text("ALTER TABLE user_accounts ADD COLUMN first_name VARCHAR(80)"))
                added = True
            except Exception:
                pass
        if 'last_name' not in ua_cols:
            try:
                conn.execute(text("ALTER TABLE user_accounts ADD COLUMN last_name VARCHAR(80)"))
                added = True
            except Exception:
                pass
        if 'email' not in ua_cols:
            try:
                conn.execute(text("ALTER TABLE user_accounts ADD COLUMN email VARCHAR(120)"))
                added = True
            except Exception:
                pass
        if 'phone' not in ua_cols:
            try:
                conn.execute(text("ALTER TABLE user_accounts ADD COLUMN phone VARCHAR(30)"))
                added = True
            except Exception:
                pass
        if 'profile_id' not in ua_cols:
            try:
                conn.execute(text("ALTER TABLE user_accounts ADD COLUMN profile_id INTEGER"))
                added = True
            except Exception:
                pass

        try:
            req_cols = table_columns('request')
        except Exception:
            req_cols = set()
        if 'accepted_csr_id' not in req_cols:
            try:
                conn.execute(text("ALTER TABLE request ADD COLUMN accepted_csr_id INTEGER"))
            except Exception:
                pass
        if 'accepted_at' not in req_cols:
            try:
                conn.execute(text("ALTER TABLE request ADD COLUMN accepted_at DATETIME"))
            except Exception:
                pass

        if 'role' in ua_cols:
            # create missing roles first
            existing_role_names = {p.name for p in UserProfile.query.all()} if 'name' in table_columns('user_profiles') else set()
            try:
                rows = conn.execute(text("SELECT DISTINCT role FROM user_accounts WHERE role IS NOT NULL"))
                distinct_roles = [r[0] for r in rows.fetchall() if r[0]]
            except Exception:
                distinct_roles = []
            for rn in distinct_roles:
                if rn not in existing_role_names:
                    try:
                        conn.execute(text("INSERT INTO user_profiles (name, is_active) VALUES (:n, 1)"), {'n': rn})
                    except Exception:
                        pass
            # map user_accounts.role -> user_profiles.id
            try:
                try:
                    rows = conn.execute(text("SELECT DISTINCT role FROM user_accounts WHERE role IS NOT NULL"))
                    distinct_roles = [r[0] for r in rows.fetchall() if r[0]]
                except Exception:
                    distinct_roles = []
                for rn in distinct_roles:
                    pid_row = conn.execute(text("SELECT id FROM user_profiles WHERE name = :n LIMIT 1"), {'n': rn}).fetchone()
                    if pid_row:
                        pid = pid_row['id'] if isinstance(pid_row, dict) or hasattr(pid_row, 'keys') else pid_row[0]
                        conn.execute(text("UPDATE user_accounts SET profile_id = :pid WHERE role = :r"), {'pid': pid, 'r': rn})
            except Exception:
                pass

            try:
                if 'role' in ua_cols:
                    conn.execute(text("PRAGMA foreign_keys=OFF"))
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS user_accounts_new (
                            id INTEGER PRIMARY KEY,
                            profile_id INTEGER,
                            first_name VARCHAR(80),
                            last_name VARCHAR(80),
                            email VARCHAR(120),
                            phone VARCHAR(30),
                            username VARCHAR(80) UNIQUE NOT NULL,
                            password_hash VARCHAR(128) NOT NULL,
                            is_active BOOLEAN DEFAULT 1
                        )
                    """))
                    conn.execute(text("""
                        INSERT INTO user_accounts_new (id, profile_id, first_name, last_name, email, phone, username, password_hash, is_active)
                        SELECT ua.id,
                               (SELECT id FROM user_profiles WHERE name = ua.role LIMIT 1),
                               ua.first_name, ua.last_name, ua.email, ua.phone, ua.username, ua.password_hash, ua.is_active
                        FROM user_accounts ua
                    """))
                    conn.execute(text("DROP TABLE user_accounts"))
                    conn.execute(text("ALTER TABLE user_accounts_new RENAME TO user_accounts"))
                    conn.execute(text("PRAGMA foreign_keys=ON"))
            except Exception:
                pass

        conn.close()
    except Exception:
        pass

    try:
        if UserAccount.query.first() or UserProfile.query.first() or Category.query.first():
            return
    except Exception:
        pass

    # Seed categories if empty
    if not Category.query.first():
        for n in ['Medical Escort', 'Grocery Run', 'Wheelchair Repair', 'Tutoring', 'Home Maintenance']:
            db.session.add(Category(name=n))
        db.session.commit()

    existing = {p.name for p in UserProfile.query.all()}
    profile_map = {}
    if existing:
        names_to_ensure = list(existing)
    else:
        names_to_ensure = ['User Admin', 'CSR Representative', 'Person in Need', 'Platform Manager']

    for name in names_to_ensure:
        if name not in existing:
            p = UserProfile(name=name, is_active=True)
            db.session.add(p)
            db.session.flush()
            profile_map[name] = p
        else:
            profile_map[name] = UserProfile.query.filter_by(name=name).first()
    db.session.commit()

    def createuser_for_profile(profile_name, username, pwd, first_name='', last_name=''):
        prof = profile_map.get(profile_name)
        if not prof:
            return None
        if UserAccount.query.filter_by(username=username).first():
            return None
        u = UserAccount(profile_id=prof.id, username=username, is_active=True, first_name=first_name, last_name=last_name)
        u.set_password(pwd)
        db.session.add(u)
        db.session.flush()
        return u

    createuser_for_profile('User Admin', 'user_admin1', 'user_admin1!', first_name='User', last_name='Admin')
    createuser_for_profile('CSR Representative', 'csr_user1', 'csr_user1!', first_name='CSR', last_name='User')
    createuser_for_profile('Person in Need', 'pin_user1', 'pin_user1!', first_name='PIN', last_name='User')
    createuser_for_profile('Platform Manager', 'pm_user1', 'pm_user1!', first_name='Platform', last_name='Manager')
    db.session.commit()

    # Additional seeding: create sample requests for the Person in Need user.
    pin_user = UserAccount.query.filter_by(username='pin_user1').first()
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


    # Fetch the PIN user
    pin = UserAccount.query.filter_by(username=pin_username).first()
    if not pin:
        raise RuntimeError(f"{pin_username!r} not found. Run seed_database() first.")

    # Retrieve available categories
    cats = Category.query.all()
    if not cats:
        raise RuntimeError("No categories found. Run seed_database() first.")

    # Attach a CSR for history rows where possible (CSR history pages need data)
    csr_prof = UserProfile.query.filter_by(name='CSR Representative').first()
    csr_user = None
    if csr_prof:
        csr_user = UserAccount.query.filter_by(profile_id=csr_prof.id).first()

    # Helper to create random timestamps within the last 180 days
    now = datetime.now(timezone.utc)
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
