# CONTROL: User Admin use cases (CRUD + search on Users & Profiles)
from ..entity.models import db, User, UserProfile

class UserAdminController:
    @staticmethod
    def search_users(q: str = "", user_type: str = "accounts", page: int = 1, per_page: int = 20):
        """
        user_type: 'accounts' (only the four fixed accounts) or 'profiles' (standalone demo profiles)
        """
        if (user_type or '').lower() == 'profiles':
            return UserProfile.search_profiles(q=q or "", page=page, per_page=per_page)
        # default to the fixed four accounts list
        return User.search_accounts_fixed_four(q=q or "", page=page, per_page=per_page)

    @staticmethod
    def create_user_with_profile(role, username, password, active, full_name, email, phone):
        return User.create_with_profile(role, username, password, active, full_name, email, phone)

    @staticmethod
    def update_user_with_profile(user_id, role, username, password, active, full_name, email, phone):
        return User.update_with_profile(user_id, role, username, password, active, full_name, email, phone)

    @staticmethod
    def suspend_user(user_id):
        User.suspend_user(user_id)

    @staticmethod
    def activate_user(user_id):
        User.activate_user(user_id)
