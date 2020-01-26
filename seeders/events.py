from datetime import timedelta
import random
import factory
from factory.faker import Faker
from api.models import event as model
from api.db_config import Session
import uuid


session = Session()

EVENT_CATEGORIES = ['Photography', 'Technology', 'Art & Music', 'Movies', 'Education', 'Politics', 'Agriculture', 'Startup', 'Business']
IMAGE_URL = ['https://placeimg.com/500/300/people', 'https://source.unsplash.com/random/500*300?event']
HUMAN_IMAGE_URL = 'https://placeimg.com/500/300/people?'

EVENT_TICKET_TYPES = ['Early Bird', 'Single', 'Couple', 'Discounted']
CONTACT_TYPE = ['email', 'mobile']
CONTACT_VALUES = ['ofelix03@gmail.com', '0542180582', 'paulotoo@gmail.com', '054217829', 'soemone@hotmail.com', '0242310913']
EVENT_PRICE = [20.5, 100.00, 50, 320, 550]
EVENT_TICKET_QTY = [200, 500, 420, 380, 900]


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = model.User
        sqlalchemy_session = session   # the SQLAlchemy session object

    name = Faker('name')
    email = factory.LazyAttribute(lambda obj: obj.name.split(" ")[0].lower() + "@gmail.com")
    password = '123'
    country = 'Ghana'


users = UserFactory.build_batch(20)


class EventMediaFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = model.EventMedia
        sqlalchemy_session = session   # the SQLAlchemy session object

    name = Faker('word')
    source_url = factory.Iterator(IMAGE_URL)
    media_type = 'image/jpeg'
    is_cover_image = False


class JobFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = model.Job
        sqlalchemy_session = session

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = Faker('job')

jobs = JobFactory.build_batch(30)
session.add_all(jobs)
session.commit()

class EventContactInfoFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = model.EventContactInfo
        sqlalchemy_session = session   # the SQLAlchemy session object

    type = factory.Iterator(CONTACT_TYPE)  # type: email | mobile
    info = factory.Iterator(CONTACT_VALUES)  # info: 0242310913 | ofelix03@gmail.com


class TicketTypeFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = model.EventTicketType
        sqlalchemy_session = session   # the SQLAlchemy session object

    name = factory.Iterator(EVENT_TICKET_TYPES)
    price = factory.Iterator(EVENT_PRICE)
    total_qty = factory.Iterator(EVENT_TICKET_QTY)


class EventCategoryFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = model.EventCategory
        sqlalchemy_session = session   # the SQLAlchemy session object

    name = factory.Iterator(EVENT_CATEGORIES)
    image = factory.Iterator(IMAGE_URL)
    id = factory.LazyAttribute(lambda obj: str(uuid.uuid4()))

event_categories = EventCategoryFactory.build_batch(9)
session.add_all(event_categories)
session.commit()


class EventOrganizerFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = model.EventOrganizer
        sqlalchemy_session = session

    # name = Faker('name')
    user = users[random.randint(0, 19)]
    # id = factory.LazyAttribute(lambda obj: str(uuid.uuid4()))
    # image = HUMAN_IMAGE_URL + str(random.random())

class SocialMediaFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = model.SocialMedia

    id = factory.LazyAttribute(lambda obj: str(uuid.uuid4()))
    name = factory.Iterator(['twitter', 'facebook', 'instagram', 'reddit'])

social_media = SocialMediaFactory.build_batch(4)
session.add_all(social_media)
session.commit()


class EventSpeakerFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = model.EventSpeaker
        sqlalchemy_session = session

    # id = factory.LazyAttribute(lambda obj: str(uuid.uuid4()))
    name = Faker('name')
    social_account = social_media[random.randint(0, 3)]
    social_account_handle = factory.LazyAttribute(lambda obj: '@' + obj.name.split(" ")[0].lower())

class EventBookmarkFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = model.EventBookmark
        sqlalchemy_session = session

    id = factory.LazyAttribute(lambda obj: str(uuid.uuid4()))
    user = factory.Iterator(users)


class EventRecommendationFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = model.EventRecommendation
        sqlalchemy_session = session

    recommended_to = factory.Iterator(users)
    recommended_by = factory.Iterator(users)


class EventFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = model.Event
        sqlalchemy_session = session

    name = Faker('name')
    description = Faker('text')
    venue = Faker('address')
    start_datetime = Faker('date_time_this_year', before_now=False, after_now=True)
    end_datetime = factory.LazyAttribute(lambda obj: obj.start_datetime + timedelta(days=random.randint(1, 5)))


class EventReviewMediaFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = model.EventReviewMedia
        sqlalchemy_session = session

    type = 'image/jpeg'
    url = factory.Iterator(IMAGE_URL)


class EventReviewFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = model.EventReview
        sqlalchemy_session = session


    content = Faker('text')
    published_at = Faker('date_time_this_year', before_now=False, after_now=True)
    upvotes = random.randint(0, 500)
    downvotes = random.randint(0, 100)
    author = users[random.randint(0, 19)]
    # media = EventReviewMediaFactory.build_batch(random.randint(0, 5))



def build_relational_data(event):
    event.organizers = EventOrganizerFactory.build_batch(random.randint(1, 5))
    event.speakers = EventSpeakerFactory.build_batch(random.randint(1, 8))
    event.user = users[random.randint(0, 19)]
    event.contact_info = EventContactInfoFactory.build_batch(random.randint(1, 3))
    event.bookmarks = EventBookmarkFactory.build_batch(random.randint(0, 3))
    event.recommendations = EventRecommendationFactory.build_batch(random.randint(1, 10))
    event.media = EventMediaFactory.build_batch(random.randint(1, 18))
    event.category = event_categories[random.randint(0, 8)]
    # event.reviews = EventReviewFactory.build_batch(random.randint(0, 5))

    return event


def seed():
    events = EventFactory.build_batch(100)
    events = map(build_relational_data, events)
    session.add_all(events)
    session.commit()



if __name__ == '__main__':
    seed()



