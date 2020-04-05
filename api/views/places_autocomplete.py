from marshmallow import ValidationError

from . import *
import googlemaps
from ..utils import GOOGLE_CLOUD_API_KEY


class PlacesAutocompleteView(FlaskView):

    def index(self):
        try:
            if request.args:
                input_text = request.args['input_text'] if 'input_text' in request.args else None
                offset = request.args['offset'] if 'offset' in request.args else None
                location = request.args['location'] if 'location' in request.args else None
                radius = request.args['radisu'] if 'radius' in request.args else None
                types = request.args['types'] if 'types' in request.args else None

                results = []
                if input_text:
                    gmaps = googlemaps.Client(key=GOOGLE_CLOUD_API_KEY)
                    places = gmaps.places_autocomplete(input_text=input_text)
                    print("places##", places)
                    for place in places:
                        results.append({
                            'name': place['description'],
                            'type': place['types']
                        })
                return response({
                    'ok': True,
                    'results': results,
                })
        except googlemaps.exceptions.Timeout:
            return response({
                'ok': False,
                'code': 'REQUEST_TIMEOUT'
            }, 408)

    @route('/reverse_geocode', methods=['POST'])
    def reverse_geocode(self):
        data = request.get_json()
        if 'latitude' in data and 'longitude' in data:
            latlng = (data['latitude'], data['longitude'])
            gmaps = googlemaps.Client(key=GOOGLE_CLOUD_API_KEY)
            results = gmaps.reverse_geocode(latlng, result_type=['country'])
            if len(results):
                country_name = results[0]['address_components'][0]['long_name']
                country_shortname = results[0]['address_components'][0]['short_name']
                return response({
                    'ok': True,
                    'data': {
                        'country': {
                            'name': country_name,
                            'shortname': country_shortname
                        }
                    }
                })
            else:
                return response({
                    'ok': True,
                    'code': 'EMPTY_RESULT',
                    'data': None
                })
        else:
            return response({
                'ok': False,
                'code': 'MISSING_PARAMETERS',
            }, 400)

    @route('/geocode', methods=['POST'])
    def geocode(self):
        data = request.get_json()
        if 'address' in data:
            address = data['address']
            gmaps = googlemaps.Client(key=GOOGLE_CLOUD_API_KEY)
            results = gmaps.geocode(address)
            print("myresult##", results)
            if len(results) > 0:
                result = results[0]
                return response({
                    'ok': True,
                    'data': {
                        'geocode': {
                            'lat': result['geometry']['location']['lat'],
                            'lng': result['geometry']['location']['lng']
                        }
                    }
                })
            else:
                return response({
                    'ok': True,
                    'data': []
                })
        else:
            return response({
                'ok': False,
                'code': 'BAD_REQUEST'
            }, 400)


