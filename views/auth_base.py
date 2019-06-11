from . import *
from api.views.base import BaseView
from api.auth.authenticator import UserAuthFail
from api.serializers import user as user_schemas
from api.auth.authenticator import Authenticator


user_summary_schema = user_schemas.UserSummarySchema()

USERS_UNGUARDED_ENDPOINTS = ['login_user', 'index', 'get']
BRANDS_UNGUARDED_ENDPOINTS = ['index', 'search_brand', 'get_brand_validations', 'get_created_events']
EVENT_UNGUARDED_ENDPOINTS = ['get_event_reviews', 'get_event_review', 'get_review_comments', 'get_event_review_comment_responses', 'get_event_attendees']
UNGUARDED_ENDPOINTS = USERS_UNGUARDED_ENDPOINTS + BRANDS_UNGUARDED_ENDPOINTS + EVENT_UNGUARDED_ENDPOINTS


class AuthBaseView(BaseView):

    def get_auth_user(self):
        return Authenticator.get_instance().get_auth_user()

    @staticmethod
    def before_request(name, *args, **kwargs):
        try:
            Authenticator.get_instance().authenticate(request)
        except UserAuthFail:
            if name not in UNGUARDED_ENDPOINTS:
                return response({
                    'ok': False,
                    "errors": {
                        "message": "Authentication failed"
                    }
                }, 401)