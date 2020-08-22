from api.views import *
from api.views.auth_base import AuthBaseView
from api.auth.authenticator import Authenticator
from marshmallow.exceptions import ValidationError
from api.serializers.brand import BrandSchema, CreateBrandSchema, BrandValidationSchema
from api.models.event import Brand, BrandCategory, BrandValidation, BrandMedia, BrandFounder
from api.repositories import exceptions
from api.utils import general as general_utils

brand_schema = BrandSchema()
create_brand_schema = CreateBrandSchema()
brand_validation_schema = BrandValidationSchema()


class BrandView(AuthBaseView):

    def index(self):
        try:
            cursor = self.get_cursor(request)
            if 'category_id' in request.args:
                category_id = request.args['category_id']
            else:
                category_id = None
            brands = Brand.get_brands(category_id=category_id, cursor=cursor)
            return response({
                'ok': True,
                'brands': brand_schema.dump(brands, many=True),
                'brands_count': Brand.get_brands_total(category_id=category_id),
                'metadata': {
                    'cursor': {
                        'before': cursor.before,
                        'after': cursor.after,
                        'has_more': cursor.has_more,
                        'limit': cursor.limit
                    }
                }

            })
        except exceptions.BrandCategoryNotFound:
            return response({
                "ok": False,
                "code": "BRAND_CATEGORY_NOT_FOUND"
            }, 400)

    def get(self, brand_id):
        try:
            brand = Brand.get_brand(brand_id)
            print("onebrand##", brand)
            return response({
                'ok': True,
                'brand': brand_schema.dump(brand)
            })
        except exceptions.BrandNotFound:
            return response({
                'ok': False,
                'code': "BRAND_NOT_FOUND"
            }, 400)

    def post(self):
        data = request.get_json()
        auth_user = Authenticator.get_instance().get_auth_user()

        try:
            data = create_brand_schema.load(data)
            name = data['name']
            description = data['description']
            country = data['country']
            category_id = data['category_id']
            image = data['image']
            image = BrandMedia(source_url=image['source_url'], format=image['format'], public_id=image['public_id'],
                               filename=image['filename'])
            founders = data['founder']
            brand_founders = []
            for founder in founders:
                [founder, founder_url] = general_utils.founder_url_explode(founder)
                brand_founders.append(BrandFounder(name=founder, url=founder_url))

            founded_date = data['founded_date']
            category = BrandCategory.get_category(category_id)
            website_link = data['website']
            brand = Brand.create(name=name, description=description, country=country, creator=auth_user,
                                 category=category, image=image, founders=brand_founders, founded_date=founded_date,
                                 website_link=website_link)
            return response(brand_schema.dump(brand))
        except ValidationError as e:
            return response({
                "errors": e.messages
            }, 400)
        except exceptions.BrandNotFound:
            return response({
                "ok": False,
                "code": "BRAND_NOT_FOUND"
            }, 400)
        except exceptions.BrandCategoryNotFound:
            return response({
                "ok": False,
                "code": "BRAND_CATEGORY_NOT_FOUND"
            }, 400)

    def put(self, brand_id):
        try:
            data = request.get_json()
            auth_user = Authenticator.get_instance().get_auth_user()
            brand = Brand.get_brand(brand_id)
            brand.creator = auth_user
            if 'name' in data:
                brand.name = data['name']

            if 'description' in data:
                brand.description = data['description']

            if 'country' in data:
                brand.country = data['country']

            if 'category_id' in data:
                category_id = data['category_id']
                brand.category = BrandCategory.get_category(category_id)

            if 'founder' in data:
                founders = data['founder']
                brand_founders = []
                for founder in founders:
                    [founder, founder_url] = general_utils.founder_url_explode(str(founder))
                    brand_founders.append(BrandFounder(name=founder, url=founder_url))
                brand.founders = brand_founders

            if 'founded_date' in data:
                brand.founded_date = data['founded_date']

            if 'website' in data:
                brand.website_link = data['website']

            if 'image' in data:
                image = data['image']
                brand.image = BrandMedia(source_url=image['source_url'], format=image['format'],
                                         public_id=image['public_id'], filename=image['filename'])

            brand.update()
            return response(brand_schema.dump(brand))
        except exceptions.BrandNotFound:
            return response({
                "ok": False,
                "code": "BRAND_NOT_FOUND"
            }, 400)
        except exceptions.BrandCategoryNotFound:
            return response({
                "ok": False,
                "code": "BRAND_CATEGORY_NOT_FOUND"
            }, 400)

    def delete(self, brand_id):
        try:
            Brand.delete_brand(brand_id)
            return response("")
        except exceptions.BrandNotFound:
            return response({
                "ok": False,
                "code": "BRAND_NOT_FOUND"
            }, 400)

    @route('search', methods=['GET'])
    def search_brand(self):

        cursor = self.get_cursor(request)
        if 'q' in request.args:
            searchterm = request.args['q']
            brands = Brand.get_brands(searchterm=searchterm, cursor=cursor)
            brands_total = Brand.get_brands_total(searchterm=searchterm)
            return response({
                "ok": True,
                "brands": brand_schema.dump(brands, many=True),
                "brands_count": brands_total,
                "metadata": {
                    "cursor": {
                        "before": cursor.before,
                        "after": cursor.after,
                        "cursor": cursor.has_more,
                        "limit": cursor.limit
                    }
                }
            })

        return response({
            "ok": True,
            "brands": []
        })

    @route('<string:brand_id>/validations', methods=['GET'])
    def get_brand_endorsements(self, brand_id):
        try:
            brand = Brand.get_brand(brand_id)
            brand_endorsements = brand.get_brand_endorsements(brand_id)
            return response({
                'ok': True,
                'brand_endorsements': brand_validation_schema.dump(brand_endorsements, many=True)
            })
        except exceptions.BrandNotFound:
            return response({
                "ok": False,
                "code": "BRAND_NOT_FOUND"
            }, 400)

    @route('<string:brand_id>/endorsements', methods=['POST'])
    def create_brand_validation(self, brand_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            brand = Brand.get_brand(brand_id)
            brand.add_validation(BrandValidation(validator=auth_user))
            return response(brand_schema.dump(brand))
        except exceptions.BrandAlreadyValidated:
            brand.remove_validation_of_user(auth_user)
            return response(brand_schema.dump(Brand.get_brand(brand.id)))
        except exceptions.BrandNotFound:
            return response({
                "ok": False,
                "code": "BRAND_NOT_FOUND"
            }, 400)
