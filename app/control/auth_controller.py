# CONTROL: Authentication and authorization rules
from flask import session, abort
from ..entity.models import UserAccount

class AuthController:
    @staticmethod
    def login(role, username, password):
        return UserAccount.login(role, username, password)

    @staticmethod
    def logout():
        """Clear current session."""
        session.clear()

    @staticmethod
    def require_role(role):
        if session.get('role') != role:
            abort(403)
