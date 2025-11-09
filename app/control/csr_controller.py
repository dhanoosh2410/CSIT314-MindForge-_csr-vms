
# CONTROL: CSR Rep use cases (browse/search PIN requests, shortlist, history)
from datetime import datetime, timezone
from ..entity.models import Category, Request, Shortlist, ServiceHistory, db
from flask import session

class CSRController:
    @staticmethod
    def get_categories():
        return Category.get_all()

    @staticmethod
    def search_requests(category_id=None, q: str = '', page=1, per_page=12):
        # return paginated open requests without changing view counts.
        # supports optional category filter and text search q
        return Request.paginate_open_no_increment(category_id=category_id, q=(q or '').strip() or None, page=page, per_page=per_page)

    @staticmethod
    def get_open_requests(category_id=None, page=1, per_page=12):
        return Request.paginate_open_no_increment(category_id=category_id, q=None, page=page, per_page=per_page)

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
    def search_shortlist(q: str = None, category_id: int = None):
        # return shortlist items for current CSR optionally filtered by query and/or category
        csr_id = session.get('user_id')
        if not csr_id:
            return []
        return Shortlist.search_for_csr(csr_id, q=(q or '').strip() or None, category_id=category_id)

    @staticmethod
    def remove_request(req_id):
        csr_id = session.get('user_id')
        if not csr_id:
            return False
        return Shortlist.remove_if_exists(csr_id, req_id)

    @staticmethod
    def accept_request(req_id):
        csr_id = session.get('user_id')
        if not csr_id:
            return False
        r = Request.query.get(req_id)
        if not r or r.status != 'open':
            return False
        try:
            r.accepted_csr_id = csr_id
            r.accepted_at = datetime.now(timezone.utc)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    @staticmethod
    def history(category_id=None, start=None, end=None, page=1, per_page=12):
        sd = datetime.fromisoformat(start) if start else None
        ed = datetime.fromisoformat(end) if end else None
        csr_id = session.get('user_id')
        # return paginated history relevant to the current CSR
        return ServiceHistory.paginate_for_csr(csr_id=csr_id, category_id=category_id, start=sd, end=ed, page=page, per_page=per_page)

    @staticmethod
    def get_request(req_id):
        # return the open request and increment views only once per CSR session
        r = Request.get_if_open(req_id)
        if not r:
            return None
        viewed = session.get('viewed_requests') or set()
        if isinstance(viewed, list):
            viewed = set(viewed)
        if r.id not in viewed:
            # increment the counter and mark as viewed in this session
            Request.increment_views(r.id)
            viewed.add(r.id)
            session['viewed_requests'] = list(viewed)
        return r

    @staticmethod
    def is_saved_by(req_id):
        csr_id = session.get('user_id')
        if not csr_id:
            return False
        return Shortlist.exists(csr_id, req_id)
