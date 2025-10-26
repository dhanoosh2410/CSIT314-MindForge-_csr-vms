
# CONTROL: User Admin use cases (CRUD+search on Users & Profiles)
from ..entity.models import db, User, UserProfile

class UserAdminController:
    @staticmethod
    def search_users(q, page=1, per_page=20):
        query = User.query
        if q:
            like = f"%{q}%"
            query = query.join(UserProfile, isouter=True).filter(
                (User.username.like(like)) | (User.role.like(like)) |
                (UserProfile.full_name.like(like)) | (UserProfile.email.like(like))
            )
        # ascending by id
        query = query.order_by(User.id.asc())
        try:
            pag = query.paginate(page=page, per_page=per_page, error_out=False)
            items = pag.items
            total = pag.total
            pages = pag.pages
        except Exception:
            # Fallback for SQLAlchemy core: use offset/limit
            total = query.count()
            items = query.offset((page-1)*per_page).limit(per_page).all()
            pages = (total + per_page - 1) // per_page
        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': pages
        }

    @staticmethod
    def create_user_with_profile(role, username, password, active, full_name, email, phone):
        if User.query.filter_by(username=username).first():
            return False, 'Username exists.'
        u = User(role=role, username=username, is_active=active)
        u.set_password(password)
        db.session.add(u); db.session.flush()
        p = UserProfile(user_id=u.id, full_name=full_name, email=email, phone=phone)
        db.session.add(p); db.session.commit()
        return True, 'User created.'

    @staticmethod
    def update_user_with_profile(user_id, role, username, password, active, full_name, email, phone):
        u = User.query.get(user_id)
        if not u: return False, 'User not found.'
        u.role = role; u.username = username; u.is_active = active
        if password: u.set_password(password)
        if not u.profile:
            u.profile = UserProfile(user_id=u.id)
        u.profile.full_name = full_name; u.profile.email = email; u.profile.phone = phone
        db.session.commit()
        return True, 'User updated.'

    @staticmethod
    def suspend_user(user_id):
        u = User.query.get(user_id)
        if u:
            u.is_active = False
            db.session.commit()
