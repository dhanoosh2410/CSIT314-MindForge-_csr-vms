import pytest
from app import create_app
from app.entity import models
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
test_logger = logging.getLogger('tests')


@pytest.fixture(scope='function')
def app_instance():
    # Create a Flask app configured for testing with an in-memory DB
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    })

    with app.app_context():
        models.db.create_all()
        yield app
        models.db.session.remove()
        models.db.drop_all()


def pytest_runtest_makereport(item, call):
    if call.when != 'call':
        return
    description = None
    try:
        description = item.obj.__doc__
    except Exception:
        description = None
    desc = (description or item.name).strip()
    desc_clean = ' '.join(desc.split())
    try:
        if hasattr(item, 'callspec') and item.callspec is not None:
            params = getattr(item, 'callspec').params
            if 'role' in params:
                desc_clean = f"{params['role']} - {desc_clean}"
            elif 'username' in params:
                desc_clean = f"{params['username']} - {desc_clean}"
    except Exception:
        pass

    outcome = getattr(call, 'excinfo', None)
    if outcome is None:
        test_logger.info(f"TEST PASSED: {desc_clean}")
    else:
        if outcome.typename == 'Skipped':
            test_logger.warning(f"TEST SKIPPED: {desc_clean}")
        else:
            short = ''
            try:
                short = str(outcome.value)
            except Exception:
                short = ''
            if short:
                test_logger.error(f"TEST FAILED: {desc_clean} — {short}")
            else:
                test_logger.error(f"TEST FAILED: {desc_clean}")
