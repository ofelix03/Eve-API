from api.views import *
from api.views.auth_base import AuthBaseView
from marshmallow.exceptions import ValidationError
from api.models.event import BrandCategory
from api.serializers.brand import BrandCategorySchema
from api.repositories import exceptions

brand_category_schema = BrandCategorySchema()


class BrandCategoryView(AuthBaseView):

    def index(self):
        categories = BrandCategory.get_categories()
        return response({
            'brand_categories': brand_category_schema.dump(categories, many=True)
        })

    def post(self):
        try:
            data = brand_category_schema.load(request.get_json())
        except ValidationError as e:
            return response({
                'errors': e.message
            }, 400)

        category = BrandCategory(name=data['name'])
        BrandCategory.add_category(category)
        return response({
            'creatd_id': category.id
        }, 201)

    def put(self, category_id):
        try:
            data = brand_category_schema.load(request.get_json())
            brand_catogry = BrandCategory.get_category(category_id)
            brand_catogry.update(name=data['name'])
            brand_category = BrandCategory.get_category(category_id)
            return response(brand_category_schema.dump(brand_catogry), 200)
        except exceptions.BrandCategoryNotFound:
            return response({
                "ok": False,
                "code": "BRAND_CATEGORY_NOT_FOUND"
            }, 400)
        except ValidationError as e:
            return response({
                'errors': e.message
            }, 400)

    def delete(self, category_id):
       try:
           BrandCategory.remove_category(category_id)
           return response("", 200)
       except exceptions.BrandCategoryNotFound:
           return response({
               "ok": False,
               "code": "BRAND_CATEGORY_NOT_FOUND"
           }, 400)

