
# CONTROL: Reporting (daily/weekly/monthly aggregates) for PM
from sqlalchemy.sql import func
from ..entity.models import db, Request, ServiceHistory

class ReportController:
    @staticmethod
    def generate(scope='daily'):
        # Aggregate counts of requests and completed services
        if scope == 'weekly':
            fmt = '%Y-W%W'
        elif scope == 'monthly':
            fmt = '%Y-%m'
        else:
            fmt = '%Y-%m-%d'
        reqs = db.session.query(func.strftime(fmt, Request.created_at), func.count(Request.id))                .group_by(func.strftime(fmt, Request.created_at)).all()
        done = db.session.query(func.strftime(fmt, ServiceHistory.date_completed), func.count(ServiceHistory.id))                .group_by(func.strftime(fmt, ServiceHistory.date_completed)).all()
        return {'requests': reqs, 'completed': done}
