from . import *
from api.views.auth_base import AuthBaseView
from api.serializers.user import UserSchema, UserSummarySchema, UserSchemaFull
from api.serializers.event import EventSchema, EventSummarySchema


user_schema = UserSchema()
user_full_schema = UserSchemaFull()
user_summary_schema = UserSummarySchema()
event_schema = EventSchema()
event_summary_schema = EventSummarySchema()


class MeView(AuthBaseView):

    def index(self):
        auth_user = self.get_auth_user()
        return response(user_full_schema.dump(auth_user))

    @route('/created-events', methods=['GET'])
    def get_created_events(self):
        auth_user = self.get_auth_user()
        events = auth_user.get_created_events()
        return response({
            "events": event_summary_schema.dump(events, many=True)
        })

    @route('/attending-events', methods=['GET'])
    def get_attending_events(self):
        auth_user = self.get_auth_user()

        events = auth_user.get_attending_events()
        return response({
            "events": event_summary_schema.dump(events, many=True)
        })

    @route('/bookmarked-events', methods=['GET'])
    def get_bookmarked_events(self):

        auth_user = self.get_auth_user()

        events = auth_user.get_bookmarked_events()
        return response({
            "events": event_summary_schema.dump(events, many=True)
        })

