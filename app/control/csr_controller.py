
# CONTROL: CSR Rep use cases (browse/search PIN requests, shortlist, history)
from datetime import datetime
from ..entity.models import db, Category, Request, Shortlist, ServiceHistory
from flask import session

class CSRController:
    @staticmethod
    def get_categories():
        return Category.get_all()

    @staticmethod
    def search_requests(category_id=None):
        return Request.list_open(category_id=category_id)

    @staticmethod
    def save_request(req_id):
        csr_id = session.get('user_id')
        if not csr_id: return
        Shortlist.add_if_not_exists(csr_id, req_id)

    @staticmethod
    def get_shortlist():
        csr_id = session.get('user_id')
        return Shortlist.for_csr(csr_id)

    @staticmethod
    def history(category_id=None, start=None, end=None):
        sd = datetime.fromisoformat(start) if start else None
        ed = datetime.fromisoformat(end) if end else None
        return ServiceHistory.filter_history(category_id=category_id, start=sd, end=ed)
