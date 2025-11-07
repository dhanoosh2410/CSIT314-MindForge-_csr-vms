from app.control.auth_controller import AuthController
from app.entity import models
import pytest


def seed_roles_and_users():
    # Create the four canonical profiles
    names = ['User Admin', 'CSR Representative', 'Person in Need', 'Platform Manager']
    profile_map = {}
    for n in names:
        p = models.UserProfile.query.filter_by(name=n).first()
        if not p:
            p = models.UserProfile(name=n, is_active=True)
            models.db.session.add(p)
            models.db.session.flush()
        profile_map[n] = p

    # Create users for each profile
    def create_user(profile_name, username, pwd, active=True):
        prof = profile_map[profile_name]
        u = models.UserAccount(profile_id=prof.id, username=username, is_active=active)
        u.set_password(pwd)
        models.db.session.add(u)
        return u

    ua = create_user('User Admin', 'user_admin_test', 'adminpass')
    csr = create_user('CSR Representative', 'csr_test', 'csrpass')
    pin = create_user('Person in Need', 'pin_test', 'pinpass')
    pm = create_user('Platform Manager', 'pm_test', 'pmpass')

    models.db.session.commit()
    return {'User Admin': ua, 'CSR Representative': csr, 'Person in Need': pin, 'Platform Manager': pm}


def test_login_user_admin_success(app_instance):
    """User Admin can log in with correct credentials."""
    with app_instance.app_context():
        seed_roles_and_users()
        u = AuthController.login('User Admin', 'user_admin_test', 'adminpass')
        assert u is not None and u.username == 'user_admin_test'


def test_login_csr_success(app_instance):
    """CSR Representative can log in with correct credentials."""
    with app_instance.app_context():
        seed_roles_and_users()
        u = AuthController.login('CSR Representative', 'csr_test', 'csrpass')
        assert u is not None and u.username == 'csr_test'


def test_login_pin_success(app_instance):
    """Person in Need can log in with correct credentials."""
    with app_instance.app_context():
        seed_roles_and_users()
        u = AuthController.login('Person in Need', 'pin_test', 'pinpass')
        assert u is not None and u.username == 'pin_test'


def test_login_pm_success(app_instance):
    """Platform Manager can log in with correct credentials."""
    with app_instance.app_context():
        seed_roles_and_users()
        u = AuthController.login('Platform Manager', 'pm_test', 'pmpass')
        assert u is not None and u.username == 'pm_test'


@pytest.mark.parametrize("role,username", [
    ("User Admin", "user_admin_test"),
    ("CSR Representative", "csr_test"),
    ("Person in Need", "pin_test"),
    ("Platform Manager", "pm_test"),
])
def test_login_wrong_password_per_role(app_instance, role, username):
    """Login fails with wrong password for the given role"""
    with app_instance.app_context():
        seed_roles_and_users()
        res = AuthController.login(role, username, 'wrong-password')
        assert res is None


@pytest.mark.parametrize("role,username", [
    ("User Admin", "user_admin_test"),
    ("CSR Representative", "csr_test"),
    ("Person in Need", "pin_test"),
    ("Platform Manager", "pm_test"),
])
def test_login_suspended_profile_per_role(app_instance, role, username):
    """Login fails when the role/profile is suspended"""
    with app_instance.app_context():
        seed_roles_and_users()
        # find profile and suspend it
        prof = models.UserProfile.query.filter_by(name=role).first()
        assert prof is not None
        prof.is_active = False
        models.db.session.commit()

        res = AuthController.login(role, username, f"{username}pass")
        assert res is None


@pytest.mark.parametrize("role,username", [
    ("User Admin", "user_admin_test"),
    ("CSR Representative", "csr_test"),
    ("Person in Need", "pin_test"),
    ("Platform Manager", "pm_test"),
])
def test_login_suspended_account_per_role(app_instance, role, username):
    """Login fails when the user account is suspended"""
    with app_instance.app_context():
        seed_roles_and_users()
        u = models.UserAccount.query.filter_by(username=username).first()
        assert u is not None
        u.is_active = False
        models.db.session.commit()

        res = AuthController.login(role, username, f"{username}pass")
        assert res is None


def test_login_wrong_password_fails(app_instance):
    """User Admin login fails with wrong password"""
    with app_instance.app_context():
        seed_roles_and_users()
        u = AuthController.login('User Admin', 'user_admin_test', 'wrong')
        assert u is None


def test_login_unassigned_profile_fails(app_instance):
    """Login fails when account has no assigned profile"""
    with app_instance.app_context():
        # Create account without assigning profile_id (do not touch existing profiles)
        u = models.UserAccount(username='no_profile', is_active=True)
        u.set_password('nopass')
        models.db.session.add(u)
        models.db.session.commit()

        # Attempt to login selecting User Admin role should fail because account has no profile_id
        res = AuthController.login('User Admin', 'no_profile', 'nopass')
        assert res is None


def test_login_suspended_profile_or_account(app_instance):
    """Login fails when profile is suspended or when account is suspended"""
    with app_instance.app_context():
        # suspended profile: update existing profile to suspended if present
        p = models.UserProfile.query.filter_by(name='CSR Representative').first()
        if not p:
            p = models.UserProfile(name='CSR Representative', is_active=False)
            models.db.session.add(p)
            models.db.session.flush()
        else:
            p.is_active = False
            models.db.session.flush()

        u = models.UserAccount(profile_id=p.id, username='suspended_profile_user', is_active=True)
        u.set_password('pw')
        models.db.session.add(u)
        models.db.session.commit()

        assert AuthController.login('CSR Representative', 'suspended_profile_user', 'pw') is None

        # suspended account: use existing 'Person in Need' profile if present
        p2 = models.UserProfile.query.filter_by(name='Person in Need').first()
        if not p2:
            p2 = models.UserProfile(name='Person in Need', is_active=True)
            models.db.session.add(p2)
            models.db.session.flush()

        u2 = models.UserAccount(profile_id=p2.id, username='suspended_account_user', is_active=False)
        u2.set_password('pw2')
        models.db.session.add(u2)
        models.db.session.commit()

        assert AuthController.login('Person in Need', 'suspended_account_user', 'pw2') is None
