# CONTROL: Platform Manager use cases (Category CRUD + search + Reports)
from ..entity.models import Category, ServiceHistory

class PMController:
    @staticmethod
    def search_categories(q):
        return Category.search(q)

    @staticmethod
    def get_categories():
        return Category.get_all()

    # NEW: paginated categories
    @staticmethod
    def get_categories_paginated(q: str = "", page: int = 1, per_page: int = 12, order: str = "asc"):
        return Category.paginate(q=q, page=page, per_page=per_page, order=order)

    @staticmethod
    def create_category(name):
        return Category.create(name)

    @staticmethod
    def update_category(cat_id, name):
        return Category.update(cat_id, name)

    @staticmethod
    def delete_category(cat_id):
        return Category.delete(cat_id)

    @staticmethod
    def generate_report(scope='daily', page: int = 1, per_page: int = 20, order: str = 'asc'):
        return ServiceHistory.generate_report(scope=scope, page=page, per_page=per_page, order=order)

