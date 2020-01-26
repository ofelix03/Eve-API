from api.repositories.base import Repository
from api.models.event import EventCategory


class EventCategoryRepository(Repository):

    model = EventCategory

    def get_categories(self):
        return self.query(self.model).all()

    def get_category(self, category_id):
        return self.query(self.model).filter_by(id=category_id).first()

    def update_category(self, category_id=None, data=None):
        self.query(self.model).filter_by(id=category_id).update(data)
        self.session.commit()
        return self.get_category(category_id)

    def has_category(self, category_id):
        return self.query(self.model).filter_by(id=category_id).count()

    def delete_category(self, category_id):
        is_deleted = self.query(self.model).filter_by(id=category_id).delete()
        self.session.commit()

    def add_catgory(self, category):
        self.session.add(category)
        self.session.commit()
        return category

    def find_category_by_searchterm(self, search_term):
        search_term = '%' + search_term + '%'
        categories = self.session.query(EventCategory).filter(EventCategory.name.ilike(search_term)).all()
        return categories
