from marshmallow import Schema, fields
from api.auth.authenticator import Authenticator
from api.utils.general import CardExpirationDateField


class CountrySerializer(Schema):
    id = fields.String(required=True, dump_only=True)
    name = fields.String(required=True)
    code = fields.String(required=True)
    calling_code = fields.String(required=True)


class CreateUserSchema(Schema):
    name = fields.String(required=True)
    email = fields.String(required=True)
    country_id = fields.String(required=True)
    gender = fields.String(required=True)
    phone_number = fields.String(required=True)
    password = fields.String(required=True)


class UserSchema(Schema):
    id = fields.String(required=True)
    name = fields.String()
    image = fields.String(required=True)
    email = fields.Email()
    country = fields.Nested(CountrySerializer, required=True)
    gender = fields.String()
    phone_number = fields.String()
    is_ghost = fields.Boolean()


class UserSchemaFull(UserSchema):
    created_events_count = fields.Function(lambda user: user.get_created_events_count())
    attending_events_count = fields.Function(lambda user: user.get_attending_events_count())
    bookmarked_events_count = fields.Function(lambda user: user.get_bookmarked_events_count())
    followers_count = fields.Integer()


class LoggedInUserSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    email = fields.String(required=True)
    image = fields.String(required=True, default='https://source.unsplash.com/1600x900/?human')
    is_ghost = fields.Boolean()


class UserSummarySchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    email = fields.String(required=True)
    image = fields.String(required=True)
    is_ghost = fields.Boolean()
    is_follower = fields.Function(lambda user: Authenticator.get_instance().get_auth_user_without_auth_check().
                                  am_following_user(user) if Authenticator.get_instance().
                                  get_auth_user_without_auth_check() else False)


class UserSummaryAnonSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    email = fields.String(required=True)
    image = fields.String(required=True)
    is_ghost = fields.Boolean(default=False)
    is_follower = fields.Boolean(default=False)


class ChangeUserPasswordSerliazer(Schema):
    new_password = fields.String(required=True)
    new_password_confirmation = fields.String(required=True)


class UserPaymentDetailsSchema(Schema):
    id = fields.String()
    card_name = fields.String()
    card_type= fields.String()
    card_number = fields.String()
    card_expiration_date = CardExpirationDateField()
    card_cv = fields.String()
    payment_type = fields.String()
    mobile_network = fields.String()
    mobile_number = fields.String()


class CardPaymentInfoSchema(Schema):
    card_name = fields.String(required=True)
    card_type = fields.String(required=True)
    card_number = fields.String(required=True)
    card_cv = fields.Integer(required=True)
    card_expiration_date = fields.String(required=True)
    payment_type = fields.String()


class MobilePaymentInfoSchema(Schema):
    mobile_network = fields.String(required=True)
    mobile_number = fields.String(required=True)
    is_default_payment = fields.Boolean()
    payment_type = fields.String()


class LoginUserSchema(Schema):
    email = fields.String(required=True)
    password = fields.String(required=True)


class RequestPasswordChangeSchema(Schema):
    email = fields.String(required=True)


class ChangePasswordWithCodeSchema(Schema):
    code = fields.String(required=True)
    password = fields.String(required=True)
    password_confirmation = fields.String(required=True)