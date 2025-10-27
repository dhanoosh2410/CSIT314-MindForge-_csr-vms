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
        # delegate to model-level search
        return User.search_users(q=q or "", user_type=user_type, page=page, per_page=per_page)

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
