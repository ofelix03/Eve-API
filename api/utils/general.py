import bcrypt
from datetime import date, datetime
from marshmallow.fields import Field
import base64


from api.repositories.exceptions import InvalidCardExpirationDateFmt

APP_NAME = "Eve"

APP_BASE_URL = "http://127.0.0.1:8000"
CLIENT_BASE_URL = "http://127.0.0.1:4300"

MEDIA_DIR = '/home/felix/Desktop/EVE_MEDIA'

ENCRYPTION_KEY = 'r4e7SulNhTkt0T_QWtB0tHQ6OJYUSHC93alsL7s8ALI'
AUTH_USER_ID = '097d05c3-de53-4de4-9efa-ef71cd64cb11'

GOOGLE_CLOUD_API_KEY = 'AIzaSyCmBIPWntZIbDdKfEf7IZ_u3cjY79Eh2MU'

CLOUDINARY_URL = "https://res.cloudinary.com/ofelix03/image/upload/v1586382968/"
CLOUDINARY_ASSETS_URL = CLOUDINARY_URL + 'asssets/'


FEMALE_PROFILE_IMAGE = CLOUDINARY_ASSETS_URL + 'female-profile.svg'
MALE_PROFILE_IMAGE = CLOUDINARY_ASSETS_URL + 'male-profile.svg'
NO_IMAGE = CLOUDINARY_ASSETS_URL + 'no-image.jpg'



HASH_SALT = bcrypt.gensalt()


def hash_password(password):
    return bcrypt.hashpw(password.encode(), salt=HASH_SALT).decode()


def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def parse_card_expiration_date(mdate=''):
    # Converts date of format "YY/MM" to a datetime object
    try:
        if '/' in mdate:
            [y, m] = mdate.split('/')
            y = str(date.today().year)[:2] + y
            return date(int(y), int(m), int(1))
        else:
            raise InvalidCardExpirationDateFmt()
    except Exception:
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




def founder_url_explode(founder_str):
    founder_str = founder_str.replace('<', '===')
    founder_str = founder_str.replace('>', '===')
    founder_url_list = list(filter(lambda l: len(l) > 0, map(lambda l: l.strip(), founder_str.split("==="))))
    if len(founder_url_list) > 1:
        return founder_url_list[0], founder_url_list[1]
    return founder_url_list[0], None


def generate_slug(url):
    return slugify(url, to_lower=True)