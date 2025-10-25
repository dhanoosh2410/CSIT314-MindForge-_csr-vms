
# CONTROL: Platform Manager use cases (Category CRUD + search)
from ..entity.models import db, Category

class PMController:
    @staticmethod
    def search_categories(q):
        query = Category.query
        if q:
            query = query.filter(Category.name.like(f"%{q}%"))
        return query.order_by(Category.name).all()

    @staticmethod
    def create_category(name):
        db.session.add(Category(name=name)); db.session.commit()

    @staticmethod
    def update_category(cat_id, name):
        c = Category.query.get(cat_id)
        if c: c.name = name; db.session.commit()

    @staticmethod
    def delete_category(cat_id):
        c = Category.query.get(cat_id)
        if c: db.session.delete(c); db.session.commit()
