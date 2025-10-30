
# CONTROL: PIN use cases (CRUD requests, search, view counts, history filters)
from datetime import datetime
from flask import session
from ..entity.models import Category, Request, ServiceHistory

class PINController:
    @staticmethod
    def get_categories():
        return Category.get_all()

    @staticmethod
    def list_my_requests(q):
        pin_id = session.get('user_id')
        return Request.search_by_pin(pin_id, q)

    @staticmethod
    def get_request(req_id):
        pin_id = session.get('user_id')
        return Request.get_for_pin(req_id, pin_id)

    @staticmethod
    def create_request(title, description, category_id):
        pin_id = session.get('user_id')
        title = (title or '').strip()
        description = (description or '').strip()
        if not title:
            return False, 'Title required.'
        cat_id = None
        if category_id:
            try:
                cat_id = int(category_id)
            except (TypeError, ValueError):
                return False, 'Invalid category.'
            # ensure category exists via entity helper
            if not Category.get_by_id(cat_id):
                return False, 'Invalid category.'

        Request.create_for_pin(pin_id, title, description, cat_id)
        return True, 'Request created.'

    @staticmethod
    def update_request(req_id, title, description, category_id, status):
        # ownership check
        pin_id = session.get('user_id')
        r = Request.get_for_pin(req_id, pin_id)
        if not r:
            return False, 'Not found or permission denied.'
        ok = Request.update_by_id(req_id, title, description, category_id, status)
        if not ok:
            return False, 'Not found.'
        return True, 'Request updated.'

    @staticmethod
    def delete_request(req_id):
        # ownership check
        pin_id = session.get('user_id')
        r = Request.get_for_pin(req_id, pin_id)
        if not r:
            return False
        Request.delete_by_id(req_id)
        return True

    @staticmethod
    def history(category_id=None, start=None, end=None):
        # return completed matches relevant to the current PIN user
        pin_id = session.get('user_id')
        sd = datetime.fromisoformat(start) if start else None
        ed = datetime.fromisoformat(end) if end else None
        return ServiceHistory.filter_for_pin(pin_id=pin_id, category_id=category_id, start=sd, end=ed)
