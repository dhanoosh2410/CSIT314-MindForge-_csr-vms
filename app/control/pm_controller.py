# CONTROL: Platform Manager use cases (Category CRUD + search + Reports)
from ..entity.models import Category, ServiceHistory

class PMController:
	@staticmethod
	def search_categories(q):
		return Category.search(q)

	@staticmethod
	def get_categories():
		return Category.get_all()

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
	def generate_report(scope='daily'):
		return ServiceHistory.generate_report(scope=scope)
