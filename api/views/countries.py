from marshmallow import ValidationError

from . import *
from api.serializers.user import CountrySerializer
from api.models.event import Country
from api.repositories import exceptions

country_serializer = CountrySerializer()


class CountryView(FlaskView):

    def index(self):
        countries = Country.get_countries()
        return response({
            "ok": True,
            "countries": country_serializer.dump(countries, many=True)
        })

    def post(self):
        try:
            data = country_serializer.load(request.get_json())
            country = Country.create(name=data['name'], code=data['code'], calling_code=data['calling_code'])
            return response(country_serializer.dump(country))
        except ValidationError as e:
            return response({
                "errors": e.messages
            })

    def put(self, country_id):
        try:
            data = country_serializer.load(request.get_json())
            country = Country.get_country(country_id)
            country.name = data['name']
            country.calling_code = data['calling_code']
            country.code = data['code']
            country.update()
            return response(country_serializer.dump(country))
        except ValidationError as e:
            return response({
                "errors": e.messages
            }, 400)
        except exceptions.CountryNotFound:
            return response({
                "ok": False,
                "code": "COUNTRY_NOT_FOUND"
            }, 400)

    def delete(self, country_id):
        try:
            Country.remove_country(country_id)
            return response("")
            return response("")
        except exceptions.CountryNotFound:
            return response({
                "ok": False,
                "code": "COUNTRY_NOT_FOUND"
            }, 400)

    @route('/search', methods=['GET'])
    def search(self):
        if 'q' not in request.args:
            return response({
                "errors": {
                    "message": "[q] query string is required"
                }
            }, 400)

        search_term = request.args['q']
        countries = Country.find_countries_by_searchterm(search_term)
        return response({
            "ok": True,
            "countries": country_serializer.dump(countries, many=True)
        })
