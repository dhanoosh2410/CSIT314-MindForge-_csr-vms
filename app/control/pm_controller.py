# CONTROL: Platform Manager use cases (Category CRUD + search + Reports)
from sqlalchemy.sql import func
from ..entity.models import db, Category, Request, ServiceHistory

class PMController:
    # ------- Categories -------
    @staticmethod
    def search_categories(q):
        return Category.search(q)

    @staticmethod
    def create_category(name):
        db.session.add(Category(name=name)); db.session.commit()

    @staticmethod
    def update_category(cat_id, name):
        c = Category.query.get(cat_id)
        if c:
            c.name = name
            db.session.commit()

    @staticmethod
    def delete_category(cat_id):
        c = Category.query.get(cat_id)
        if c:
            db.session.delete(c)
            db.session.commit()

    # ------- Reports -------
    @staticmethod
    def generate_report(scope='daily'):
        """
        Aggregate counts of requests created and services completed
        grouped by day/week/month, using SQLite's strftime pattern
        (works with your current DB config).
        """
        if scope == 'weekly':
            fmt = '%Y-W%W'
        elif scope == 'monthly':
            fmt = '%Y-%m'
        else:
            fmt = '%Y-%m-%d'

        # Requests created per bucket
        reqs = (
            db.session.query(
                func.strftime(fmt, Request.created_at),
                func.count(Request.id)
            )
            .group_by(func.strftime(fmt, Request.created_at))
            .all()
        )

        # Completed services per bucket
        done = (
            db.session.query(
                func.strftime(fmt, ServiceHistory.date_completed),
                func.count(ServiceHistory.id)
            )
            .group_by(func.strftime(fmt, ServiceHistory.date_completed))
            .all()
        )

        return {'requests': reqs, 'completed': done}
