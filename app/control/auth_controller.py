
# CONTROL: Authentication and authorization rules
from flask import session, abort
from ..entity.models import User

class AuthController:
    @staticmethod
    def login(role, username, password):
        user = User.query.filter_by(username=username, role=role).first()
        if user and user.is_active and user.check_password(password):
            return user
        return None

    @staticmethod
    def require_role(role):
        if session.get('role') != role:
            abort(403)
