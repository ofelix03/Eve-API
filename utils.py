
import bcrypt
from datetime import date, datetime
from marshmallow.fields import Field
import base64

from api.exceptions.payments import InvalidCardExpirationDateFmt

ENCRYPTION_KEY = 'r4e7SulNhTkt0T_QWtB0tHQ6OJYUSHC93alsL7s8ALI'
AUTH_USER_ID = '097d05c3-de53-4de4-9efa-ef71cd64cb11'

GOOGLE_CLOUD_API_KEY = 'AIzaSyCmBIPWntZIbDdKfEf7IZ_u3cjY79Eh2MU'


class TicketDiscountOperator(object):
    EQUAL_TO = '='
    GREATER_THAN = '>'
    GREATER_THAN_OR_EQUAL_TO = '>='
    BETWEEN = '<->'
    operators = [EQUAL_TO, GREATER_THAN, GREATER_THAN_OR_EQUAL_TO, BETWEEN]

    @classmethod
    def has_operator(cls, op):
        return op in cls.operators


class TicketDiscountType:
    EARLY_PURCHASE = "1f8ed81a-f652-44c3-8d16-3b75be10fe2a"
    NUMBER_OF_PURCHASES = "d4925ff6-6779-4204-be9d-63613c652c77"


HASH_SALT = bcrypt.gensalt()


def hash_password(password):
    return bcrypt.hashpw(password.encode(), salt=HASH_SALT).decode()


def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def parse_card_expiration_date(mdate=''):
    # Converts date of format "YY/MM" to a datetime object
    if '/' in mdate:
        [y, m, d] = mdate.split('/') + [1]
        y = str(date.today().year)[:2] + y
        return date(int(y), int(m), int(d))
    raise InvalidCardExpirationDateFmt()


class CardExpirationDateField(Field):

    def _serialize(self, value, attr, obj, **kwargs):
        if isinstance(value, datetime) or isinstance(value, date):
            return value.strftime('%y/%m')
        return None

    def _deserialize(self, value, attr, data, **kwargs):
        return parse_card_expiration_date(value)


def gen_po_ref(po_id):
    """
    Takes a purchase order ID and base32 encode it.
    Taket the first 4 characters as the PO ref
    :param po_id:
    :return:
    """
    return 'PO' + base64.b32encode(po_id.encode())[:4].decode()


def gen_image_filename(uid):
    return base64.b32encode(uid.encode())[:7].decode()


MEDIA_DIR = '/home/felix/Desktop/EVE_MEDIA'
