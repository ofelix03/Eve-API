from . import *
from api.models.pagination_cursor import PaginationCursor, BadCursorQuery
from api.auth.authenticator import Authenticator
from api.exceptions import UserNotFound


class BaseView(FlaskView):
    trailing_slash = True

    def get_auth_user(self):
        return Authenticator.get_instance().get_auth_user()

    def get_auth_user_without_auth_check(self):
        return Authenticator.get_instance().get_auth_user_without_auth_check()

    def after_request(self, name, response):
        return response

    def set_cursor(self, cursor_after=None, cursor_limit=None):
        self.cursor.set_after(cursor_after=cursor_after)
        self.cursor.set_limit(cursor_limit=cursor_limit)
        return self

    def get_cursor(self, request):
        cursor = PaginationCursor()
        try:
            if 'cursor_after' in request.args:
                cursor.set_after(request.args['cursor_after'])

            if 'cursor_before' in request.args:
                cursor.set_before(request.args['cursor_before'])

            if 'limit' in request.args:
                cursor.set_limit(request.args['limit'])

            return cursor
        except BadCursorQuery:
            return response({
                "ok": False,
                "code": "INVALID_CURSOR_QUERY_VALUE"
            }, 400)

