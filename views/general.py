from . import *
from api.serializers.user import CountrySerializer
from api.services.geolocation_service import GeolocationService
from api.models.event import Country

country_serializer = CountrySerializer()


class GeneralView(FlaskView):
    trailing_slash = True

    @route('/reverse-geocode', methods=['POST'])
    def reverse_geocode(self):
        data = request.get_json()
        print
        if 'latitude' not in data or 'longitude' not in data:
            return response({
                "ok": "false",
                "message": "required field missing",
                "code": '400'
            }, 400)
        geolocation_service = GeolocationService()
        address = geolocation_service.reverse_search(latitude=data['latitude'], longitude=data['longitude'])
        country = Country.get_country_by_code(address.country_code)
        return response(country_serializer.dump(country))