# CONTROL: User Admin use cases (CRUD + search on Users & Profiles)
from ..entity.models import db, UserAccount, UserProfile

class UserAdminController:
    @staticmethod
    def search_users(q: str = "", user_type: str = "accounts", page: int = 1, per_page: int = 20):
        """
        user_type: 'accounts' (only the four fixed accounts) or 'profiles' (standalone demo profiles)
        """
        if (user_type or '').lower() == 'profiles':
            return UserProfile.search_profiles(q=q or "", page=page, per_page=per_page)
        # default to the fixed four accounts list
        return UserAccount.search_accounts_fixed_four(q=q or "", page=page, per_page=per_page)

    @staticmethod
    def create_user_account(first_name, last_name, email, phone, username, password):
        return UserAccount.create_account(first_name, last_name, email, phone, username, password)

    @staticmethod
    def get_user_by_id(user_id):
        return UserAccount.get_by_id(user_id)

    @staticmethod
    def update_user_with_profile(user_id, profile_name, username, password, active, first_name, last_name, email, phone):
        return UserAccount.update_with_profile(user_id, profile_name, username, password, active, first_name, last_name, email, phone)

    @staticmethod
    def suspend_user(user_id):
        UserAccount.suspend_user(user_id)

    @staticmethod
    def activate_user(user_id):
        UserAccount.activate_user(user_id)
    
    @staticmethod
    def create_profile(name, active=True):
        return UserProfile.create_profile(name, active)

    @staticmethod
    def get_active_profiles():
        return UserProfile.query.filter_by(is_active=True).order_by(UserProfile.name).all()

    @staticmethod
    def get_profile_by_id(profile_id):
        return UserProfile.query.get(profile_id)

    @staticmethod
    def update_profile(profile_id, name, active=None):
        return UserProfile.update_profile(profile_id, name, active)

    @staticmethod
    def suspend_profile(profile_id):
        UserProfile.suspend_profile(profile_id)

    @staticmethod
    def activate_profile(profile_id):
        UserProfile.activate_profile(profile_id)
