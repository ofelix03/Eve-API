import simplejson as json
from flask import request, make_response
from flask_classy import FlaskView, route

headers = {
    'content-type': 'application/json'
}


def response(payload=None, status=200, headers=headers):
    return make_response(json.dumps(payload), status, headers)

