
# CONTROL: PIN use cases (CRUD requests, search, view counts, history filters)
from datetime import datetime
from flask import session
from ..entity.models import db, Category, Request, ServiceHistory

class PINController:
    @staticmethod
    def get_categories():
        return Category.get_all()

    @staticmethod
    def list_my_requests(q):
        pin_id = session.get('user_id')
        return Request.search_by_pin(pin_id, q)

    @staticmethod
    def create_request(title, description, category_id):
        pin_id = session.get('user_id')
        if not title: return False, 'Title required.'
        Request.create_for_pin(pin_id, title, description, category_id)
        return True, 'Request created.'

    @staticmethod
    def update_request(req_id, title, description, category_id, status):
        ok = Request.update_by_id(req_id, title, description, category_id, status)
        if not ok:
            return False, 'Not found.'
        return True, 'Request updated.'

    @staticmethod
    def delete_request(req_id):
        Request.delete_by_id(req_id)

    @staticmethod
    def history(category_id=None, start=None, end=None):
        q = ServiceHistory.query
        if category_id: q = q.filter_by(category_id=category_id)
        if start:
            q = q.filter(ServiceHistory.date_completed >= datetime.fromisoformat(start))
        if end:
            q = q.filter(ServiceHistory.date_completed <= datetime.fromisoformat(end))
        return q.order_by(ServiceHistory.date_completed.desc()).all()
