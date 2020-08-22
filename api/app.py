from flask import Flask
from flask_cors import CORS

from api.views.event_category import EventCategoryView
from api.views.images import ImagesView
from api.views.event import EventView
from api.views.ticket import TicketsView
from api.views.user import UserView
from api.views.event_attendees import EventAttendeesView
from api.views.social_media import SocialMediaView
from api.views.jobs import JobView
from api.views.brands import BrandView
from api.views.brand_category import BrandCategoryView
from api.views.me import MeView
from api.views.countries import CountryView
from api.views.general import GeneralView
from api.views.places_autocomplete import PlacesAutocompleteView
from api.models.event import db
from api import db_config
from api.utils import general as general_utils

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


def create_app():
    app = Flask(__name__)
    app.config.from_object(db_config)
    db.init_app(app)
    return app


app = create_app()

cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.config['UPLOAD_FOLDER'] = general_utils.MEDIA_DIR

ImagesView.register(app, route_base='images')
EventCategoryView.register(app, route_base='event-categories')
EventView.register(app, route_base='events')
TicketsView.register(app, route_base='tickets')
UserView.register(app, route_base='users')
EventAttendeesView.register(app, route_base='attendees')
SocialMediaView.register(app, route_base='social-media')
JobView.register(app, route_base='jobs')
BrandView.register(app, route_base='brands')
BrandCategoryView.register(app, route_base='brand-categories')
MeView.register(app, route_base='me')
CountryView.register(app, route_base='countries')
GeneralView.register(app, route_base='general')
PlacesAutocompleteView.register(app, route_base='places_autocomplete')
