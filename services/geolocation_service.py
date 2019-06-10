import requests


class ResponseDataMapper(object):
    type = 'adminArea1Type'
    country_code = 'adminArea1'
    city_name = 'adminArea5'
    state = 'adminArea3'
    postal_code = 'postalCode'


class Address(object):
    def __init__(self, country_name=None, country_code=None, city_name=None, state=None, postal_code=None):
        self.country_name = country_name
        self.country_code = country_code
        self.city_name = city_name
        self.state = state
        self.postal_code = postal_code


class GeolocationService(object):
    API_KEY = 'JIEAeISjTGdne1yoE5H9G2erfVGTqtGS'
    BASE_URL = 'http://www.mapquestapi.com/geocoding/v1/'
    REVERSE_SEARCH_URL = BASE_URL + 'reverse?outFormat=json&key=' + API_KEY
    ADDRESS_SEARCH_URL = BASE_URL = 'address?outFormat=json&key=' + API_KEY

    URL = "http://www.mapquestapi.com/geocoding/v1/reverse?key=JIEAeISjTGdne1yoE5H9G2erfVGTqtGS&outFormat=json"

    def reverse_search(self, latitude=None, longitude=None):
        data = {
            "location": {
                "latLng": {
                    "lat": float(latitude),
                    "lng": float(longitude)}
            }
        }
        print("data##", data)
        resp = requests.post(GeolocationService.URL, json=data)
        address = Address()
        if resp.status_code == requests.codes.ok:
            # print("data", resp.json())
            locations = resp.json()['results'][0]['locations']
            if locations:
                location = locations[0]
                city_name = location[ResponseDataMapper.city_name]
                state = location[ResponseDataMapper.state]
                postal_code = location[ResponseDataMapper.postal_code]
                country_code = location[ResponseDataMapper.country_code]
                return Address(city_name=city_name,state=state, postal_code=postal_code, country_code=country_code)
        return address

    def search(self, address=None):
        pass


