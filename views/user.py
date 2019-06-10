from . import *
from marshmallow import ValidationError
from api.views.auth_base import AuthBaseView
from api.repositories import exceptions
from api.auth.authenticator import Authenticator, data_encryptor
from api.models.event import User, UserLoginSession, Country, Notification
from api.models.domain.user_payment_info import CardPaymentInfo, MobilePaymentInfo, PaymentTypes
from api import serializers
from api import exceptions

from api import utils


class UserView(AuthBaseView):

    def index(self):
        users = User.get_users()
        return response({
            'ok': True,
            'users': serializers.user_summary_schema.dump(users, many=True)
        })

    @route('/me/update-profile', methods=['PUT'])
    def update_user_profile(self):
        print("updating user")
        auth_user = Authenticator.get_instance().get_auth_user()

        data = request.get_json()
        profile = User.get_user(auth_user.id)

        if 'name' in data and data['name'] != profile.name:
            auth_user.name = data['name']

        if 'email' in data and data['email'] != profile.email:
            profile.email = data['name']

        if 'phone_number' in data and data['phone_number'] != profile.phone_number:
            profile.phone_number = data['phone_number']

        if 'country_id' in data and data['country_id'] != profile.country_id:
            country_id = data['country_id']
            if not Country.has_country(country_id):
                return response({
                    "errors": {
                        "message": "Country not found"
                    }
                }, 400)
            profile.country = Country.get_country(country_id)
        profile.update()

        return response(serializers.user_schema.dump(profile))

    def delete(self, user_id=None):
        pass

    def post(self):
        data = request.get_json()
        try:
            data = serializers.create_user_schema.dump(data)
            password = utils.hash_password(data['password'])
            name = data['name']
            email = data['email']
            gender = data['gender']
            phone_number = data['phone_number']

            if not Country.has_country(data['country_id']):
                return response({
                    "errors": {
                        "message": "Country not found"
                    }
                }, 400)
            country = Country.get_country(data['country_id'])
            user = User.create(name=name, email=email, password=password,country=country, gender=gender,phone_number=phone_number)
            return response(serializers.user_schema.dump(user))
        except exceptions.UserAlreadyExists:
            return response({
                "errors": {
                    "message": "User already exists"
                }
            }, 400)
        except ValidationError as e:
            return response({
                "errors": e.messages
            }, 400)

    @route('/logout', methods=['POST'])
    def logout_user(self):
        user = Authenticator.get_instance().get_auth_user()
        user.remove_login_session()
        return response("")

    @route('/login', methods=['POST'])
    def login_user(self):
        try:
            data = serializers.login_user_schema.load(request.get_json())
            email = data['email']
            password = data['password']

            if not User.has_email(email):
                return response({
                    "errors": {
                        "message": "Authentication failed"
                    }
                }, 401)

            user = User.get_user_by_email(email)

            if not utils.check_password(password, user.password):
                return response({
                    "errors": {
                        "message": "Authentication failed"
                    }
                }, 401)

            session_user = serializers.logged_in_user_schema.dump(user)
            if not user.has_login_session():
                session_token = data_encryptor.encrypt(session_user, utils.ENCRYPTION_KEY)
                user.login_session = [UserLoginSession(session_token=session_token, user=user)]
                user.update()
            else:
                session_token = user.login_session[0].session_token

            return response({
                "session_token": session_token,
                "session_user": session_user
            })
        except ValidationError as e:
            return response({
                "errors": {
                    "message": e.messages
                }
            }, 400)

    @route('/me/change-password', methods=["PUT"])
    def change_user_password(self):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            data = request.get_json()
            data = serializers.change_user_password_schema.load(data)

            new_password = data['new_password']
            new_password_confirmation = data['new_password_confirmation']

            auth_user.change_password(new_password, new_password_confirmation)
            return response(None)
        except ValidationError as e:
            return response({
                "ok": False,
                "errors": e.messages
            }, 400)
        except exceptions.user.PasswordConfirmationMismatch:
            return response({
                'ok': False,
                'code': 'USER_PASSWORD_CONFIRMATION_MISMATCH'
            }, 400)

    @route('/me/new-password-request', methods=['GET'])
    def reset_password_send_link_notification(self):
        pass

    @route('/<string:user_id>')
    def get_user(self, user_id):
        try:
            user = User.get_user(user_id)
            return response(serializers.user_summary_schema.dump(user))
        except exceptions.user.UserNotFound:
            return response({
                'ok': False,
                'code': 'USER_NOT_FOUND'
            }, 404)

    @route('/search', methods=['GET'])
    def search(self):
        if 'q' not in request.args:
            return response({
                "message": "Bad request",
                "errors": {
                    "q": "searchterm query parameter missing"
                }
            })
        searchterm = request.args['q']
        users = User.find_users_by_searchterm(searchterm)
        return response({
            'ok': True,
            'users': serializers.user_summary_schema.dump(users, many=True)
        })

    @route('/me', methods=['GET'])
    @route('/<string:user_id>/profile')
    def get_my_profile(self, user_id=None):
        try:
            if not user_id:
                auth_user = Authenticator.get_instance().get_auth_user()
                user = User.get_user_full(auth_user.id)
            else:
                user = User.get_user_full(user_id)
            return response(serializers.user_full_schema.dump(user))
        except exceptions.user.UserNotFound:
            return response({
                'ok': False,
                'code': 'USER_NOT_FOUND',
            }, 404)

    @route('/me/created-events', methods=['GET'])
    @route('/<string:user_id>/created-events', methods=['GET'])
    def get_created_events(self, user_id=None):

        try:
            cursor = self.get_cursor(request)
            if not user_id:
                auth_user = self.get_auth_user()
            else:
                auth_user = User.get_user(user_id)
            events = auth_user.get_created_events(cursor)
            events_total = auth_user.get_created_events_count()
            return response({
                "ok": True,
                "events": serializers.event_summary_schema.dump(events, many=True),
                "events_total": events_total,
                "metadata": {
                    "cursor": {
                        "before": cursor.before,
                        "after": cursor.after,
                        "limit": cursor.limit
                    }
                }
            })
        except exceptions.user.UserNotFound:
            return response({
                'ok': False,
                'code': 'USER_NOT_FOUND'
            }, 404)

    @route('/me/attending-events', methods=['GET'])
    @route('/<string:user_id>/attending-events', methods=['GET'])
    def get_attending_events(self, user_id=None):
        try:
            cursor = self.get_cursor(request)
            if not user_id:
                auth_user = self.get_auth_user()
            else:
                auth_user = User.get_user(user_id)
            events = auth_user.get_attending_events(cursor)
            events_total = auth_user.get_attending_events_count()
            return response({
                "ok": True,
                "events": serializers.event_summary_schema.dump(events, many=True),
                "events_count": events_total,
                "metadata": {
                    "cursor": {
                        "before": cursor.before,
                        "after": cursor.after,
                        "limit": cursor.limit
                    }
                }
            })
        except exceptions.user.UserNotFound:
            return response({
                'ok': False,
                'code': 'USER_NOT_FOUND'
            }, 404)

    @route('/me/bookmarked-events', methods=['GET'])
    @route('/<string:user_id>/bookmarked-events', methods=['GET'])
    def get_bookmarked_events(self, user_id=None):
        try:
            cursor = self.get_cursor(request)
            if not user_id:
                auth_user = self.get_auth_user()
            else:
                auth_user = User.get_user(user_id)
            events = auth_user.get_bookmarked_events(cursor)
            events_total = auth_user.get_bookmarked_events_count()
            return response({
                "ok": True,
                "events": serializers.event_summary_schema.dump(events, many=True),
                "events_count": events_total,
                "metadata": {
                    "cursor": {
                        "before": cursor.before,
                        "after": cursor.after,
                        "limit": cursor.limit
                    }
                }
            })
        except exceptions.UserNotFound:
            return response({
                'ok': False,
                'code': 'USER_NOT_FOUND'
            }, 404)

    @route('/me/followings', methods=['GET'])
    @route('/<string:user_id>/followings', methods=['GET'])
    def get_my_followings(self, user_id=None):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            if not user_id:
                followings = auth_user.get_followings()
                followings_count = auth_user.get_total_followings_count()
            else:
                followings = auth_user.get_followings()
                followings_count = auth_user.get_total_followings_count()
            return response({
                'ok': True,
                'followings': serializers.user_summary_schema.dump(followings, many=True),
                'followings_count': followings_count
            })
        except exceptions.user.UserNotFound:
            response({
                'ok': False,
                'code': 'USER_NOT_FOUND'
            }, 400)

    @route('/me/followers', methods=['GET'])
    @route('/<string:user_id>/followers', methods=['GET'])
    def get_my_followers(self, user_id=None):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            if not user_id:
                followers = auth_user.get_followers()
                followers_count = auth_user.get_total_followers_count()
            else:
                followers = auth_user.get_followers()
                followers_count = auth_user.get_total_followers_count()
            return response({
                'ok': True,
                'followers': serializers.user_summary_schema.dump(followers, many=True),
                'followers_count': followers_count
            })
        except exceptions.UserNotFound:
            return response({
                'ok': False,
                'code': 'USER_NOT_FOUND'
            }, 400)

    @route('/<string:user_id>/follow', methods=['POST'])
    def follow_user(self, user_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            user = User.get_user(user_id)
            user.add_follower(auth_user)
        except exceptions.AlreadyFollowingUser:
            return response({
                "ok": False,
                "message": "already following user"
            }, 400)
        except exceptions.user.UserNotFound:
            return response({
                'ok': False,
                'code': 'USER_NOT_FOUND'
            }, 400)
        return response(serializers.user_summary_schema.dump(auth_user))

    @route('/<string:user_id>/unfollow', methods=['DELETE'])
    def unfollow_user(self, user_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            user = User.get_user(user_id)
            user.remove_follower(auth_user)
            return response(serializers.user_summary_schema.dump(auth_user))
        except exceptions.user.UserNotFound:
            return response({
                'ok': False,
                'code': 'USER_NOT_FOUND'
            }, 400)

    @route('/me/payment-details', methods=['GET'])
    def get_my_payment_details(self):
        auth_user = self.get_auth_user()
        payment_details = auth_user.get_payment_details()
        return response(serializers.user_payment_details_schema.dump(payment_details, many=True))

    @route('/notifications', methods=['GET'])
    def get_user_notifications(self):
        auth_user = Authenticator.get_instance().get_auth_user()
        cursor = self.get_cursor(request)

        if 't' in request.args:
            if request.args['t'] in ['read', 'unread', 'all']:
                type = request.args['t']
                if type == 'read':
                    notifications = Notification.get_read_notifications(auth_user, cursor)
                elif type == 'unread':
                    notifications = Notification.get_unread_notifications(auth_user, cursor)
                elif type == 'all':
                    notifications = Notification.get_all_notifications(auth_user, cursor)
        else:
            notifications = Notification.get_all_notifications(auth_user)

        return response({
            "ok": True,
            "notifications": serializers.notification_schema.dump(notifications, many=True),
            "all_notifications_count": Notification.get_total_notifications(auth_user),
            "unread_notifications_count": Notification.get_total_unread_notifications(auth_user),
            "read_notifications_count": Notification.get_total_read_notifications(auth_user),
            "metadata": {
                "cursor": {
                    "before": cursor.before,
                    "after": cursor.after,
                    "limit": cursor.limit
                }
            }
        })

    @route('/me/payment-details', methods=['POST'])
    def add_payment_details(self):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            data = request.get_json()

            if 'payment_type' not in data:
                return response({
                    'ok': False,
                    'code': 'PAYMENT_DATA_INVALID'
                }, 400)
            payment_type = data['payment_type']
            if not PaymentTypes.accepts_payment_of_type(payment_type):
                return response({
                    'ok': False,
                    'code': 'UNAVAILABLE_PAYMENT_OPTION'
                }, 400)

            if PaymentTypes.CARD == payment_type:
                serializers.card_payment_info_schema.load(data)
                card_expiration_date = data['card_expiration_date']
                card_expiration_date = utils.parse_card_expiration_date(card_expiration_date)
                card_info = CardPaymentInfo(card_name=data['card_name'],
                                            card_type=data['card_type'],
                                            card_number=data['card_number'],
                                            card_expiration_date=card_expiration_date,
                                            card_cv=data['card_cv']
                                            )
                if not auth_user.has_card_payment():
                    auth_user.add_card_payment_info(card_info)
                elif auth_user.has_card_payment():
                    payment_info = auth_user.get_card_payment_info()
                    payment_info.update_card_payment(card_info)
            elif PaymentTypes.MOBILE_MONEY == payment_type:
                serializers.mobile_payment_info_schema.load(data)
                mobile_info = MobilePaymentInfo(mobile_network=data['mobile_network'], mobile_number=data['mobile_number'])
                if not auth_user.has_mobile_money_payment():
                    auth_user.add_mobile_payment_info(mobile_info)
                elif auth_user.has_mobile_money_payment():
                    payment_info = auth_user.get_mobile_payment_info()
                    payment_info.update_mobile_payment(mobile_info)
            user_payment_infos = auth_user.get_payment_details()
            return response({
                'ok': True,
                'payment_info': serializers.user_payment_details_schema.dump(user_payment_infos, many=True)
            })
        except ValidationError as e:
            return response({
                'ok': False,
                'code': 'REQUEST_VALIDATION_ERROR',
                'message': e.messages
            }, 400)
        except exceptions.payments.InvalidCardExpirationDateFmt:
            return response({
                'ok': False,
                'code': 'INVALID_CARD_EXPIRATON_DATE_FORMAT'
            }, 400)
