from . import *
from api.serializers.event import EventCategorySchema
from api.models.event import EventCategory
from api.repositories import exceptions


event_category_schema = EventCategorySchema()


class EventCategoryView(FlaskView):

    def get(self, category_id=None):
        try:
            event_category = EventCategory.get_category(category_id)
            return response({
                'ok': True,
                'category': event_category_schema.dump(event_category)
            })
        except exceptions.BrandCategoryNotFound:
            return response({
                "ok": False,
                "code": "BRAND_CATEGORY_NOT_FOUND"
            }, 400)

    def put(self, category_id=None):
        try:
            data = request.get_json()
            event_category = EventCategory.get_category(category_id)
            event_category.name = data['name']
            event_category.update()
        except exceptions.EventCategoryNotFound:
            return response({
                "ok": False,
                "code": "EVENT_CATEGORY_NOT_FOUND"
            }, 400)

    def delete(self, category_id=None):
        try:
            EventCategory.delete_category(category_id)
            return response("")
        except exceptions.EventCategoryNotFound:
            return response({
                "ok": False,
                "code": "EVENT_CATEGORY_NOT_FOUND"
            }, 400)

    def index(self):
        categories = EventCategory.get_categories()
        return response({
            "ok": True,
            "categories": EventCategorySchema().dump(categories, many=True)
        })

    def post(self):
        data = request.get_json()
        is_valid_data = EventCategorySchema().validate(data, partial=['id'])
        if is_valid_data == {}:
            name = None
            image = None
            if 'name' in data:
                name = data['name']

            if 'image' in data:
                image = data['image']

            category = EventCategory.create(name=name, image=image)
            return response({
                "ok": True,
                "category": event_category_schema.dump(category)
            }, 201)
        else:
            return response({
                "ok": False,
                "code": "BAD_REQUEST"
            }, 400)

    @route('/search')
    def search(self):
        queries = request.args
        if 'q' in queries:
            search_term = queries.get('q')
            categories = EventCategory.find_category_by_searchterm(search_term)
            return response({
                'ok': True,
                'categories': event_category_schema.dump(categories, many=True)
            })
        else:
            return response({
                'ok': False,
                "message": "Bad request",
                "errors": {
                    'q': 'search query parameter is required'
                }
            }, 400)


