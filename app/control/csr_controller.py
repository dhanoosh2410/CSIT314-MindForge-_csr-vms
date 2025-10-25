
# CONTROL: CSR Rep use cases (browse/search PIN requests, shortlist, history)
from datetime import datetime
from ..entity.models import db, Category, Request, Shortlist, ServiceHistory
from flask import session

class CSRController:
    @staticmethod
    def get_categories():
        return Category.query.order_by(Category.name).all()

    @staticmethod
    def search_requests(category_id=None):
        q = Request.query.filter_by(status='open')
        if category_id:
            q = q.filter_by(category_id=category_id)
        # Increase views_count for listing as a simple approximation of views
        for r in q.all():
            r.views_count += 1
        db.session.commit()
        return Request.query.filter_by(status='open').filter(
            (Request.category_id == category_id) if category_id else True
        ).order_by(Request.created_at.desc()).all()

    @staticmethod
    def save_request(req_id):
        csr_id = session.get('user_id')
        if not csr_id: return
        exists = Shortlist.query.filter_by(csr_id=csr_id, request_id=req_id).first()
        if not exists:
            db.session.add(Shortlist(csr_id=csr_id, request_id=req_id))
            # bump shortlist count on request
            r = Request.query.get(req_id)
            if r: r.shortlist_count += 1
            db.session.commit()

    @staticmethod
    def get_shortlist():
        csr_id = session.get('user_id')
        return Shortlist.query.filter_by(csr_id=csr_id).order_by(Shortlist.created_at.desc()).all()

    @staticmethod
    def history(category_id=None, start=None, end=None):
        q = ServiceHistory.query
        if category_id: q = q.filter_by(category_id=category_id)
        if start:
            q = q.filter(ServiceHistory.date_completed >= datetime.fromisoformat(start))
        if end:
            q = q.filter(ServiceHistory.date_completed <= datetime.fromisoformat(end))
        return q.order_by(ServiceHistory.date_completed.desc()).all()
