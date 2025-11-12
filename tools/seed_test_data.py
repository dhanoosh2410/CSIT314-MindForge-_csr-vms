#!/usr/bin/env python3
"""
Seed test data for the app. Creates 100 records each for the following entities:
- UserAccount (accounts)
- Category
- Request
- Shortlist
- ServiceHistory

UserProfile is seeded only with the four canonical roles and will NOT be populated
with 100 records.

Usage:
    python tools/seed_test_data.py [--in-memory]

By default this will use the app's configured database (instance csr_vms.db). Use
--in-memory to run against an ephemeral SQLite DB for verification.
"""
import sys
import os
import argparse
import random
from datetime import datetime, timezone, timedelta

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from app.entity import models

COUNT = 100


def ensure_profiles():
    names = ['User Admin', 'CSR Representative', 'Person in Need', 'Platform Manager']
    created = 0
    for n in names:
        p = models.UserProfile.query.filter_by(name=n).first()
        if not p:
            # add a short canonical description for seeded profiles
            desc_map = {
                'User Admin': 'Administrative user who manages accounts and profiles.',
                'CSR Representative': 'Customer service representative who manages requests.',
                'Person in Need': 'End-user who creates requests for assistance.',
                'Platform Manager': 'Manages categories and platform-level reports.'
            }
            p = models.UserProfile(name=n, is_active=True, description=desc_map.get(n))
            models.db.session.add(p)
            created += 1
    models.db.session.commit()
    return created


def ensure_categories(target=COUNT):
    # create categories named Test Category 1..N until we have target count
    existing = models.Category.query.filter(models.Category.name.like('Category %')).all()
    existing_names = {c.name for c in existing}
    to_create = target - len(existing)
    created = 0
    idx = 1
    while created < to_create:
        name = f"Category {idx}"
        idx += 1
        if name in existing_names or models.Category.query.filter_by(name=name).first():
            continue
        models.db.session.add(models.Category(name=name))
        created += 1
    if created:
        models.db.session.commit()
    total = models.Category.query.count()
    return created, total


def ensure_useraccounts(target=COUNT):
    # Create users distributed across the 4 roles so we have PIN and CSR pools
    profiles = {p.name: p for p in models.UserProfile.query.all()}
    if not profiles:
        raise RuntimeError('Profiles not seeded')
    # count existing seeded accounts with the 'seed_' prefix
    existing = models.UserAccount.query.filter(models.UserAccount.username.like('seed_user_%')).count()
    to_create = max(0, target - existing)
    created = 0
    # distribute evenly
    role_names = list(profiles.keys())
    i = 0
    while created < to_create:
        rn = role_names[i % len(role_names)]
        i += 1
        uname = f"user_account_{created+1}_{rn.replace(' ','_')[:10]}"
        if models.UserAccount.query.filter_by(username=uname).first():
            created += 1
            continue
        prof = profiles[rn]
        u = models.UserAccount(profile_id=prof.id, username=uname, first_name=rn.split()[0], last_name=f"UserAccount{created+1}", is_active=True)
        u.set_password('password')
        models.db.session.add(u)
        created += 1
    if created:
        models.db.session.commit()
    total = models.UserAccount.query.count()
    return created, total


def ensure_requests(target=COUNT):
    # create requests belonging to random PIN users
    pin_profile = models.UserProfile.query.filter_by(name='Person in Need').first()
    if not pin_profile:
        raise RuntimeError('Person in Need profile missing')
    pins = models.UserAccount.query.filter_by(profile_id=pin_profile.id).all()
    if not pins:
        raise RuntimeError('No PIN users available')
    cats = models.Category.query.all()
    if not cats:
        raise RuntimeError('No categories available')

    existing = models.Request.query.filter(models.Request.title.like('Request%')).count()
    to_create = max(0, target - existing)
    created = 0
    now = datetime.now(timezone.utc)
    for i in range(to_create):
        pin = random.choice(pins)
        cat = random.choice(cats)
        ts = now - timedelta(days=random.randint(0, 30), hours=random.randint(0,23))
        r = models.Request(pin_id=pin.id, title=f"Request #{existing + created + 1}", description="Auto-generated request", category_id=cat.id, status='open', created_at=ts, updated_at=ts)
        # randomize counters
        r.views_count = random.randint(0, 50)
        r.shortlist_count = 0
        models.db.session.add(r)
        created += 1
    if created:
        models.db.session.commit()
    total = models.Request.query.count()
    return created, total


