
# CONTROL: Authentication and authorization rules
from flask import session, abort
from ..entity.models import User

class AuthController:
    @staticmethod
    def login(role, username, password):
        # Delegate authentication to the User model
        return User.login(role, username, password)

    @staticmethod
    def require_role(role):
        if session.get('role') != role:
            abort(403)
