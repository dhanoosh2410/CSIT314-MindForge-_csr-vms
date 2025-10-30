
# CONTROL: PIN use cases (CRUD requests, search, view counts, history filters)
from datetime import datetime
from flask import session
from ..entity.models import Category, Request, ServiceHistory

class PINController:
    @staticmethod
    def get_categories():
        return Category.get_all()

    @staticmethod
    def list_my_requests(q, page=1, per_page=12):
        """return paginated requests for the current PIN filtered by q.

        the boundary layer (routes) should pass page and per_page values extracted from
        the HTTP request

        returns a paginated dict with keys: items, total, page, per_page, pages.
        """
        pin_id = session.get('user_id')
        if not pin_id:
            return { 'items': [], 'total': 0, 'page': 1, 'per_page': per_page, 'pages': 1 }
        return Request.paginate_for_pin(pin_id=pin_id, q=q, page=page, per_page=per_page)

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
        # basic validation: title required
        title = (title or '').strip()
        if not title:
            return False, 'Title required.'

        # validate category id if provided
        cat_id = None
        if category_id:
            try:
                cat_id = int(category_id)
            except (TypeError, ValueError):
                return False, 'Invalid category.'
            if not Category.get_by_id(cat_id):
                return False, 'Invalid category.'

        ok = Request.update_by_id(req_id, title, description or '', cat_id, status)
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
    def history(category_id=None, start=None, end=None, q=None):
        # return completed matches relevant to the current PIN user, with optional search q
        pin_id = session.get('user_id')
        sd = datetime.fromisoformat(start) if start else None
        ed = datetime.fromisoformat(end) if end else None
        return ServiceHistory.filter_for_pin(pin_id=pin_id, category_id=category_id, start=sd, end=ed, q=q)