def ensure_shortlists(target=COUNT):
    # create shortlist entries linking CSR users to requests
    csr_profile = models.UserProfile.query.filter_by(name='CSR Representative').first()
    if not csr_profile:
        raise RuntimeError('CSR Representative profile missing')
    csrs = models.UserAccount.query.filter_by(profile_id=csr_profile.id).all()
    reqs = models.Request.query.all()
    if not csrs or not reqs:
        raise RuntimeError('Missing CSR users or requests')

    existing = models.Shortlist.query.count()
    to_create = max(0, target - existing)
    created = 0
    i = 0
    # Use add_if_not_exists helper which updates request.shortlist_count
    while created < to_create:
        csr = random.choice(csrs)
        req = random.choice(reqs)
        # skip if exists
        if models.Shortlist.exists(csr.id, req.id):
            i += 1
            if i > target * 5:
                break
            continue
        models.Shortlist.add_if_not_exists(csr.id, req.id)
        created += 1
    total = models.Shortlist.query.count()
    return created, total


def ensure_servicehistory(target=COUNT):
    # create service history rows linking csr, pin, request
    csrs = models.UserAccount.query.join(models.UserProfile).filter(models.UserProfile.name=='CSR Representative').all()
    pins = models.UserAccount.query.join(models.UserProfile).filter(models.UserProfile.name=='Person in Need').all()
    cats = models.Category.query.all()
    reqs = models.Request.query.all()
    if not csrs or not pins or not cats or not reqs:
        raise RuntimeError('Missing required entities for ServiceHistory')

    existing = models.ServiceHistory.query.count()
    to_create = max(0, target - existing)
    created = 0
    now = datetime.now(timezone.utc)
    for i in range(to_create):
        csr = random.choice(csrs)
        pin = random.choice(pins)
        req = random.choice(reqs)
        cat = random.choice(cats)
        comp_ts = now - timedelta(days=random.randint(0, 30), hours=random.randint(0,23))
        sh = models.ServiceHistory(csr_id=csr.id, pin_id=pin.id, request_id=req.id, category_id=cat.id, date_completed=comp_ts)
        models.db.session.add(sh)
        # mark request completed if not already
        if req.status != 'completed':
            req.status = 'completed'
        created += 1
    if created:
        models.db.session.commit()
    total = models.ServiceHistory.query.count()
    return created, total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--in-memory', action='store_true', help='Run against an in-memory SQLite DB (safe)')
    args = parser.parse_args()

    if args.in_memory:
        app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    else:
        app = create_app()

    with app.app_context():
        models.db.create_all()
        p_created = ensure_profiles()
        cat_created, cat_total = ensure_categories(COUNT)
        ua_created, ua_total = ensure_useraccounts(COUNT)
        req_created, req_total = ensure_requests(COUNT)
        sl_created, sl_total = ensure_shortlists(COUNT)
        sh_created, sh_total = ensure_servicehistory(COUNT)

        print('Seed summary:')
        print(f'  profiles_created: {p_created} (should be 0..4)')
        print(f'  categories_created: {cat_created} total={cat_total}')
        print(f'  useraccounts_created: {ua_created} total={ua_total}')
        print(f'  requests_created: {req_created} total={req_total}')
        print(f'  shortlists_created: {sl_created} total={sl_total}')
        print(f'  servicehistory_created: {sh_created} total={sh_total}')


if __name__ == '__main__':
    main()
