# CONTROL: User Admin use cases (CRUD + search on Users & Profiles)
from ..entity.models import db, User, UserProfile
from sqlalchemy import or_

# The four fixed “User Accounts”
FIXED_ACCOUNTS = {
    ('User Admin', 'user_admin1'),
    ('CSR Representative', 'csr_user1'),
    ('Person in Need', 'pin_user1'),
    ('Platform Manager', 'pm_user1'),
}

class UserAdminController:
    @staticmethod
    def search_users(q: str = "", user_type: str = "accounts", page: int = 1, per_page: int = 20):
        """
        user_type: 'accounts' (only the four fixed accounts) or 'profiles' (everything else)
        """
        query = User.query

        # filter by type
        if user_type == 'accounts':
            ors = [ (User.role == r) & (User.username == u) for (r, u) in FIXED_ACCOUNTS ]
            f = ors[0]
            for cond in ors[1:]:
                f = f | cond
            query = query.filter(f)
        else:
            # profiles = NOT the four fixed accounts
            for (r, u) in FIXED_ACCOUNTS:
                query = query.filter(~((User.role == r) & (User.username == u)))

        # optional free-text search
        if q:
            like = f"%{q}%"
            query = query.join(UserProfile, isouter=True).filter(
                or_(
                    User.username.like(like),
                    User.role.like(like),
                    UserProfile.full_name.like(like),
                    UserProfile.email.like(like),
                )
            )

        query = query.order_by(User.id.asc())
        pag = query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            "items": pag.items,
            "total": pag.total,
            "page": pag.page,
            "per_page": per_page,
            "pages": pag.pages,
        }

    @staticmethod
    def create_user_with_profile(role, username, password, active, full_name, email, phone):
        if User.query.filter_by(username=username).first():
            return False, "Username exists."
        u = User(role=role, username=username, is_active=active)
        u.set_password(password)
        db.session.add(u)
        db.session.flush()
        p = UserProfile(user_id=u.id, full_name=full_name, email=email, phone=phone)
        db.session.add(p)
        db.session.commit()
        return True, "User created."

    @staticmethod
    def update_user_with_profile(user_id, role, username, password, active, full_name, email, phone):
        u = User.query.get(user_id)
        if not u:
            return False, "User not found."
        u.role = role
        u.username = username
        u.is_active = active
        if password:
            u.set_password(password)
        if not u.profile:
            u.profile = UserProfile(user_id=u.id)
        u.profile.full_name = full_name
        u.profile.email = email
        u.profile.phone = phone
        db.session.commit()
        return True, "User updated."

    @staticmethod
    def suspend_user(user_id):
        u = User.query.get(user_id)
        if u:
            u.is_active = False
            db.session.commit()

    @staticmethod
    def activate_user(user_id):
        u = User.query.get(user_id)
        if u:
            u.is_active = True
            db.session.commit()
