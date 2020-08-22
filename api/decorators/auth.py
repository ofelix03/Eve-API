from functools import wraps
from flask import make_response
import json

from api.auth.authenticator import Authenticator
from api.repositories.exceptions import NotAuthUser


def only_auth_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            Authenticator.get_instance().get_auth_user()
            return func(*args, **kwargs)
        except NotAuthUser:
            return make_response(json.dumps({
                "ok": False,
                "code": "NOT_AUTH_USER"
            }), 401)
    return wrapper

