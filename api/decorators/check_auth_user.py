from flask import make_response
import json

from api.repositories.exceptions import NotAuthUser


def check_auth_user(func):
    print("amhere##", func)
    def decorator():
        try:
            return func
        except NotAuthUser:
            return make_response(json.dumps({
                "ok": False,
                "code": "NOT_AUTH_USER"
            }), 401)
    return decorator
