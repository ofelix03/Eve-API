from . import *
from marshmallow import ValidationError
from api.views.auth_base import AuthBaseView, BaseView
from api.repositories import exceptions
from api.auth.authenticator import Authenticator, data_encryptor
from api.models.event import User, UserLoginSession, Country, Notification
from api.models.domain.user_payment_info import CardPaymentInfo, MobilePaymentInfo, PaymentTypes
from api import serializers

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
        try:
            auth_user = Authenticator.get_instance().get_auth_user()

            data = request.get_json()
            profile = User.get_user(auth_user.id)
            print("updating user", profile)

            if 'name' in data and data['name'] != profile.name:
                auth_user.name = data['name']

            if 'email' in data and data['email'] != profile.email:
                profile.email = data['email']

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

            if 'country_code' in data:
                pass

            if 'image' in data:
                profile.image = data['image']

            profile.update()
            return response(serializers.user_schema.dump(profile))
        except exceptions.NotAuthUser:
            return self.not_auth_response()

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
            country_id = data['country_id']

            if not Country.has_country(country_id):
                return response({
                    "ok": False,
                    "errors": {
                        "message": "Country not found"
                    }
                }, 401)
            country = Country.get_country(country_id)
            user = User.create(name=name, email=email, password=password, country=country, gender=gender,
                               phone_number=phone_number)
            return response(serializers.user_schema.dump(user))
        except exceptions.UserAlreadyExists:
            return response({
                "ok": False,
                "errors": {
                    "message": "A user already exists with the same email"
                }
            }, 401)
        except ValidationError as e:
            return response({
                "ok": False,
                "errors": e.messages
            }, 401)

    @route('/logout', methods=['POST'])
    def logout_user(self):
        user = Authenticator.get_instance().get_auth_user_without_auth_check()
        print("user##", user)
        if user:
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
                    "ok": False,
                    "errors": {
                        "message": "Login failed. Check email and password"
                    }
                }, 401)

            user = User.get_user_by_email(email)

            if not utils.check_password(password, user.password):
                return response({
                    "ok": False,
                    "errors": {
                        "message": "Login failed. Check email and password"
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
                "ok": True,
                "session_token": session_token,
                "session_user": session_user
            })
        except ValidationError:
            return response({
                "ok": False,
                "errors": {
                    "message": "Login failed. Check email and password"
                }
            }, 401)

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
        except exceptions.PasswordConfirmationMismatch:
            return response({
                'ok': False,
                'code': 'USER_PASSWORD_CONFIRMATION_MISMATCH'
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('/me/new-password-request', methods=['GET'])
    def reset_password_send_link_notification(self):
        pass

    @route('/<string:user_id>')
    def get_user(self, user_id):
        try:
            user = User.get_user(user_id)
            return response(serializers.user_summary_schema.dump(user))
        except exceptions.UserNotFound:
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
        except exceptions.NotAuthUser:
            return self.not_auth_response()
        except exceptions.UserNotFound:
            return response({
                'ok': False,
                'code': 'USER_NOT_FOUND',
            }, 404)

    @route('/me/created-events', methods=['GET'])
    @route('/<string:user_id>/created-events', methods=['GET'])
    def get_created_events(self, user_id=None):
        try:
            cursor = self.get_cursor(request)
            auth_user = self.get_auth_user_without_auth_check()
            if user_id:
                user = User.get_user((user_id))
            else:
                user = self.get_auth_user_without_auth_check()

            is_published = True if 'is_published' in request.args else False
            is_not_published = True if 'not_published' in request.args else False

            events = user.get_created_events(cursor, is_published, is_not_published)
            events_total = user.get_created_events_count(is_published, is_not_published)

            if auth_user:
                events = serializers.event_summary_schema.dump(events, many=True)
            else:
                events = serializers.event_summary_anon_schema.dump(events, many=True)

            return response({
                "ok": True,
                "events": events,
                "events_total": events_total,
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

    @route('/me/attending-events', methods=['GET'])
    @route('/<string:user_id>/attending-events', methods=['GET'])
    def get_attending_events(self, user_id=None):
        try:
            cursor = self.get_cursor(request)
            auth_user = self.get_auth_user_without_auth_check()

            if user_id:
                user = User.get_user(user_id)
            else:
                user = auth_user

            events = user.get_attending_events(cursor)
            events_total = user.get_attending_events_count()

            if auth_user:
                events = serializers.event_summary_schema.dump(events, many=True)
            else:
                events = serializers.event_summary_anon_schema.dump(events, many=True)

            return response({
                "ok": True,
                "events": events,
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

    @route('/me/bookmarked-events', methods=['GET'])
    @route('/<string:user_id>/bookmarked-events', methods=['GET'])
    def get_bookmarked_events(self, user_id=None):
        try:
            cursor = self.get_cursor(request)
            auth_user = self.get_auth_user_without_auth_check()

            if user_id:
                user = User.get_user(user_id)
            else:
                user = auth_user

            events = user.get_bookmarked_events(cursor)
            events_total = user.get_bookmarked_events_count()

            if auth_user:
                events = serializers.event_summary_schema.dump(events, many=True)
            else:
                events = serializers.event_summary_anon_schema.dump(events, many=True)
            return response({
                "ok": True,
                "events": events,
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

            if user_id:
                user = User.get_user(user_id)
                followings = user.get_followings()
                followings_count = user.get_total_followings_count()
            else:
                followings = auth_user.get_followings()
                followings_count = auth_user.get_total_followings_count()
            return response({
                'ok': True,
                'followings': serializers.user_summary_schema.dump(followings, many=True),
                'followings_count': followings_count
            })
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('/me/followers', methods=['GET'])
    @route('/<string:user_id>/followers', methods=['GET'])
    def get_my_followers(self, user_id=None):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()

            if user_id:
                user = User.get_user(user_id)
                followers = user.get_followers()
                followers_count = user.get_total_followers_count()
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
            return response(serializers.user_summary_schema.dump(auth_user))
        except exceptions.AlreadyFollowingUser:
            return response({
                "ok": False,
                "message": "already following user"
            }, 400)
        except exceptions.UserNotFound:
            return response({
                'ok': False,
                'code': 'USER_NOT_FOUND'
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('/<string:user_id>/unfollow', methods=['DELETE'])
    def unfollow_user(self, user_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            user = User.get_user(user_id)
            user.remove_follower(auth_user)
            return response(serializers.user_summary_schema.dump(auth_user))
        except exceptions.UserNotFound:
            return response({
                'ok': False,
                'code': 'USER_NOT_FOUND'
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('/me/payment-details', methods=['GET'])
    def get_my_payment_details(self):
        try:
            auth_user = self.get_auth_user()
            payment_details = auth_user.get_payment_details()
            return response(serializers.user_payment_details_schema.dump(payment_details, many=True))
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('/notifications', methods=['GET'])
    def get_user_notifications(self):
        try:
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
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('/notifications/unread_count', methods=['GET'])
    def get_user_notifcation_counts(self):
        auth_user = Authenticator.get_instance().get_auth_user_without_auth_check()
        notification_count = Notification.get_total_unread_notifications(auth_user) if auth_user else 0
        return response({
            "ok": True,
            "unread_notifications_count": notification_count
        })

    @route('/notifications/mark_as_read', methods=['PUT'])
    def mark_notifications_as_read(self):
        try:
            notification_ids = request.get_json()['notification_ids']
            for notification in Notification.get_notifications(notification_ids):
                notification.mark_as_read()
            return response({
                "ok": True
            })
        except exceptions.NotAuthUser:
            return self.not_auth_response()

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
                mobile_info = MobilePaymentInfo(mobile_network=data['mobile_network'],
                                                mobile_number=data['mobile_number'])
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
        except exceptions.InvalidCardExpirationDateFmt:
            return response({
                'ok': False,
                'code': 'INVALID_CARD_EXPIRATON_DATE_FORMAT',
                'message': 'Invalid card expiration date format. Require a format of [YY/MM]'
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('/me/payment-accounts/<string:account_id>', methods=['DELETE'])
    def remove_payment_account(self, account_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            auth_user.remove_payment_account(account_id)
            return response({
                'ok': True,
            })
        except exceptions.PaymentAccountDoesNotExist:
            return response({
                'ok': False,
                'code': "PAYMENT_ACCOUNT_NOT_FOUND"
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()
