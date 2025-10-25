
# CONTROL: PIN use cases (CRUD requests, search, view counts, history filters)
from datetime import datetime
from flask import session
from ..entity.models import db, Category, Request, ServiceHistory

class PINController:
    @staticmethod
    def get_categories():
        return Category.query.order_by(Category.name).all()

    @staticmethod
    def list_my_requests(q):
        pin_id = session.get('user_id')
        query = Request.query.filter_by(pin_id=pin_id)
        if q:
            like=f"%{q}%"
            query = query.filter((Request.title.like(like)) | (Request.description.like(like)))
        return query.order_by(Request.created_at.desc()).all()

    @staticmethod
    def create_request(title, description, category_id):
        pin_id = session.get('user_id')
        if not title: return False, 'Title required.'
        r = Request(pin_id=pin_id, title=title, description=description, category_id=category_id, status='open')
        db.session.add(r); db.session.commit()
        return True, 'Request created.'

    @staticmethod
    def update_request(req_id, title, description, category_id, status):
        r = Request.query.get(req_id)
        if not r: return False, 'Not found.'
        r.title = title; r.description = description; r.category_id = category_id; r.status = status
        db.session.commit()
        return True, 'Request updated.'

    @staticmethod
    def delete_request(req_id):
        r = Request.query.get(req_id)
        if r: db.session.delete(r); db.session.commit()

    @staticmethod
    def history(category_id=None, start=None, end=None):
        q = ServiceHistory.query
        if category_id: q = q.filter_by(category_id=category_id)
        if start:
            q = q.filter(ServiceHistory.date_completed >= datetime.fromisoformat(start))
        if end:
            q = q.filter(ServiceHistory.date_completed <= datetime.fromisoformat(end))
        return q.order_by(ServiceHistory.date_completed.desc()).all()
