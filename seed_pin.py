# seed_pin.py  (place in project root next to your app/ and entity/ folders)
import os, sys, random
from datetime import datetime

BASE = os.path.dirname(__file__)
sys.path.insert(0, BASE)

# --- Get a Flask app instance, regardless of layout ---
flask_app = None
try:
    # Package style: app/__init__.py with create_app()
    from app import create_app  # type: ignore
    flask_app = create_app()
except Exception:
    # Single-file fallback: app.py exports "app"
    from app import app as flask_app  # type: ignore

# Ensure entity is importable
try:
    from entity.models import db, User, Request, Category, ServiceHistory
except ModuleNotFoundError:
    raise SystemExit("ERROR: Cannot import entity.models. Make sure 'entity/__init__.py' exists and you run from project root.")

# --- Seeder helper (kept here; safe to run more than once if you clear old rows) ---
def seed_pin_samples(pin_username: str = 'pin_user1', n_open: int = 60, n_completed: int = 40):
    """
    Create ~100 sample rows for a Person in Need user:
      - n_open open requests (Table 1)
      - n_completed completed requests + ServiceHistory (Table 2)
    """
    import random
    random.seed(314)

    pin = User.query.filter_by(username=pin_username, role='Person in Need').first()
    if not pin:
        raise RuntimeError(f"{pin_username!r} not found. Seed your base users first.")

    cats = Category.query.all()
    if not cats:
        raise RuntimeError("No categories found. Seed categories first.")

    def bump_counts(r: Request):
        r.views_count = random.randint(0, 120)
        r.shortlist_count = random.randint(0, 25)

    # Open requests
    for i in range(n_open):
        cat = random.choice(cats)
        r = Request(
            pin_id=pin.id,
            title=f"{cat.name} help (open) #{i+1}",
            description="Sample open request for testing",
            category_id=cat.id,
            status='open'
        )
        db.session.add(r)
        db.session.flush()
        bump_counts(r)

    # Completed requests + history
    for i in range(n_completed):
        cat = random.choice(cats)
        r = Request(
            pin_id=pin.id,
            title=f"{cat.name} help (completed) #{i+1}",
            description="Sample completed request for testing",
            category_id=cat.id,
            status='completed'
        )
        db.session.add(r)
        db.session.flush()
        bump_counts(r)

        h = ServiceHistory(
            pin_id=pin.id,
            csr_id=None,  # leave None unless you want to point to a CSR user id
            request_id=r.id,
            category_id=cat.id
        )
        db.session.add(h)

    db.session.commit()

def clear_pin_data(pin_username='pin_user1'):
    pin = User.query.filter_by(username=pin_username, role='Person in Need').first()
    if not pin:
        return
    ServiceHistory.query.filter_by(pin_id=pin.id).delete()
    Request.query.filter_by(pin_id=pin.id).delete()
    db.session.commit()

def run():
    with flask_app.app_context():
        # Optional: clear old rows so you don’t double-count when reseeding
        clear_pin_data('pin_user1')
        seed_pin_samples('pin_user1', 60, 40)
        print("✅ Seeded 60 open + 40 completed requests for pin_user1")

if __name__ == "__main__":
    run()
