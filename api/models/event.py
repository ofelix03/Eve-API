import uuid, random
from enum import Enum
import copy
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload, relation
from sqlalchemy import func, or_, and_, text
from sqlalchemy.orm import relationship
from sqlalchemy import Boolean, Column
from sqlalchemy import cast, Numeric
from sqlalchemy.orm import load_only

from api import utils
from api.models.event_periods import EventPeriods
from api.models.pagination_cursor import PaginationCursor
from api.models.domain.user_payment_info import PaymentTypes
from api.exceptions import payments as payment_exceptions
from api.repositories import exceptions

from api.models.domain.user_payment_info import DiscountTypes
from api.utils import TicketDiscountOperator, TicketDiscountType, generate_slug


from flask_sqlalchemy import SQLAlchemy


DEFAULT_IMAGE = "https://res.cloudinary.com/ofelix03/image/upload/v1585692212/asssets/no-image.jpg"

CASCADE = 'CASCADE'

db = SQLAlchemy()


class Media(db.Model):
    __tablename__ = 'media'

    id = db.Column(db.String, primary_key=True)
    filename = db.Column(db.String)
    source_url = db.Column(db.String)
    format = db.Column(db.String)
    public_id = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.now())

    def __init__(self, source_url=None, filename=None, format=None, public_id=None):
        self.id = str(uuid.uuid4())
        self.filename = filename
        self.source_url = source_url
        self.format = format
        self.public_id = public_id
        self.created_at = datetime.now()

    @classmethod
    def create(cls, source_url=None, filename=None, format=None, public_id=None):
        media = cls(source_url=source_url, format=format, public_id=public_id, filename=filename)
        db.session.add(media)
        return media


class Country(db.Model):
    __tablename__ = 'countries'

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    code = db.Column(db.String)
    calling_code = db.Column(db.String)

    def __init__(self, name=None, code=None, calling_code=None):
        self.id = str(uuid.uuid4())
        if name:
            self.name = name

        if code:
            self.code = code

        if calling_code:
            self.calling_code = calling_code

    @classmethod
    def create(cls, name, code, calling_code):
        country = cls(name, code, calling_code)
        db.session.add(country)
        db.session.commit()

    @classmethod
    def has_country(cls, country_id):
        count = db.session.query(Country).filter(Country.id == country_id).count()
        return bool(count)

    @classmethod
    def has_country_by_name(cls, name):
        return db.session.query(db.session.query(Country).filter(Country.name == name).exists()).scalar()

    @classmethod
    def get_countries(cls):
        countries = db.session.query(Country).all()
        return countries

    @classmethod
    def get_country(cls, country_id):
        return db.session.query(Country).filter(Country.id == country_id).one()

    @classmethod
    def get_country_by_code(cls, code):
        return db.session.query(Country).filter(Country.code == code).first()

    def update(self):
        self.db.session.commit()

    @classmethod
    def remove_country(cls, country_id):
        if not cls.has_country(country_id):
            raise exceptions.CountryNotFound()
        db.session.query(Country).filter(Country.id == country_id).delete()

    @classmethod
    def find_countries_by_searchterm(cls, searchterm):
        if searchterm is None:
            return []
        searchterm = '%' + searchterm + '%'
        countries = db.session.query(Country) \
            .filter(Country.name.ilike(searchterm)) \
            .all()
        return countries


class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.String, primary_key=True, default=uuid.uuid4())
    name = db.Column(db.String, index=True)

    def __init__(self, name):
        self.id = str(uuid.uuid4())
        self.name = name

    @classmethod
    def create(cls, name):
        job = cls(name)
        db.session.add(job)
        db.session.commit()

    @classmethod
    def has_job(cls, job_id):
        return db.session.query(db.session.query(Job).filter(Job.id == job_id).exists()).scalar()

    @classmethod
    def get_job(cls, job_id):
        if not cls.has_job(job_id):
            raise exceptions.JobNotFound()
        return db.session.query(Job).filter(Job.id == job_id).first()

    @classmethod
    def get_jobs(cls):
        return db.session.query(Job).all()

    @classmethod
    def find_job_by_searchterm(self, searchterm=None):
        if searchterm is None:
            return []
        searchterm = '%' + searchterm + '%'
        jobs = db.session.query(Job).filter(Job.name.ilike(searchterm)).all()
        return jobs


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String, primary_key=True)
    image = db.Column(db.String)
    name = db.Column(db.String)
    email = db.Column(db.String)
    password = db.Column(db.String)
    country = relationship('Country')
    country_id = db.Column(db.String, db.ForeignKey('countries.id'))
    gender = db.Column(db.String)
    phone_number = db.Column(db.String)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    is_ghost = db.Column(db.Boolean, default=False)
    events = relationship('Event', backref='users')
    bookmarks = relationship('EventBookmark', backref='users')
    followers = relationship('UserFollower', foreign_keys='UserFollower.user_id', backref='users')
    payment_info = relationship('UserPaymentDetails', backref='users')
    login_history = relationship('UserLoginHistory', backref='users')
    login_session = relationship('UserLoginSession', backref='users')

    def __init__(self, image=None, name=None, email=None, password=None, country=None, country_code=None, gender=None,
                 phone_number=None, is_ghost=None):

        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()

        if image:
            self.image = image
        elif gender in ('male', 'm'):
            self.image = utils.MALE_PROFILE_IMAGE
        elif gender in ('female', 'f'):
            self.image = utils.FEMALE_PROFILE_IMAGE

        if name:
            self.name = name

        if email:
            self.email = email

        if password:
            self.password = password

        if country:
            self.country = country

        if country_code:
            self.country_code = country_code

        if gender:
            self.gender = gender

        if phone_number:
            self.phone_number = phone_number

        if is_ghost:
            self.is_ghost = is_ghost

    @classmethod
    def create(cls, name=None, image=None, email=None, password=None, country=None, country_code=None, gender=None,
               phone_number=None, is_ghost=False):

        if cls.has_email(email):
            raise exceptions.UserAlreadyExists()

        user = cls(name=name, image=image, email=email, password=password, country=country, country_code=country_code,
                   gender=gender, phone_number=phone_number, is_ghost=is_ghost)
        db.session.add(user)
        db.session.commit()
        return user

    @classmethod
    def create_ghost_user(cls, email):
        user = cls(email=email, is_ghost=True)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def has_user(user_id):
        return db.session.query(db.session.query(User).filter(User.id == user_id).exists()).scalar()

    def change_password(self, new_password, new_password_confirmation):
        if new_password != new_password_confirmation:
            raise exceptions.user.PasswordConfirmationMismatch()
        self.password = utils.hash_password(new_password)
        db.session.commit()

    def has_password(self, password):
        return utils.check_password(self.password, password)

    @classmethod
    def get_user(cls, user_id):
        # if not cls.has_user(user_id):
        #     raise exceptions.user.UserNotFound()
        return db.session.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_users():
        return db.session.query(User).filter(User.is_ghost == False).all()

    @classmethod
    def get_user_by_email(cls, email):
        if not cls.has_email(email):
            raise exceptions.user.UserNotFound()
        return db.session.query(User).filter(User.email == email).first()

    @staticmethod
    def has_email(email):
        return db.session.query(db.session.query(User).filter(User.email == email).exists()).scalar()

    @staticmethod
    def has_email_n_password(email, password):
        return db.session.query(
            db.session.query(User).filter(User.email == email).filter(User.password == password).exists()).scalar()

    def has_login_session(self):
        return db.session.query(
            db.session.query(UserLoginSession).filter(UserLoginSession.user_id == self.id).exists()).scalar()

    def get_login_session(self):
        return db.session.query(UserLoginSession).filter(UserLoginSession.user_id == self.id).first()

    def remove_login_session(self):
        db.session.query(UserLoginSession).filter(UserLoginSession.user_id == self.id).delete()
        db.session.commit()

    def am_following_user(self, user):
        if user:
            return db.session.query(db.session.query(UserFollower.id)
                                    .filter(UserFollower.user_id == user.id)
                                    .filter(UserFollower.follower_id == self.id).exists()
                                    ).scalar()
        return False

    def is_following_me(self, user):
        return db.session.query(is_following_me=db.session.query(UserFollower.id)
                                .filter(UserFollower.user_id == self.id)
                                .filter(UserFollower.follower_id == user.id).exists()
                                ).scalar()

    def is_me(self, user):
        return self.id == user.id

    def remove_follower(self, user):
        db.session.query(UserFollower) \
            .filter(UserFollower.user_id == self.id) \
            .filter(UserFollower.follower_id == user.id) \
            .delete()
        db.session.commit()

    def add_follower(self, user):
        if self.has_follower(user):
            raise exceptions.AlreadyFollowingUser()
        self.followers += [UserFollower(follower=user, user=self)]
        db.session.commit()

    def remove_follower(self, user):
        if not self.has_follower():
            raise exceptions.NotFollowingUser()
        db.session.query(UserFollower) \
            .filter(UserFollower.follower_id == user.id) \
            .filter(UserFollower.user_id == self.id) \
            .delete()
        db.session.commit()

    def has_follower(self, user):
        return db.session.query(db.session.query(UserFollower)
                                .filter(UserFollower.follower_id == user.id)
                                .filter(UserFollower.user_id == self.id).exists()
                                ).scalar()

    def has_purchased_tickets_for_event(self, event):
        return db.session.query(db.session.query(EventTicket).filter(EventTicket.owner_id == self.id)
                                .filter(EventTicket.event_id == event.id)
                                .exists()).scalar()

    def has_gifted_tickets_for_event(self, event):
        return db.session.query(db.session.query(EventTicketTypeAssignment)
                                .filter(EventTicketTypeAssignment.event_id == event.id)
                                .filter(EventTicketTypeAssignment.assigned_to_user_id == self.id)
                                .exists()).scalar()

    def has_tickets_for_event(self, event):
        return self.has_purchased_tickets_for_event(event) or self.has_gifted_tickets_for_event(event)

    def get_attending_events(self, cursor=None):
        event_ids_query = db.session.query(EventTicket.event_id.label("event_id")) \
            .distinct(EventTicket.event_id) \
            .filter(or_(EventTicket.owner_id == self.id,
                        and_(EventTicket.assignment.any(EventTicketTypeAssignment.ticket_id == EventTicket.id),
                             EventTicket.assignment.any(EventTicketTypeAssignment.assigned_to_user_id == self.id))))

        query = db.session.query(Event).filter(Event.id.in_(event_ids_query))

        if cursor and cursor.after:
            query = query.filter(func.round(cast(func.extract('EPOCH', Event.created_at), Numeric), 3) < func.round(cursor.get_after_as_float(), 3))

        if cursor and cursor.before:
            query = query.filter(func.round(cast(func.extract('EPOCH', Event.created_at), Numeric), 3) > func.round(cursor.get_before_as_float(), 3))

        events = query.order_by(Event.created_at.desc()).limit(cursor.limit).all()

        if events:
            cursor.set_before(events[0].created_at)
            cursor.set_after(events[-1].created_at)
        else:
            cursor.set_before(None)
            cursor.set_after(None)

        return events

    def get_attending_events_count(self):
        events_count = db.session.query(EventTicket.event_id.label("event_id")) \
            .distinct(EventTicket.event_id) \
            .filter(or_(EventTicket.owner_id == self.id,
                        and_(EventTicket.assignment.any(EventTicketTypeAssignment.ticket_id == EventTicket.id)))) \
            .count()
        return events_count

    def get_created_events(self, cursor, is_published=True, is_not_published=True):

        query = db.session.query(Event) \
            .filter(Event.user_id == self.id)

        if is_published and not is_not_published:
            query = query.filter(Event.is_published==True)
        elif not is_published and is_not_published:
            query = query.filter(Event.is_published==False)

        if cursor and cursor.after:
            query = query.filter(func.round(cast(func.extract('EPOCH', Event.created_at), Numeric), 3)
                                 < func.round(cursor.get_after_as_float(), 3))

        if cursor and cursor.before:
            query = query.filter(func.round(cast(func.extract('EPOCH', Event.created_at), Numeric), 3)
                                 > func.round(cursor.get_before_as_float(), 3))

        events = query.order_by(Event.created_at.desc()).limit(cursor.limit).all()

        if events:
            cursor.set_before(events[0].created_at)
            cursor.set_after(events[-1].created_at)
        else:
            cursor.set_before(None)
            cursor.set_after(None)

        return events

    def get_created_events_count(self, is_published=True, is_not_published=True):
        query = db.session.query(Event) \
            .filter(Event.user_id == self.id)

        if is_published and not is_not_published:
            query = query.filter(Event.is_published==True)
        elif is_not_published and not is_published:
            query = query.filter(Event.is_published==False)
        return query.count()

    def get_bookmarked_events(self, cursor):
        query = db.session.query(EventBookmark) \
            .options(load_only('id', 'event_id', 'created_at')) \
            .filter(EventBookmark.user_id == self.id)

        if cursor and cursor.after:
            query = query.filter(func.round(cast(func.extract('EPOCH', EventBookmark.created_at), Numeric), 3) < func.round(
                cursor.get_after_as_float(), 3))

        if cursor and cursor.before:
            query = query.filter(func.round(cast(func.extract('EPOCH', Event.created_at), Numeric), 3) > func.round(
                cursor.get_before_as_float(), 3))

        bookmarks = query.order_by(EventBookmark.created_at.desc()).limit(cursor.limit).all()

        if len(bookmarks):
            cursor.set_before(bookmarks[0].created_at)
            cursor.set_after(bookmarks[-1].created_at)
        else:
            cursor.set_before(None)
            cursor.set_after(None)

        events = db.session.query(Event).filter(Event.id.in_(list(map(lambda bookmark: bookmark.event_id, bookmarks)))).all()
        return events

    def get_bookmarked_events_count(self):
        return db.session.query(EventBookmark) \
            .filter(EventBookmark.user_id == self.id) \
            .count()

    @classmethod
    def find_users_by_searchterm(cls, searchterm=None):
        if searchterm is None:
            return []
        searchterm = '%' + searchterm + '%'
        users = db.session.query(User) \
            .filter(User.is_ghost == False) \
            .filter(or_(User.name.ilike(searchterm), User.email.ilike(searchterm))) \
            .all()
        return users

    @classmethod
    def get_user_full(self, user_id):
        if not self.has_user(user_id):
            raise exceptions.user.UserNotFound()

        return db.session.query(User).options(
            joinedload(User.events),
            joinedload(User.bookmarks)
        ).filter(User.id == user_id).first()

    def update(self):
        self.updated_at = datetime.now()
        db.session.add(self)
        db.session.commit()

    def has_followers(self):
        return db.session.query(db.session.query(UserFollower).filter(UserFollower.user_id == self).exists()).scalar()

    def get_followers(self):
        followers = db.session.query(User).filter(User.id.in_(
            self.db.session.query(UserFollower.follower_id).filter(UserFollower.user_id == self.id).subquery()
        )).all()
        return followers

    def get_followings(self):
        followings = db.session.query(User).filter(User.id.in_(
            self.db.session.query(UserFollower.user_id).filter(UserFollower.follower_id == self.id).subquery()
        )).all()

        return followings

    def get_total_followings_count(self):
        return self.db.session.query(UserFollower.user_id).filter(UserFollower.follower_id == self.id).count()

    def get_total_followers_count(self, user_id):
        return self.db.session.query(UserFollower.follower_id).filter(UserFollower.user_id == self.id).count()

    def has_payment_details(self):
        return db.session.query(
            self.db.session.query(UserPaymentDetails).filter(UserPaymentDetails.user_id == self.id).exists()).scalar()

    def has_card_payment(self):
        return UserPaymentDetails.has_card_payment(self)

    def has_mobile_money_payment(self):
        return UserPaymentDetails.has_mobile_money_payment(self)

    def get_payment_details(self):
        return db.session.query(UserPaymentDetails).filter(UserPaymentDetails.user_id == self.id).all()

    def get_card_payment_info(self):
        return UserPaymentDetails.get_card_payment(self)

    def get_mobile_payment_info(self):
        return UserPaymentDetails.get_mobile_payment(self)

    def add_mobile_payment_info(self, mobile_payment_info=None, is_default_payment=False):
        if self.has_mobile_money_payment():
            raise payment_exceptions.UserAlreadyHasPaymentSetup()
        return UserPaymentDetails.create_mobile_payment(self, mobile_payment_info, is_default_payment)

    def add_card_payment_info(self, card_payment_info=None, is_default_payment=False):
        if self.has_card_payment():
            raise payment_exceptions.UserAlreadyHasPaymentSetup()
        return UserPaymentDetails.create_card_payment(self, card_payment_info, is_default_payment)

    def has_payment_account(self, account_id):
        return UserPaymentDetails.has_payment_account(account_id)

    def remove_payment_account(self, account_id):
        print("###1")
        if not self.has_payment_account(account_id):
            raise exceptions.PaymentAccountDoesNotExist()
        UserPaymentDetails.remove_payment_account(account_id)


class UserLoginSession(db.Model):
    __tablename__ = 'user_login_sessions'

    id = db.Column(db.String, primary_key=True)
    session_token = db.Column(db.String, index=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    user = relationship('User')
    created_at = db.Column(db.DateTime, default=datetime.now())

    def __init__(self, session_token=None, user=None, user_id=None):
        self.id = str(uuid.uuid4())
        if session_token:
            self.session_token = session_token

        if user:
            self.user = user

        if user_id:
            self.user_id = user_id


class UserLoginHistory(db.Model):
    __tablename__ = 'user_login_history'

    id = db.Column(db.String, primary_key=True)
    login_at = db.Column(db.DateTime, default=datetime.now())
    logout_at = db.Column(db.DateTime)
    user_agent = db.Column(db.String)
    ip_address = db.Column(db.String)
    user_location = db.Column(db.String)
    user_id = db.Column(db.String, db.ForeignKey('users.id'))
    user = relationship('User')

    def __init__(self, user_agent=None, ip_address=None, user_location=None, user_id=None, user=None):
        self.id = str(uuid.uuid4())

        if user_agent:
            self.user_agent = user_agent

        if ip_address:
            self.ip_address = ip_address

        if user_location:
            self.user_location = user_location

        if user_id:
            self.user_id = user_id

        if user:
            self.user = user


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.String, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.Text)
    description = db.Column(db.Text)
    venue_type = db.Column(db.String, index=True)
    venue = db.Column(db.String)
    start_datetime = db.Column(db.DateTime)
    end_datetime = db.Column(db.DateTime)
    cover_image = db.Column(db.String)
    organizers = relationship('EventOrganizer', backref='events')
    speakers = relationship('EventSpeaker', backref='events')
    media = relationship('EventMedia', backref='events')
    contact_info = relationship('EventContactInfo', backref='events')
    ticket_types = relationship('EventTicketType', backref='events')
    category = relationship('EventCategory')
    ticket_sales = relationship('EventTicketSaleOrder', backref='events')
    bookmarks = relationship('EventBookmark', backref='events')
    user = relationship('User')
    recommendations = relationship('EventRecommendation', backref='events')
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete=CASCADE, onupdate=CASCADE))
    category_id = db.Column(db.String, db.ForeignKey('event_categories.id', ondelete=CASCADE, onupdate=CASCADE))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    is_shareable_during_event = db.Column(db.Boolean, default=True)
    is_shareable_after_event = db.Column(db.Boolean, default=True)
    reviews = relationship('EventReview', backref='events')
    sponsors = relationship('EventSponsor', backref='events')
    is_published = db.Column(db.Boolean, index=True)

    def __init__(self, name=None, description=None, venue=None, start_datetime=None, end_datetime=None,
                 cover_image=None, is_published=False):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.venue = venue
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.cover_image = cover_image
        self.is_published = is_published
        self.created_at = datetime.now()

    @classmethod
    def has_event(cls, event_id):
        return db.session.query(db.session.query(Event).filter(Event.id == event_id).exists()).scalar()

    @staticmethod
    def add_event(event):
        event = db.session.merge(event)
        db.session.add(event)
        db.session.commit()
        return Event.get_event(event.id)

    @classmethod
    def delete_event(cls, event_id):
        if not cls.has_event(event_id):
            raise exceptions.EventNotFound()
        db.session.query(Event).filter(Event.id == event_id).delete()
        db.session.commit()

    @classmethod
    def get_event_only(cls, event_id):
        if not cls.has_event(event_id):
            raise exceptions.EventNotFound()
        return db.session.query(Event).filter(Event.id == event_id).first()

    def user_has_tickets(self, user):
        return user.has_tickets_for_event(self)
        # return EventTicket.user_has_tickets_for_event(self, user)

    def _update_attendee_pagination_cursor(self, cursor):
        rs = db.engine.execute(self._attendees_view_query_created_at(cursor)).fetchall()
        if rs:
            cursor.set_before(rs[0][0])
            cursor.set_after(rs[-1][0])
        else:
            cursor.set_before(None)
            cursor.set_after(None)

    def _attendees_view_query_user_id(self, cursor):
        query_text = """
            SELECT user_id FROM event_attendees_view
            WHERE event_id = :event_id
            AND CASE WHEN COALESCE(:cursor_after,0)!=0 THEN extract('epoch' FROM created_at) > :cursor_after ELSE TRUE END
            AND CASE WHEN  COALESCE(:cursor_before,0)!=0 THEN extract('epoch' FROM created_at) < :cursor_before ELSE TRUE END
            ORDER BY created_at ASC LIMIT :limit
        """
        return text(query_text).bindparams(
            event_id=self.id,
            limit=cursor.limit,
            cursor_after=cursor.get_after_as_float(),
            cursor_before=cursor.get_before_as_float()
        )

    def _attendees_view_query_created_at(self, cursor):
        query_text = """
               SELECT created_at FROM event_attendees_view
               WHERE event_id = :event_id
               AND CASE WHEN COALESCE(:cursor_after,0)!=0 THEN extract('epoch' FROM created_at) > :cursor_after ELSE TRUE END
               AND CASE WHEN  COALESCE(:cursor_before,0)!=0 THEN extract('epoch' FROM created_at) < :cursor_before ELSE TRUE END
               ORDER BY created_at ASC LIMIT :limit
           """
        return text(query_text).bindparams(
            event_id=self.id,
            limit=cursor.limit,
            cursor_after=cursor.get_after_as_float(),
            cursor_before=cursor.get_before_as_float()
        )

    def get_attendees(self, cursor=None):
        attendees = db.session.query(User).filter(User.id.in_(self._attendees_view_query_user_id(cursor))).all()
        self._update_attendee_pagination_cursor(cursor)
        return attendees

    def get_total_attendees(self):
        return db.session.query(User).filter(
            User.id.in_(self._attendees_view_query_user_id(cursor=PaginationCursor()))).count()

    def is_bookmarked_by(self, user):
        if not user:
            return False
        return db.session.query(db.session.query(EventBookmark)
                                .filter(EventBookmark.event_id == self.id)
                                .filter(EventBookmark.user_id == user.id).exists()
                                ).scalar()

    def bookmark(self, user):
        if EventBookmark.user_already_bookmarked_event(self, user):
            raise exceptions.BookmarkAlreadyExist()
        bookmark = EventBookmark.create(self, user)
        return bookmark

    def unbookmark(self, user):
        EventBookmark.delete_bookmark(self, user)

    @staticmethod
    def get_events_total(period=None, category=None, creator_id=None, is_published=True):
        query = db.session.query(Event)

        if is_published:
            query= query.filter(Event.is_published==True)

        if period and 'period' in period and 'value' in period:
            period_type = period['period']
            period_value = period['value']

            if period_type == EventPeriods.TODAY:
                query = query.filter(func.DATE(Event.start_datetime) == period_value)
            elif period_type == EventPeriods.TOMORROW:
                query = query.filter(func.DATE(Event.start_datetime) == period_value)
            elif period_type == EventPeriods.THIS_WEEK:
                start_date = period_value[0]
                end_date = period_value[1]
                query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))
            elif period_type == EventPeriods.THIS_MONTH:
                start_date = period_value[0]
                end_date = period_value[1]
                query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))
            elif period_type == EventPeriods.NEXT_MONTH:
                start_date = period_value[0]
                query = query.filter(func.DATE(Event.start_datetime) >= start_date)
            elif period_type == EventPeriods.THIS_YEAR:
                start_date = period_value[0]
                end_date = period_value[1]
                query = query.filter(func.TIMESTAMP(Event.start_datetime).between(start_date, end_date))

        if creator_id:
            query = query.filter(Event.user_id == creator_id)

        if category:
            query = query.filter(Event.category_id == category.id)

        return query.count()

    @staticmethod
    def has_more_events(period=None, category_id=None, creator_id=None, cursor=None, is_published=True):
        has_more_cursor = copy.copy(cursor)
        more_events = Event.get_events(period, category_id, creator_id, has_more_cursor, is_published)
        return len(more_events) > 0

    @staticmethod
    def get_events(period=None, category_id=None, creator_id=None, cursor=None, is_published=True):
        query = db.session.query(Event).options(
            joinedload(Event.recommendations),
            joinedload(Event.organizers),
            joinedload(Event.user),
            joinedload(Event.category),
            joinedload(Event.ticket_types),
            joinedload(Event.contact_info),
            joinedload(Event.speakers),
            joinedload(Event.media),
        )

        if is_published:
            query = query.filter(Event.is_published==True)

        if period and 'period' in period and 'value' in period:
            period_type = period['period']
            period_value = period['value']

            if period_type == EventPeriods.TODAY:
                query = query.filter(func.DATE(Event.start_datetime) == period_value)
            elif period_type == EventPeriods.TOMORROW:
                query = query.filter(func.DATE(Event.start_datetime) == period_value)
            elif period_type == EventPeriods.THIS_WEEK:
                start_date = period_value[0]
                end_date = period_value[1]
                query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))
            elif period_type == EventPeriods.THIS_MONTH:
                start_date = period_value[0]
                end_date = period_value[1]
                query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))
            elif period_type == EventPeriods.NEXT_MONTH:
                start_date = period_value[0]
                end_date = period_value[1]
                query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))
            elif period_type == EventPeriods.THIS_YEAR:
                start_date = period_value[0]
                end_date = period_value[1]
                query = query.filter(func.TIMESTAMP(Event.start_datetime).between(start_date, end_date))

        if creator_id:
            query = query.filter(Event.user_id == creator_id)

        if category_id:
            query = query.filter(Event.category_id == category_id)

        if cursor and cursor.after:
            query = query.filter(func.round(cast(func.extract('EPOCH', Event.created_at), Numeric), 3) < func.round(
                cursor.get_after_as_float(), 3))

        elif cursor and cursor.before:
            query = query.filter(func.round(cast(func.extract('EPOCH', Event.created_at), Numeric), 3) > func.round(
                cursor.get_before_as_float(), 3))

        events = query.order_by(Event.created_at.desc()).limit(cursor.limit).all()

        if events:
            cursor.set_before(events[0].created_at)
            cursor.set_after(events[-1].created_at)
            cursor.set_has_more(Event.has_more_events(period, category_id, creator_id, cursor, is_published))
        else:
            cursor.set_before(None)
            cursor.set_after(None)
            cursor.set_has_more(False)
        return events

    @staticmethod
    def has_more_events_summary(category=None, period=None, cursor=None, is_published=True):
        has_more_cursor = copy.copy(cursor)
        more_events = Event.get_events_summary(category, period, has_more_cursor, is_published)
        return len(more_events) > 0

    @staticmethod
    def get_events_summary(category=None, period=None, cursor=None, is_published=True):

        query = db.session.query(Event)

        if is_published:
            query = query.filter(Event.is_published==True)

        if period and 'period' in period and 'value' in period:
            period_type = period['period']
            period_value = period['value']

            if period_type == EventPeriods.TODAY:
                query = query.filter(func.DATE(Event.start_datetime) == period_value)
            elif period_type == EventPeriods.TOMORROW:
                query = query.filter(func.DATE(Event.start_datetime) == period_value)
            elif period_type == EventPeriods.THIS_WEEK:
                [start_date, end_date] = period_value
                query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))
            elif period_type == EventPeriods.THIS_MONTH:
                [start_date, end_date] = period_value
                query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))
            elif period_type == EventPeriods.NEXT_MONTH:
                [start_date, end_date] = period_value
                query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))
            elif period_type == EventPeriods.THIS_YEAR:
                [start_date, end_date] = period_value
                query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))

        if category:
            query = query.filter(Event.category_id == category.id)

        if cursor and cursor.after:
            query = query.filter(func.round(cast(func.extract('EPOCH', Event.created_at), Numeric), 3)
                                 < func.round(cursor.get_after_as_float(), 3))

        elif cursor and cursor.before:
            query = query.filter(func.round(cast(func.extract('EPOCH', Event.created_at), Numeric), 3)
                                 > func.round(cursor.get_before_as_float(), 3))

        events = query.order_by(Event.created_at.desc()).limit(cursor.limit).all()

        if events:
            cursor.set_before(events[0].created_at)
            cursor.set_after(events[-1].created_at)
            cursor.set_has_more(Event.has_more_events_summary(category, period, cursor, is_published))
        else:
            cursor.set_before(None)
            cursor.set_after(None)
            cursor.set_has_more(False)

        return events

    @staticmethod
    def get_event(event_id):
        return db.session.query(Event).options(
            joinedload(Event.recommendations),
            joinedload(Event.organizers),
            joinedload(Event.user),
            joinedload(Event.category),
            joinedload(Event.ticket_types),
            joinedload(Event.contact_info),
            joinedload(Event.speakers),
            joinedload(Event.media),
            joinedload(Event.ticket_types)
        ).filter(Event.id == event_id).first()

    def add_organizer(self, organizer):
        self.organizers += [organizer]
        db.session.commit()

    def add_organizers(self, organizers):
        self.organizers += organizers
        db.session.commit()

    def publish(self):
        self.is_published = True
        db.session.commit()

    def update_event(self, data=None):
        if data:
            self.update(data)
        db.session.commit()

    def has_organizer(self, user):
        return db.session.query(
            db.session.query(EventOrganizer).filter(EventOrganizer.user_id == user.id).exists()).scalar()

    def clear_organizers(self):
        db.session.query(EventOrganizer).filter(EventOrganizer.event_id == self.id).delete()
        db.session.commit()

    def clear_sponsors(self):
        db.session.query(EventSponsor).filter(EventSponsor.event_id == self.id).delete()
        db.session.commit()

    def clear_contact_infos(self):
        db.session.query(EventContactInfo).filter(EventContactInfo.event_id == self.id).delete()
        db.session.commit()

    def clear_categories(self):
        self.category_id = None
        db.session.commit()

    def update(self):
        db.session.add(self)
        db.session.commit()

    def has_speaker(self, speaker_id):
        return db.session.query(db.session.query(EventSpeaker)
                                .filter(EventSpeaker.event_id == self.id)
                                .filter(EventSpeaker.id == speaker_id)
                                .exists()
                                ).scalar()

    def add_speaker(self, speaker):
        self.speakers += [speaker]
        db.session.commit()

    def add_speakers(self, speakers):
        self.speakers += speakers
        db.session.commit()

    def remove_speaker(self, speaker_id):
        if not self.has_speaker(speaker_id):
            raise exceptions.EventSpeakerNotFound()
        db.session.query(EventSpeaker).filter(EventSpeaker.id == speaker_id).delete()
        db.session.commit()

    def get_speaker(self, speaker_id):
        if not self.has_speaker(speaker_id):
            raise exceptions.EventSpeakerNotFound()

        return db.session.query(EventSpeaker) \
            .options(joinedload(EventSpeaker.social_account), joinedload(EventSpeaker.profession)) \
            .filter(EventSpeaker.id == speaker_id) \
            .first()

    def get_speakers(self):
        return db.session.query(EventSpeaker).filter(EventSpeaker.event_id == self.id).all()

    def get_ticket_type_discount(self, ticket_type_id, discount_id):
        return db.session.query(EventTicketDiscount). \
            filter(EventTicketDiscount.id == discount_id). \
            filter(EventTicketDiscount.ticket_type_id == ticket_type_id) \
            .first()

    def get_ticket_type_discounts(self, ticket_type_id):
        if not EventTicketType.has_ticket_type(ticket_type_id):
            raise exceptions.TicketTypeNotFound()
        return db.session.query(EventTicketDiscount).filter(EventTicketDiscount.ticket_type_id == ticket_type_id).all()

    def remove_ticket_type_discount(self, ticket_type_id, discount_id):
        if not EventTicketType.has_ticket_type(ticket_type_id):
            raise exceptions.TicketTypeNotFound()
        db.session.query(EventTicketDiscount).filter(EventTicketDiscount.id == discount_id).delete()
        db.session.commit()

    def get_event_recommendations(self):
        return db.session.query(EventRecommendation) \
            .filter(EventRecommendation.event_id == self.id) \
            .all()

    def has_recommendation_for(self, recommended_by_id, search_term=None, recommended_to_id=None):
        query = db.session.query(EventRecommendation) \
            .filter(EventRecommendation.event_id == self.id)

        if search_term:
            query = query.filter(
                or_(EventRecommendation.email == search_term, EventRecommendation.phone_number == search_term))
        elif recommended_to_id:
            query = query.filter(EventRecommendation.recommended_to_id == recommended_to_id)
        else:
            raise Exception("A searchterm or recommend_to_id is required")

        return db.session.query(
            query.filter(EventRecommendation.recommended_by_id == recommended_by_id).exists()).scalar()

    def add_sponsor(self, sponsor):
        self.sponsors += [sponsor]
        db.session.commit()

    def remove_sponsor(self, event_id, sponsor_id):
        if not self.has_sponsor(sponsor_id):
            raise exceptions.EventSponsorNotFound()

        db.session.query(EventSponsor).filter(EventSponsor.id == sponsor_id).filter(
            EventSponsor.event_id == event_id).delete()

    def get_sponsors(self):
        return db.session.query(EventSponsor).filter(EventSponsor.event_id == self.id).all()

    def get_sponsor(self, sponsor_id):
        if not self.has_sponsor(sponsor_id):
            raise exceptions.EventSponsorNotFound()

        return db.session.query(EventSponsor).filter(EventSponsor.event_id == self.id).filter(
            EventSponsor.id == sponsor_id).first()

    def has_sponsor(self, sponsor_id=None):
        return db.session.query(db.session.query(EventSponsor).filter(EventSponsor.event_id == self.id).filter(
            EventSponsor.id == sponsor_id).exists()).scalar()

    def add_bookmark(self, event_id, bookmark):
        event = self.get_event(event_id)
        if not event:
            raise exceptions.EventNotFound()

        if self.event_bookmarked_by_user(event_id, bookmark.user.id):
            raise exceptions.BookmarkAlreadyExist()

        event.bookmarks += [bookmark]
        db.session.commit()

    def remove_bookmark(self, event_id, user_id):
        if not self.event_bookmarked_by_user(event_id, user_id):
            raise exceptions.BookmarkNotFound()
        db.session.query(EventBookmark).filter(EventBookmark.user_id == user_id).filter(
            EventBookmark.event_id == event_id).delete()
        db.session.commit()

    def event_bookmarked_by_user(self, event_id, user_id):
        event = self.get_event(event_id)
        if not event:
            raise exceptions.EventNotFound()
        count = db.session.query(EventBookmark).filter(EventBookmark.user_id == user_id).filter(
            EventBookmark.event_id == event_id).count()
        return bool(count)

    def has_bookmark(self, bookmark_id):
        return db.session.query(db.session.query(EventBookmark)
                                .filter(EventBookmark.id == bookmark_id)
                                .filter(EventBookmark.event_id == self.id)
                                .exists()).scalar()

    def get_bookmarks(self):
        return db.session.query(EventBookmark).filter(EventBookmark.event_id == self.id).all()

    def add_review(self, review):
        self.reviews.append(review)
        db.session.commit()

    def remove_review(self, review_id):
        db.session.query(EventReview) \
            .filter(EventReview.event_id == self.id) \
            .filter(EventReview.review_id == review_id) \
            .delete()

    def has_review(self, review_id):
        return db.session.query(db.session.query(EventReview) \
                                .filter(EventReview.id == review_id) \
                                .filter(EventReview.event_id == self.id) \
                                .exists()).scalar()

    def delete_review(self, review_id):
        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()
        db.session.query(EventReview).filter(EventReview.id == review_id).filter(
            EventReview.event_id == self.id).delete()
        db.session.commit()

    def get_total_event_reviews(self):
        return db.session.query(EventReview).filter(EventReview.event_id == self.id).count()

    def get_review_only(self, review_id):
        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()

        return db.session.query(EventReview) \
            .filter(EventReview.id == review_id) \
            .first()

    def get_review(self, review_id):
        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()

        return db.session.query(EventReview).options(
            joinedload(EventReview.author),
            joinedload(EventReview.media),
            joinedload(EventReview.upvotes),
            joinedload(EventReview.downvotes)
        ).filter(EventReview.id == review_id).first()

    def has_more_reviews(self, cursor):
        _cursor = copy.copy(cursor)
        more_reviews = self.get_reviews(_cursor)
        print("has_more_reviews##", more_reviews)
        return len(more_reviews) > 0

    def get_reviews(self, cursor):
        query = db.session.query(EventReview).options(
            joinedload(EventReview.author),
            joinedload(EventReview.media),
            joinedload(EventReview.upvotes),
            joinedload(EventReview.downvotes),
            joinedload(EventReview.comments),
            joinedload(EventReview.event),
        ).filter(EventReview.event_id == self.id)

        if cursor and cursor.after:
            query = query.filter(
                func.round(cast(func.extract('EPOCH', EventReview.created_at), Numeric), 3) < func.round(
                    cursor.get_after_as_float(), 3))

        elif cursor and cursor.before:
            query = query.filter(
                func.round(cast(func.extract('EPOCH', EventReview.created_at), Numeric), 3) > func.round(
                    cursor.get_before_as_float(), 3))

        reviews = query.order_by(EventReview.created_at.desc()).limit(cursor.limit).all()

        if reviews:
            cursor.set_before(reviews[0].created_at)
            cursor.set_after(reviews[-1].created_at)
            cursor.set_has_more(self.has_more_reviews(cursor))
        else:
            cursor.set_before(None)
            cursor.set_after(None)
            cursor.set_has_more(False)

        return reviews

    @staticmethod
    def search_for_events(searchterm=None, category=None, period=None, country=None, cursor=None, is_published=True):
        # @todo use a more advance db.Text search tool
        query = db.session.query(Event).filter(Event.is_published==is_published).filter(Event.name.ilike('%' + searchterm + '%'))

        if category and category != 'all':
            query = query.filter(Event.category_id == category.id)

        if period and period != 'any':
            period_value = EventPeriods.get_date(period)['value']

            if period == EventPeriods.TODAY:
                query = query.filter(func.DATE(Event.start_datetime) == period_value)
            elif period == EventPeriods.TOMORROW:
                query = query.filter(func.DATE(Event.start_datetime) == period_value)
            elif period == EventPeriods.THIS_WEEK:
                [start_date, end_date] = period_value
                query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))
            elif period == EventPeriods.THIS_MONTH:
                [start_date, end_date] = period_value
                query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))
            elif period == EventPeriods.NEXT_MONTH:
                start_date = period_value[0]
                query = query.filter(func.DATE(Event.start_datetime) >= start_date)
            elif period == EventPeriods.THIS_YEAR:
                [start_date, end_date] = period_value
                query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))
            elif period == EventPeriods.NEXT_YEAR:
                [start_date, end_date] = period_value
                query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))

        if country:
            query = query.filter(Event.name.ilike('%' + country + '%'))

        if cursor and cursor.after:
            query = query.filter(func.round(cast(func.extract('EPOCH', Event.created_at), Numeric), 3)
                                 < func.round( cursor.get_after_as_float(), 3))

        elif cursor and cursor.before:
            query = query.filter(func.round(cast(func.extract('EPOCH', Event.created_at), Numeric), 3)
                                 > func.round(cursor.get_before_as_float(), 3))

        if cursor and cursor.limit:
            query = query.order_by(Event.created_at.desc()).limit(cursor.limit)

        events = query.all()

        if events:
            cursor.set_before(events[0].created_at)
            cursor.set_after(events[-1].created_at)
        else:
            cursor.set_before(None)
            cursor.set_after(None)

        return events

    def search_for_events_total(searchterm=None, category=None, period=None, country=None):
        # @todo use a more advance db.Text search tool
        query = db.session.query(Event).filter(Event.name.ilike('%' + searchterm + '%'))
        if category and category != 'all':
            query = query.filter(Event.category_id == category.id)

        if period and period != 'any':
            period_value = EventPeriods.get_date(period)['value']

            if period == EventPeriods.TODAY:
                query = query.filter(func.DATE(Event.start_datetime) == period_value)
            elif period == EventPeriods.TOMORROW:
                query = query.filter(func.DATE(Event.start_datetime) == period_value)
            elif period == EventPeriods.THIS_WEEK:
                start_date = period_value[0]
                end_date = period_value[1]
                query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))
            elif period == EventPeriods.THIS_MONTH:
                start_date = period_value[0]
                end_date = period_value[1]
                query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))
            elif period == EventPeriods.NEXT_MONTH:
                start_date = period_value[0]
                query = query.filter(func.DATE(Event.start_datetime) >= start_date)
            elif period == EventPeriods.THIS_YEAR:
                start_date = period_value[0]
                end_date = period_value[1]
                query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))
            elif period == EventPeriods.NEXT_YEAR:
                start_date = period_value[0]
                end_date = period_value[1]
                query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))

        return query.count()

    def has_media_file(self, file_id):
        return db.session.query(db.session.query(EventMedia)
                                .filter(EventMedia.id == file_id)
                                .filter(EventMedia.event_id == self.id)
                                .exists()).scalar()

    def get_media_file(self, file_id):
        if not self.has_media_file(file_id):
            raise exceptions.MediaNotFound()
        return db.session.query(EventMedia).filter(EventMedia.id == file_id).filter(
            EventMedia.event_id == self.id).first()

    def set_as_poster(self, file):
        file.poster = True
        self.cover_image = file.source_url
        db.session.add(self)
        db.session.add(file)
        db.session.commit()
        q = """UPDATE event_media SET poster = False WHERE id != :mediaId and event_id=:eventId"""
        db.engine.execute(text(q).bindparams(mediaId=file.id, eventId=self.id))
        # q = """UPDATE event_media SET is_poster = TRUE WHERE id = :mediaId and event_id=:eventId"""
        # db.engine.execute(text(q).bindparams(mediaId=file.id, eventId=self.id))
        db.session.commit()

    def get_poster(self):
        image = db.session.query(EventMedia).filter(EventMedia.event_id == self.id).filter(
            EventMedia.poster == True).first()
        return image.source_url if image  else utils.NO_IMAGE


class EventOrganizer(db.Model):
    __tablename__ = 'event_organizers'

    id = db.Column(db.String, primary_key=True, default=uuid.uuid4)
    event = relationship(Event)
    event_id = db.Column(db.String, db.ForeignKey('events.id', ondelete='CASCADE', onupdate='CASCADE'))
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete=CASCADE, onupdate=CASCADE))
    user = relationship('User')

    def __init__(self, user=None):
        self.user = user


class EventMedia(db.Model):
    __tablename__ = 'event_media'

    id = db.Column(db.String, primary_key=True, default=uuid.uuid4)
    filename = db.Column(db.String)
    source_url = db.Column(db.String)
    media_type = db.Column(db.String)
    poster = Column(Boolean, default=False)
    event = relationship(Event)
    event_id = db.Column(db.String, db.ForeignKey('events.id', ondelete='CASCADE', onupdate='CASCADE'))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    public_id = db.Column(db.String)

    def __init__(self, source_url=None, format=None, event=None, is_poster=False, public_id=None):
        self.id = str(uuid.uuid4())
        self.filename = utils.gen_image_filename(self.id)
        self.source_url = source_url
        self.format = format
        self.event = event
        self.is_poster = is_poster
        self.public_id = public_id
        self.created_at = datetime.now()

    @classmethod
    def create(cls, event=None, source_url=None, format=None, is_poster=False, public_id=None):
        media = cls(source_url=source_url, format=format, event=event, is_poster=is_poster, public_id=public_id)
        db.session.add(media)
        return media

    def add_source_url(self, url):
        self.source_url = url
        db.session.commit()

    def add_format(self, format):
        self.format = format

    def add_event(self, event):
        self.event = event
        db.session.commit()

    def is_poster(self, is_poster):
        self.is_poster = is_poster
        db.session.commit()

    def add_public_id(self, public_id):
        self.public_id = public_id
        db.session.commit()

    def delete(self):
        db.session.query(EventMedia).filter(EventMedia.id == self.id).delete()
        db.session.commit()


class EventSpeaker(db.Model):
    __tablename__ = 'event_speakers'

    id = db.Column(db.String, primary_key=True, default=str(uuid.uuid4()))
    name = db.Column(db.String)
    profession = relationship('Job')
    social_account = relationship('SocialMedia')
    social_account_handle = db.Column(db.String)
    social_media_id = db.Column(db.String, db.ForeignKey('social_media.id', ondelete=CASCADE, onupdate=CASCADE))
    event = relationship(Event)
    event_id = db.Column(db.String, db.ForeignKey('events.id', ondelete=CASCADE, onupdate=CASCADE))
    image = db.Column(db.String)
    profession_id = db.Column(db.String, db.ForeignKey('jobs.id', ondelete=CASCADE, onupdate=CASCADE))
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime)

    def __init__(self, name=None, social_account_id=None, social_account=None, social_account_handle=None,
                 profession_id=None, profession=None, event=None, event_id=None, image=utils.NO_IMAGE):
        self.id = str(uuid.uuid4())
        self.name = name
        self.social_media_id = social_account_id
        self.social_account = social_account
        self.social_account_handle = social_account_handle
        self.event_id = event_id
        self.event = event
        self.image = image
        self.profession_id = profession_id
        self.profession = profession

    def add_social_account(self, social_account):
        self.social_account = social_account
        db.session.commit()

    def add_profession(self, profession):
        self.profession = profession
        db.session.commit()

    def update(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_speaker(speaker_id):
        return db.session.query(EventSpeaker).filter(EventSpeaker.id == speaker_id).first()

    def update(self, name=None, social_account_id=None, social_account=None, social_account_handle=None,
               profession_id=None, profession=None, event=None, event_id=None, image=utils.NO_IMAGE):
        self.name = name
        self.social_media_id = social_account_id
        self.social_account = social_account
        self.social_account_handle = social_account_handle
        self.event_id = event_id
        self.event = event
        self.image = image
        self.profession_id = profession_id
        self.profession = profession


class EventContactInfo(db.Model):
    __tablename__ = 'event_contact_info'

    id = db.Column(db.String, primary_key=True, default=uuid.uuid4)
    type = db.Column(db.String)  # type: email | mobile
    info = db.Column(db.String)  # info: 0242310913 | ofelix03@gmail.com
    event = relationship(Event)
    event_id = db.Column(db.String, db.ForeignKey('events.id', ondelete='CASCADE', onupdate='CASCADE'))
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime)

    def __init__(self, type=None, info=None):
        self.type = type
        self.info = info


class EventCategory(db.Model):
    __tablename__ = 'event_categories'

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    image = db.Column(db.String)
    slug = db.Column(db.String)
    created_at = db.Column(db.DateTime)

    def __init__(self, name=None, image=utils.NO_IMAGE):
        self.id = str(uuid.uuid4())
        self.name = name
        self.image = image
        self.created = datetime.now()
        self.slug = generate_slug(name)

    @classmethod
    def create(cls, name=None, image=None):
        category = cls(name=name, image=image)
        db.session.add(category)
        db.session.commit()

    @classmethod
    def get_category(cls, category_id):
        if not cls.has_category(category_id):
            raise exceptions.EventCategoryNotFound()
        return db.session.query(EventCategory).filter(EventCategory.id == category_id).first()

    @staticmethod
    def has_category(category_id):
        return db.session.query(
            db.session.query(EventCategory).filter(EventCategory.id == category_id).exists()).scalar()

    def update(self):
        db.session.commit()

    @classmethod
    def delete_category(cls, category_id):
        if not cls.has_category(category_id):
            raise exceptions.EventCategoryNotFound()
        db.session.query(EventCategory).filter(EventCategory.id == category_id).delete()
        db.session.commit()

    @classmethod
    def get_categories(cls):
        return db.session.query(EventCategory).all()

    @classmethod
    def find_category(cls, category_name):
        return db.session.query(EventCategory).filter(EventCategory.name.ilike('%' + category_name + '%')).first()

    @classmethod
    def find_category_by_slug(cls, slug):
        return db.session.query(EventCategory).filter(EventCategory.slug.ilike('%' + slug + '%')).first()

    @classmethod
    def find_category_by_searchterm(cls, search_term):
        search_term = '%' + search_term + '%'
        categories = db.session.query(EventCategory).filter(EventCategory.name.ilike(search_term)).all()
        return categories


class EventBookmark(db.Model):
    __tablename__ = 'event_bookmarks'

    id = db.Column(db.String, primary_key=True)
    user = relationship('User')
    event = relationship('Event')
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'))
    event_id = db.Column(db.String, db.ForeignKey('events.id', ondelete='CASCADE', onupdate='CASCADE'))

    def __init__(self, event=None, user=None):
        self.id = str(uuid.uuid4())
        self.event = event
        self.user = user
        self.created_at = datetime.now()

    @staticmethod
    def user_already_bookmarked_event(event, user):
        return db.session.query(db.session.query(EventBookmark)
                                .filter(EventBookmark.event_id == event.id)
                                .filter(EventBookmark.user_id == user.id)
                                .exists()
                                ).scalar()

    @classmethod
    def create(cls, event, user):
        bookmark = cls(event, user)
        db.session.add(bookmark)
        db.session.commit()
        return bookmark

    @staticmethod
    def delete_bookmark(event, user):
        db.session.query(EventBookmark) \
            .filter(EventBookmark.event_id == event.id) \
            .filter(EventBookmark.user_id == user.id) \
            .delete()
        db.session.commit()

    def get_events_bookmarked_by_user(self, user_id):
        events = db.session.query(Event).filter(Event.bookmarks.any(EventBookmark.user_id == user_id)).all()
        return events

    def get_total_events_bookmarked_by_user(self, user_id):
        count = db.session.query(Event).filter(Event.bookmarks.any(EventBookmark.user_id == user_id)).count()
        return count


class EventSponsor(db.Model):
    __tablename__ = 'event_sponsors'

    id = db.Column(db.String, primary_key=True)
    brand_id = db.Column(db.String, db.ForeignKey('brands.id'))
    brand = relationship('Brand')
    created_at = db.Column(db.DateTime, default=datetime.now())
    event_id = db.Column(db.String, db.ForeignKey('events.id', ondelete=CASCADE, onupdate=CASCADE))
    event = relationship('Event')

    def __init__(self, brand=None):
        self.id = str(uuid.uuid4())

        if brand:
            self.brand = brand

    @classmethod
    def create(cls, brand):
        sponsor = cls(brand=brand)
        db.session.add(sponsor)
        db.session.commit()


class EventTicketType(db.Model):
    __tablename__ = 'event_ticket_types'

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    price = db.Column(db.Float)
    total_qty = db.Column(db.Float)
    remaining_qty = db.Column(db.Float)
    event = relationship(Event)
    event_id = db.Column(db.String, db.ForeignKey('events.id', ondelete='CASCADE', onupdate='CASCADE'))
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime)
    discounts = relationship('EventTicketDiscount', backref="event_ticket_types")

    def __init__(self, name=None, price=None, total_qty=None, event=None, discounts=[]):
        self.id = str(uuid.uuid4())
        self.name = name
        self.price = price
        self.total_qty = total_qty
        self.event = event
        self.discounts = discounts

    @classmethod
    def create(cls, name, price, total_qty, event, discount=[]):
        ticket_type = cls(name, price, total_qty, event, discount)
        db.session.add(ticket_type)
        db.session.commit()
        return ticket_type

    @classmethod
    def has_ticket_type(cls, ticket_type_id):
        return db.session.query(db.session.query(EventTicketType)
                                .filter(EventTicketType.id == ticket_type_id)
                                .exists()
                                ).scalar()

    @classmethod
    def get_ticket_type(cls, ticket_type_id):
        if not cls.has_ticket_type(ticket_type_id):
            raise exceptions.TicketTypeNotFound()

        return db.session.query(EventTicketType).filter(EventTicketType.id == ticket_type_id).first()

    def is_same(self, ticket_type):
        return ticket_type.id == self.id

    def get_available_qty(self):
        """
        Returns total_qty - (purchased_tickets + reserved_tickets)
        :return:
        """
        return self.total_qty - (self.get_purchased_qty() + self.get_reserved_qty())

    def get_unpurchased_qty(self):
        """
        Returns the  number of unpurchased tickets excluding reserved tickets
        :return:
        """
        purchased_qty = self.get_purchased_qty()
        return self.total_qty - purchased_qty

    def get_reserved_qty(self):
        result = db.session.query(func.coalesce(func.sum(EventTicketReservation.total_tickets_qty), 0)) \
            .filter(EventTicketReservation.expires_at > datetime.now()) \
            .filter(EventTicketReservation.reservation_lines.any(EventTicketReservationLine.ticket_type == self)) \
            .first()
        return result[0]

    def get_purchased_qty(self):
        qty = db.session.query(EventTicketSaleLine) \
            .filter(EventTicketSaleLine.ticket_type_id == self.id) \
            .count()
        return qty

    def set_remaining_qty(self, qty):
        self.remaining_qty = qty
        db.session.commit()

    @classmethod
    def get_ticket_type(cls, ticket_type_id):
        if not cls.has_ticket_type(ticket_type_id):
            raise exceptions.TicketTypeNotFound()
        return db.session.query(EventTicketType).filter(EventTicketType.id == ticket_type_id).first()

    @staticmethod
    def has_ticket_type(ticket_type_id):
        return db.session.query(EventTicketType).filter(EventTicketType.id == ticket_type_id).count()

    @staticmethod
    def delete_ticket_type(ticket_type_id):
        if not EventTicketType.has_ticket_type(ticket_type_id):
            raise exceptions.TicketNotFound()
        db.session.query(EventTicketType).filter(EventTicketType.id == ticket_type_id).delete()
        db.session.commit()

    def add_discount(self, discount):
        self.discounts.append(discount)
        db.session.add(self)
        db.session.commit()
        return discount

    def get_discounts(self):
        pdate = datetime.now()
        discounts = db.session.query(EventTicketDiscount) \
            .filter(EventTicketDiscount.ticket_type_id == self.id) \
            .filter(EventTicketDiscount.from_datetime <= pdate) \
            .filter(EventTicketDiscount.to_datetime >= pdate) \
            .all()

        print('mydiscounts##', discounts)
        return discounts


class EventTicketReservation(db.Model):
    __tablename__ = 'ticket_reservations'

    RESERVATION_LIMIT = 3  # Reservations limit is in minutes

    id = db.Column(db.String, primary_key=True)
    created_at = db.Column(db.DateTime, index=True)
    expires_at = db.Column(db.DateTime, index=True)
    reservation_by_id = db.Column(db.String, db.ForeignKey('users.id', onupdate=CASCADE, ondelete=CASCADE))
    reservation_by = relationship('User')
    reservation_lines = relationship('EventTicketReservationLine', backref='ticket_reservations')
    total_tickets_qty = db.Column(db.Float)

    def __init__(self, reservation_lines=[], reservation_by=None):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(minutes=self.RESERVATION_LIMIT)
        self.reservation_lines = reservation_lines
        self.reservation_by = reservation_by
        self.total_tickets_qty = sum(map(lambda line: line.ticket_qty, reservation_lines))

    @classmethod
    def has_reservation_from(cls, reservation_by=None):
        count = db.session.query(EventTicketReservation) \
            .filter(EventTicketReservation.reservation_by == reservation_by) \
            .filter(EventTicketReservation.expires_at > datetime.now()) \
            .count()
        return bool(count)

    @staticmethod
    def _check_insufficient_tickets_and_raise_exception(reservation_lines):
        """
        :param reservation_lines: [[ticket_type, ticket_qty], ...]
        :return:
        """
        for line in reservation_lines:
            ticket_type = line[0]
            ticket_qty = line[1]
            if ticket_type.get_available_qty() < ticket_qty:
                raise exceptions.InsufficientTicketsAvailable()

    @classmethod
    def create_reservation(cls, reservation_lines=[], reservation_by=None):
        """
        :param reservation_lines: [[ticket_type, ticket_qty], [ticket_type, ticket_qty], ...]
        :param reservation_by:
        :return:
        """
        cls._check_insufficient_tickets_and_raise_exception(reservation_lines)

        reservation_lines_obj = list(
            map(lambda line: EventTicketReservationLine(ticket_type=line[0], ticket_qty=line[1]), reservation_lines))
        if cls.has_reservation_from(reservation_by):
            raise exceptions.AlreadyHasTicketReservation(reservation=cls.get_reservation_from(reservation_by))
        reservation = cls(reservation_lines_obj, reservation_by)
        db.session.add(reservation)
        db.session.commit()
        return reservation

    @classmethod
    def get_reservation(cls, reservation_id):
        if not cls.reservation_exists(reservation_id):
            raise exceptions.TicketReservationNotFound()
        return db.session.query(EventTicketReservation) \
            .filter(EventTicketReservation.id == reservation_id) \
            .first()

    @staticmethod
    def reservation_exists(reservation_id):
        return db.session.query(EventTicketReservation) \
            .filter(EventTicketReservation.id == reservation_id) \
            .count()

    @staticmethod
    def get_reservation_from(reservation_by):
        return db.session.query(EventTicketReservation) \
            .filter(EventTicketReservation.reservation_by == reservation_by) \
            .filter(EventTicketReservation.expires_at > datetime.now()) \
            .first()

    @staticmethod
    def get_expired_reservations():
        return db.session.query(EventTicketReservation) \
            .filter(EventTicketReservation.expires_at < datetime.now()) \
            .all()

    @staticmethod
    def remove_reservations_from(reservations_by):
        """
        Removes both expired and unexpired user reservations
        :param reservations_by:
        :return:
        """
        db.session.query(EventTicketReservation) \
            .filter(EventTicketReservation.reservation_by == reservations_by) \
            .delete()
        db.session.commit()


class EventTicketReservationLine(db.Model):
    __tablename__ = 'ticket_reservation_lines'

    id = db.Column(db.String, primary_key=True)
    ticket_type_id = db.Column(db.String, db.ForeignKey('event_ticket_types.id', onupdate=CASCADE, ondelete=CASCADE),
                               index=True)
    ticket_type = relationship('EventTicketType')
    ticket_qty = db.Column(db.Float)
    reservation_id = db.Column(db.String, db.ForeignKey('ticket_reservations.id', onupdate=CASCADE, ondelete=CASCADE))
    reservation = relationship('EventTicketReservation')
    created_at = db.Column(db.DateTime)

    def __init__(self, ticket_type=None, ticket_qty=0, reservation=None):
        self.id = str(uuid.uuid4())
        self.ticket_type = ticket_type
        self.ticket_qty = ticket_qty
        self.reservation = reservation
        self.created_at = datetime.now()


class EventTicketDiscountType(db.Model):
    __tablename__ = 'event_ticket_discount_types'

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)

    def __init__(self, name=None):
        self.id = str(uuid.uuid4())
        self.name = name

    @staticmethod
    def has_discount_type(self, discount_type_id):
        return db.session.query(db.session.query(EventTicketDiscountType).filter(
            EventTicketDiscountType.id == discount_type_id).exists()).scalar()

    @staticmethod
    def create(name):
        discount_type = EventTicketDiscountType(name)
        db.session.add(discount_type)
        db.session.commit()
        return discount_type

    @classmethod
    def delete(cls, discount_type_id):
        if not cls.has_discount_type((discount_type_id)):
            raise exceptions.TicketTypeDiscountTypeNotFound()
        db.session.query(EventTicketDiscountType).filter(EventTicketDiscountType.id == discount_type_id).delete()
        db.session.commit()

    # @classmethod
    # def get_discount_type(cls, discount_type_id):
    #     if not cls.has_discount_type(discount_type_id):
    #         raise exceptions.TicketTypeDiscountTypeNotFound()
    #     return db.session.query(EventTicketDiscountType).filter(EventTicketDiscountType.id==discount_type_id).first()


class EventRecommendation(db.Model):
    __tablename__ = 'event_recommendations'

    id = db.Column(db.String, primary_key=True)
    event = relationship('Event')
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime)
    recommended_by_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'))
    recommended_to_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'))
    recommended_by = relationship('User', foreign_keys=[recommended_by_id])
    recommended_to = relationship('User', foreign_keys=[recommended_to_id])
    event_id = db.Column(db.String, db.ForeignKey('events.id', ondelete='CASCADE', onupdate='CASCADE'))
    is_not_user = db.Column(db.Boolean, default=False)
    phone_number = db.Column(db.String)
    email = db.Column(db.String)

    def __init__(self, event=None, recommended_by=None, recommended_to=None, phone_number=None, email=None):
        self.id = str(uuid.uuid4())
        if event and isinstance(event, Event):
            self.event = event

        if recommended_by and isinstance(recommended_by, User):
            self.recommended_by = recommended_by

        if recommended_to and isinstance(recommended_to, User):
            self.recommended_to = recommended_to

        if phone_number:
            self.phone_number = phone_number

        if email:
            self.email = email

        if (email or phone_number) and not recommended_to:
            self.is_not_user = True
        else:
            self.is_not_user = False


class AttendeeTicketGroupedByType:

    def __init__(self, type=None, assigned_tickets=None, unassigned_tickets=None):
        self.type = type or None
        self.assigned_tickets = assigned_tickets or []
        self.unassigned_tickets = unassigned_tickets or []
        self.total_qty = len(self.assigned_tickets) + len(self.unassigned_tickets)

    def add_assigned_ticket(self, ticket):
        self.assigned_tickets.append(ticket)
        self.total_qty = len(self.assigned_tickets) + len(self.unassigned_tickets)

    def add_assigned_tickets(self, tickets):
        self.assigned_tickets += tickets
        self.total_qty = len(self.assigned_tickets) + len(self.unassigned_tickets)

    def add_unassigned_ticket(self, ticket):
        self.unassigned_tickets.append(ticket)
        self.total_qty = len(self.assigned_tickets) + len(self.unassigned_tickets)

    def add_unassigned_tickets(self, tickets):
        self.unassigned_tickets += tickets
        self.total_qty = len(self.assigned_tickets) + len(self.unassigned_tickets)


class AttendeeTicket:

    def __init__(self, sale_line=None):
        self.id = sale_line.id
        self.ref = sale_line.ref
        self.event = sale_line.sale.event
        self.type = sale_line.ticket_type
        self.is_assigned = False
        self.owner = sale_line.sale.customer
        self.sale_line = sale_line
        if sale_line.is_assigned():
            self.is_assigned = True
            self.assigned_to = sale_line.assignment[0].assigned_to
        else:
            self.assigned_to = None

    def assign_to(self, user):
        if self.is_assigned:
            raise exceptions.TicketAlreadyAssigned()
        self.sale_line.assign_ticket(user)

    def unassign_from(self, user):
        if not self.is_assigned:
            raise exceptions.TicketNotAssigned()

        self.sale_line.unassign_ticket(user)

    def is_owned_by(self, owner):
        return self.owner.id == owner.id


class EventTicketSaleOrder(db.Model):
    __tablename__ = 'ticket_sales'

    id = db.Column(db.String, primary_key=True, default=uuid.uuid4)
    total_qty = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime)
    sale_lines = relationship('EventTicketSaleLine', backref='ticket_sales')
    customer_id = db.Column(db.String, db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'))
    customer = relationship(User)
    event_id = db.Column(db.String, db.ForeignKey('events.id', onupdate='CASCADE', ondelete='CASCADE'))
    event = relationship(Event)
    net_amount = db.Column(db.Float)
    ref = db.Column(db.String)

    def __init__(self, event_id=None, event=None, sale_lines=None, customer=None):
        self.id = str(uuid.uuid4())
        self.ref = utils.gen_po_ref(self.id)

        if event_id:
            self.event_id = event_id

        if event:
            self.event = event

        if sale_lines:
            self.sale_lines = sale_lines
            self.total_qty = len(sale_lines)

        if customer:
            self.customer = customer

    def generate_invoice(self):
        pass

    @classmethod
    def create_order(cls, customer, event, tickets):
        """
        :param customer:
        :param event:
        :param tickets: [{ticket_type: None, ticket_qty: 0}, ...}
        :return:
        """
        sale_order = cls(event=event, customer=customer)
        for ticket in tickets:
            ticket_type = ticket['ticket_type']
            ticket_qty = ticket['ticket_qty']
            if ticket_type.get_unpurchased_qty() < ticket_qty:
                raise exceptions.UnvailableTickets()
            sale_order.sale_lines.append(
                EventTicketSaleLine(sale_order=sale_order, ticket_type=ticket_type, ticket_qty=ticket_qty)
            )

        sale_amount = 0
        for order_line in sale_order.sale_lines:
            order_line.apply_discounts()
            order_line.create_tickets()
            sale_amount += order_line.net_amount

        sale_order.net_amount = sale_amount
        db.session.add(sale_order)
        db.session.commit()
        return sale_order

    def group_tickets_by_type(self):
        groups = []
        ticket_types = self.event.ticket_types
        attendee_tickets = []
        for line in self.sale_lines:
            attendee_tickets.append(AttendeeTicket(line))

        for ticket_type in ticket_types:
            assigned_tickets = list(
                filter(lambda ticket: ticket.is_assigned and ticket.type.is_same(ticket_type), attendee_tickets))
            unassigned_tickets = list(
                filter(lambda ticket: ticket.is_assigned is False and ticket.type.is_same(ticket_type),
                       attendee_tickets))
            groups.append(AttendeeTicketGroupedByType(type=ticket_type,
                                                      assigned_tickets=assigned_tickets,
                                                      unassigned_tickets=unassigned_tickets
                                                      )
                          )
        return groups


class EventTicketSaleLine(db.Model):
    __tablename__ = 'ticket_sale_lines'

    id = db.Column(db.String, primary_key=True, default=uuid.uuid4)
    sale_order = relationship(EventTicketSaleOrder)
    ticket_type = relationship(EventTicketType)
    ticket_qty = db.Column(db.Integer)
    sale_order_id = db.Column(db.String, db.ForeignKey('ticket_sales.id', onupdate='CASCADE', ondelete='CASCADE'))
    ticket_type_id = db.Column(db.String,
                               db.ForeignKey('event_ticket_types.id', onupdate='CASCADE', ondelete='CASCADE'))
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime)
    total_amount = db.Column(db.Float)
    discount_amount = db.Column(db.Float)
    net_amount = db.Column(db.Float)
    discounts = relationship('EventTicketSaleLineDiscount', backref='ticket_sale_lines')
    tickets = relationship('EventTicket', backref='ticket_sale_lines')

    def __init__(self, ticket_type, ticket_qty, sale_order):
        self.id = str(uuid.uuid4())
        self.sale_order = sale_order
        self.ticket_type = ticket_type
        self.ticket_qty = ticket_qty
        self.total_amount = ticket_qty * ticket_type.price

    @classmethod
    def create(cls, sale_order=None, ticket_type=None, ticket_qty=None):
        return cls(ticket_type, ticket_qty, sale_order)

    def create_tickets(self):
        for i in range(1, self.ticket_qty + 1):
            ticket = EventTicket(sale_line=self)
            self.tickets.append(ticket)

    def apply_discounts(self):
        discount_amount = 0
        for discount_type in self.ticket_type.discounts:
            if discount_type.compute_discount_amount_for_order_line(self) > 0:
                line_discount = EventTicketSaleLineDiscount(self, discount_type)
                self.discounts.append(line_discount)
                discount_amount += line_discount.amount
        self.discount_amount = discount_amount
        self.net_amount = self.total_amount - self.discount_amount


class EventTicketSaleLineDiscount(db.Model):
    __tablename__ = 'ticket_sale_lines_discounts'

    id = db.Column(db.String, primary_key=True)
    discount_type_id = db.Column(db.String,
                                 db.ForeignKey('event_ticket_discounts.id', onupdate=CASCADE, ondelete=CASCADE))
    discount_type = relationship('EventTicketDiscount')
    amount = db.Column(db.Float)
    order_line_id = db.Column(db.String, db.ForeignKey('ticket_sale_lines.id', onupdate=CASCADE, ondelete=CASCADE))
    order_line = relationship('EventTicketSaleLine')

    def __init__(self, order_line, discount_type):
        self.id = str(uuid.uuid4())
        self.discount_type = discount_type
        self.order_line = order_line
        self.amount = discount_type.compute_discount_amount_for_order_line(order_line)

    @classmethod
    def create(cls, order_line, discount_type):
        line_discount = cls(order_line, discount_type)
        db.session.add(line_discount)
        return line_discount


class EventTicketDiscount(db.Model):
    __tablename__ = 'event_ticket_discounts'

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    type = db.Column(db.String)
    ticket_type_id = db.Column(db.String, db.ForeignKey('event_ticket_types.id', ondelete=CASCADE, onupdate=CASCADE))
    ticket_type = relationship('EventTicketType')
    from_datetime = db.Column(db.DateTime)
    to_datetime = db.Column(db.DateTime)
    rate = db.Column(db.Float)
    fixed_amount = db.Column(db.Float)
    operator = db.Column(db.String)
    min_ticket_qty = db.Column(db.Float)
    max_ticket_qty = db.Column(db.Float)
    ticket_qty = db.Column(db.Float)

    def __init__(self, name=None, from_datetime=None, to_datetime=None, rate=None, operator=None, min_ticket_qty=None,
                 max_ticket_qty=None, ticket_qty=None, discount_type=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.from_datetime = from_datetime
        self.to_datetime = to_datetime
        self.rate = rate
        self.operator = operator
        self.min_ticket_qty = min_ticket_qty
        self.max_ticket_qty = max_ticket_qty
        self.ticket_qty = ticket_qty
        self.type = discount_type

    @classmethod
    def create(cls, name, from_datetime, to_datetime, rate, operator, min_ticket_qty, max_ticket_qty, ticket_qty,
               discount_type):
        discount = cls(name=name, from_datetime=from_datetime, to_datetime=to_datetime, rate=rate, operator=operator,
                       min_ticket_qty=min_ticket_qty, max_ticket_qty=max_ticket_qty, ticket_qty=ticket_qty,
                       discount_type=discount_type)
        db.session.add(discount)
        db.session.commit()
        return discount

    @classmethod
    def has_discount(cls, discount_id):
        return db.session.query(
            db.session.query(EventTicketDiscount).filter(EventTicketDiscount.id == discount_id).exists()).scalar()

    @classmethod
    def delete_discount(cls, discount_id):
        if not cls.has_discount(discount_id):
            raise exceptions.TicketDiscountNotFound()
        db.session.query(EventTicketDiscount).filter(EventTicketDiscount.id == discount_id).delete()
        db.session.commit()

    @classmethod
    def get_discount(cls, discount_id):
        return db.session.query(EventTicketDiscount).filter(EventTicketDiscount.id == discount_id).delete()

    def update(self):
        db.session.add(self)
        db.session.commit()

    def _meet_early_purchase_criteria(self, ptime=datetime.now()):
        status = ptime >= self.from_datetime and ptime <= self.to_datetime
        print("__meet_early_purchase_criteria##", status)
        return status

    def _meet_qty_purchased_criteria(self, ticket_qty):
        if self.operator == TicketDiscountOperator.EQUAL_TO:
            return ticket_qty == self.ticket_qty
        elif self.operator == TicketDiscountOperator.GREATER_THAN:
            return ticket_qty > self.ticket_qty
        elif self.operator == TicketDiscountOperator.GREATER_THAN_OR_EQUAL_TO:
            return ticket_qty >= self.ticket_qty
        elif self.operator == TicketDiscountOperator.BETWEEN:
            return (ticket_qty >= self.min_ticket_qty) and (ticket_qty <= self.max_ticket_qty)
        else:
            raise exceptions.InvalidTicketDiscountCompOperator()

    def can_redeem_discount(self, order_line):
        print("can_redeem_discount##", self.type)
        if self.type == DiscountTypes.EARLY_PURCHASE:
            ptime = datetime.now()
            return self._meet_early_purchase_criteria(ptime)
        elif self.type == DiscountTypes.NUMBER_OF_PURCHASED_TICKETS:
            return self._meet_qty_purchased_criteria(order_line.ticket_qty)
        else:
            raise exceptions.TicketTypeDiscountTypeNotFound()

    def compute_discount_amount_for_order_line(self, order_line):
        if not self.can_redeem_discount(order_line):
            return 0
        return (self.rate / 100) * order_line.total_amount


class EventTicket(db.Model):
    __tablename__ = 'event_tickets'

    id = db.Column(db.String, primary_key=True)
    ref = db.Column(db.String)
    event_id = db.Column(db.String, db.ForeignKey('events.id', onupdate=CASCADE, ondelete=CASCADE))
    event = relationship('Event')
    owner_id = db.Column(db.String, db.ForeignKey('users.id', onupdate=CASCADE, ondelete=CASCADE))
    owner = relationship('User')
    sale_line_id = db.Column(db.String, db.ForeignKey('ticket_sale_lines.id', onupdate=CASCADE, ondelete=CASCADE))
    sale_line = relationship('EventTicketSaleLine')
    sale_order_id = db.Column(db.String, db.ForeignKey('ticket_sales.id', onupdate=CASCADE, ondelete=CASCADE))
    sale_order = relationship('EventTicketSaleOrder')
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    assignment = relationship('EventTicketTypeAssignment', backref='ticket_sale_lines')
    ticket_type_id = db.Column(db.String, db.ForeignKey('event_ticket_types.id', ondelete=CASCADE, onupdate=CASCADE))
    ticket_type = relationship('EventTicketType')

    def __init__(self, sale_line):
        self.id = str(uuid.uuid4())
        self.is_assigned = False
        self.event = sale_line.sale_order.event
        self.sale_line = sale_line
        self.sale_order = sale_line.sale_order
        self.owner = sale_line.sale_order.customer
        self.ticket_type = self.sale_line.ticket_type
        self.created_at = datetime.now()

    @classmethod
    def has_ticket(cls, ticket_id):
        return db.session.query(db.session.query(EventTicket).filter(EventTicket.id == ticket_id).exists()).scalar()

    @classmethod
    def user_has_tickets_for_event(cls, event, user):
        """
        Returns whether a user has tickets for this event, either user's own purchased tickets or
        tickets gifted to him
        :param event:
        :param user:
        :return:
        """
        return cls.user_has_gifted_tickets_for_event(event, user) or cls.user_has_unassigned_tickets_for_event(event,
                                                                                                               user)

    @staticmethod
    def user_has_assigned_tickets_for_event(event, user):
        count = db.session.query(EventTicket) \
            .options(joinedload(EventTicket.owner)) \
            .filter(EventTicket.event == event) \
            .filter(EventTicket.assignment.any(EventTicketTypeAssignment.ticket_id == EventTicket.id),
                    EventTicketTypeAssignment.assigned_to == user) \
            .count()
        return bool(count)

    @staticmethod
    def user_has_gifted_tickets_for_event(event, user):
        return db.session.query(db.session.query(EventTicket)
                                .options(joinedload(EventTicket.owner))
                                .filter(EventTicket.event_id == event.id)
                                .filter(
            EventTicket.assignment.any(EventTicketTypeAssignment.ticket_id == EventTicket.id),
            EventTicketTypeAssignment.assigned_to_user_id == user.id
        ).exists()).scalar()

    @staticmethod
    def user_has_unassigned_tickets_for_event(event, user):
        return db.session.query(db.session.query(EventTicket)
                                .options(joinedload(EventTicket.owner))
                                .filter(EventTicket.event_id == event.id)
                                .filter(
            ~EventTicket.assignment.any(EventTicketTypeAssignment.ticket_id == EventTicket.id))
                                .filter(EventTicket.owner_id == user.id).exists()).scalar()

    @staticmethod
    def get_user_assigned_tickets_for_event(event, user):
        return db.session.query(EventTicket) \
            .options(joinedload(EventTicket.owner), joinedload(EventTicket.assignment)) \
            .filter(EventTicket.event_id == event.id) \
            .filter(EventTicket.assignment.any(EventTicketTypeAssignment.ticket_id == EventTicket.id)) \
            .filter(EventTicket.owner_id == user.id) \
            .all()

    @staticmethod
    def get_user_unassigned_tickets_for_event(event, user):
        return db.session.query(EventTicket) \
            .options(joinedload(EventTicket.owner),
                     joinedload(EventTicket.assignment)
                     ) \
            .filter(EventTicket.event_id == event.id) \
            .filter(~EventTicket.assignment.any(EventTicketTypeAssignment.ticket_id == EventTicket.id)) \
            .filter(EventTicket.owner_id == user.id) \
            .all()

    def assign_to(self, user):
        if user:
            if self.user_has_tickets_for_event(self.event, user):
                raise exceptions.AlreadyHasTicketsForEvent()
            self.assignment = [EventTicketTypeAssignment.create(event=self.event, sale_line=self.sale_line,
                                                                assigned_by=self.sale_order.customer, assigned_to=user)]
            self.is_assigned = True
            db.session.add(self)
            db.session.commit()

    def unassign_from(self, user):
        if not self.is_assigned_to(user):
            raise exceptions.TicketNotAssignedToUser()

        db.session.query(EventTicketTypeAssignment) \
            .filter(EventTicketTypeAssignment.assigned_to == user) \
            .delete()
        self.is_assigned = False
        db.session.commit()

    def is_assigned(self):
        count = db.session.query(EventTicketTypeAssignment) \
            .filter(EventTicketTypeAssignment.id == self.id) \
            .count()
        return bool(count)

    def is_assigned_to(self, user):
        return self.assignment[0].assigned_to == user

    def is_owned_by(self, user):
        return self.owner == user

    def is_unassigned(self):
        count = db.session.query(EventTicketTypeAssignment) \
            .filter(EventTicketTypeAssignment.id == self.id) \
            .count()
        return bool(count)

    def is_assigned_to(self, user):
        return db.session.query(db.session.query(EventTicket).filter(
            EventTicket.assignment.any(EventTicketTypeAssignment.assigned_to == user)).exists()).scalar()

    def generate_reference(self):
        ref = "REF#" + str(random.randint(100, 999999999999999999999))
        self.ref = ref
        db.session.commit()

    @staticmethod
    def get_gifted_tickets(ticket_type, user):
        gifted_tickets = db.session.query(EventTicket) \
            .join(EventTicket.sale_line) \
            .filter(EventTicketSaleLine.ticket_type_id == ticket_type.id) \
            .filter(EventTicket.assignment.any(and_(EventTicketTypeAssignment.ticket_id == EventTicket.id,
                                                    EventTicketTypeAssignment.assigned_to_user_id == user.id))) \
            .all()
        return gifted_tickets or []

    @staticmethod
    def get_assigned_tickets_of_type(ticket_type, user=None):
        """
        Returns all assigned tickets of a given <ticket_type>
        :param ticket_type:
        :return:
        """
        query = db.session.query(EventTicket).filter(EventTicket.ticket_type_id == ticket_type.id)

        if user:
            query = query.filter(EventTicket.assignment.any(EventTicketTypeAssignment.assigned_by_user_id == user.id))
        query = query.filter(EventTicket.assignment.any(EventTicketTypeAssignment.ticket_id == EventTicket.id))
        return query.all()

    @staticmethod
    def get_unassigned_tickets_of_type(ticket_type, user=None):
        query = db.session.query(EventTicket).filter(EventTicket.ticket_type_id == ticket_type.id) \
            .filter(~EventTicket.assignment.any(EventTicketTypeAssignment.ticket_id == EventTicket.id))

        if user:
            query = query.filter(EventTicket.owner_id == user.id)

        unassigned_tickets = query.all()
        return unassigned_tickets

    @classmethod
    def get_ticket(cls, ticket_id):
        if not cls.has_ticket(ticket_id):
            raise exceptions.TicketNotFound()
        return db.session.query(EventTicket) \
            .options(joinedload(EventTicket.owner),
                     joinedload(EventTicket.assignment)
                     ) \
            .filter(EventTicket.id == ticket_id) \
            .first()


class EventAttendee(db.Model):
    __tablename__ = 'event_attendees'

    id = db.Column(db.String, primary_key=True)
    attendee_id = db.Column(db.String, db.ForeignKey('users.id', onupdate=CASCADE))
    attendee = relationship('User')
    sale_order_id = db.Column(db.String, db.ForeignKey('ticket_sales.id', onupdate=CASCADE))
    sale_order = relationship('EventTicketSaleOrder')
    ownership_by_purchase = db.Column(db.Boolean, default=False)
    ownership_by_assignment = db.Column(db.Boolean, default=False)
    event_id = db.Column(db.String, db.ForeignKey('events.id', onupdate=CASCADE))
    event = relationship('Event')

    def __init__(self, attendee=None, attendee_id=None, event_id=None, event=None, sale_order=None, sale_order_id=None,
                 ownership_by_purchase=None, ownership_by_assignment=None):
        self.id = str(uuid.uuid4())
        self.attendee = attendee
        self.attendee_id = attendee_id
        self.event = event
        self.event_id = event_id
        self.sale_order = sale_order
        self.sale_order_id = sale_order_id
        self.ownership_by_assignment = ownership_by_assignment
        self.ownership_by_purchase = ownership_by_purchase

    @classmethod
    def add_attendee(cls, attendee=None, event=None, sale_order=None, ownership_by_purchase=None,
                     ownership_by_assignment=None):
        event_attendee = EventAttendee(sale_order=sale_order, event=event, attendee=attendee,
                                       ownership_by_purchase=ownership_by_purchase,
                                       ownership_by_assignment=ownership_by_assignment)
        db.session.add(event_attendee)
        db.session.commit()

    @classmethod
    def remove_attendee(cls, attendee):
        db.session.query(EventAttendee).filter(EventAttendee.attendee_id == attendee.id).delete()
        db.session.commit()


class EventTicketTypeAssignment(db.Model):
    __tablename__ = 'event_ticket_assignments'

    id = db.Column(db.String, primary_key=True, default=str(uuid.uuid4()))
    sale_line = relationship('EventTicketSaleLine')
    sale_line_id = db.Column(db.String, db.ForeignKey('ticket_sale_lines.id', ondelete=CASCADE, onupdate=CASCADE))
    assigned_by_user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete=CASCADE, onupdate=CASCADE))
    assigned_to_user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete=CASCADE, onupdate=CASCADE))
    assigned_by = relationship('User', foreign_keys=[assigned_by_user_id])
    assigned_to = relationship('User', foreign_keys=[assigned_to_user_id])
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime)
    ticket_id = db.Column(db.String, db.ForeignKey('event_tickets.id', ondelete=CASCADE, onupdate=CASCADE))
    ticket = relationship('EventTicket')
    event_id = db.Column(db.String, db.ForeignKey('events.id', ondelete=CASCADE, onupdate=CASCADE))
    event = relationship('Event')

    def __init__(self, sale_line=None, sale_line_id=None, assigned_by_user_id=None, assigned_by=None,
                 assigned_to_id=None, assigned_to=None, event=None):
        self.id = str(uuid.uuid4())

        if sale_line:
            self.sale_line = sale_line

        if sale_line_id:
            self.sale_line_id = sale_line_id

        if assigned_by_user_id:
            self.assigned_by_user_id = assigned_by_user_id

        if assigned_by:
            self.assigned_by = assigned_by

        if assigned_to_id:
            self.assigned_to_user_id = assigned_to_id

        if assigned_to:
            self.assigned_to = assigned_to

        if event:
            self.event_id = event.id

    @classmethod
    def create(cls, event, sale_line=None, assigned_by=None, assigned_to=None):
        assignment = cls(sale_line=sale_line, assigned_by=assigned_by, assigned_to=assigned_to, event=event)
        db.session.add(assignment)
        db.session.commit()

        return assignment


class EventPrivacyInfo(db.Model):
    __tablename__ = 'event_privacy_info'

    id = db.Column(db.String, primary_key=True, default=str(uuid.uuid4()))
    media_is_plateform_shareable = db.Column(db.Boolean)
    media_is_public_shareable = db.Column(db.Boolean)


class SocialMedia(db.Model):
    __tablename__ = 'social_media'

    id = db.Column(db.String, primary_key=True, default=str(uuid.uuid4()))
    name = db.Column(db.String)

    def __init__(self, name):
        self.id = str(uuid.uuid4())
        self.name = name

    @classmethod
    def create(cls, name):
        social_account = cls(name)
        db.session.add(social_account)
        db.session.commit()

    @classmethod
    def has_social_account(cls, social_account_id):
        return db.session.query(
            db.session.query(SocialMedia).filter(SocialMedia.id == social_account_id).exists()).scalar()

    @classmethod
    def get_social_account(cls, account_id):
        if not cls.has_social_account(account_id):
            raise exceptions.SocialAccountNotFound()

        return db.session.query(SocialMedia).filter(SocialMedia.id == account_id).first()

    @classmethod
    def get_all(cls):
        return db.session.query(SocialMedia).all()


class EventReview(db.Model):
    __tablename__ = 'event_reviews'

    id = db.Column(db.String, primary_key=True)
    content = db.Column(db.String)
    published_at = db.Column(db.DateTime, default=datetime.now())
    upvotes = relationship('EventReviewUpvote')
    downvotes = relationship('EventReviewDownvote')
    author_id = db.Column(db.String, db.ForeignKey('users.id'))
    author = relationship(User)
    media = relationship('EventReviewMedia', backref='event_reviews')
    event_id = db.Column(db.String, db.ForeignKey('events.id', onupdate=CASCADE, ondelete=CASCADE))
    event = relationship(Event)
    comments = relationship('EventReviewComment', backref='event_reviews')
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    def __init__(self, content=None, author_id=None, author=None, media=None, event_id=None, event=None):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.published_at = datetime.now()

        if content:
            self.content = content

        if author:
            self.author = author

        if author_id:
            self.author_id = author_id

        if media:
            self.media = media

        if event:
            self.event = event

        if event_id:
            self.event_id = event_id

    def is_upvoted_by(self, author):
        return db.session.query(db.session.query(EventReviewUpvote)
                                .filter(EventReviewUpvote.review_id == self.id)
                                .filter(EventReviewUpvote.author_id == author.id).exists()).scalar()

    def is_downvoted_by(self, author):
        return db.session.query(db.session.query(EventReviewDownvote)
                                .filter(EventReviewDownvote.review_id == self.id)
                                .filter(EventReviewDownvote.author_id == author.id).exists()).scalar()

    def upvotes_count(self):
        return db.session.query(EventReviewUpvote) \
            .filter(EventReviewUpvote.review_id == self.id) \
            .count()

    def downvotes_count(self):
        return db.session.query(EventReviewDownvote) \
            .filter(EventReviewDownvote.review_id == self.id) \
            .count()

    def comments_count(self):
        return db.session.query(EventReviewComment) \
            .filter(EventReviewComment.review_id == self.id) \
            .count()

    def upvote(self, upvote):
        if self.is_upvoted_by(upvote.author):
            raise exceptions.AlreadyUpvoted()

        if self.is_downvoted_by(upvote.author):
            raise exceptions.AlreadyDownvoted()
        self.upvotes.append(upvote)
        db.session.commit()

    def remove_upvote_by(self, author):
        db.session.query(EventReviewUpvote) \
            .filter(EventReviewUpvote.review_id == self.id) \
            .filter(EventReviewUpvote.author_id == author.id) \
            .delete()
        db.session.commit()

    def downvote(self, downvote):
        if self.is_downvoted_by(downvote.author):
            raise exceptions.AlreadyDownvoted()

        if self.is_upvoted_by(downvote.author):
            raise exceptions.AlreadyUpvoted()
        self.downvotes += [downvote]
        db.session.add(self)
        db.session.commit()

    def remove_downvote_by(self, author):
        db.session.query(EventReviewDownvote) \
            .filter(EventReviewDownvote.review_id == self.id) \
            .filter(EventReviewDownvote.author_id == author.id) \
            .delete()
        db.session.commit()

    def has_review_comment(self, comment_id):
        return db.session.query(db.session.query(EventReviewComment) \
                                .filter(EventReviewComment.id == comment_id) \
                                .filter(EventReviewComment.review_id == self.id).exists()).scalar()

    def add_review_comment(self, comment):
        self.comments += [comment]
        db.session.commit()

    def remove_review_comment(self, comment_id):
        if not self.has_review_comment(comment_id):
            raise exceptions.ReviewCommentNotFound()
        db.session.query(EventReviewComment).filter(EventReviewComment.id == comment_id).delete()

    def get_total_event_review_comments(self):
        return db.session.query(EventReviewComment) \
            .filter(EventReviewComment.review_id == self.id) \
            .count()

    def get_comment_only(self, comment_id):
        return db.session.query(EventReviewComment) \
            .filter(EventReviewComment.id == comment_id) \
            .filter(EventReviewComment.review_id == self.id) \
            .first()

    def get_review_comment(self, comment_id):
        if not self.has_review_comment(comment_id):
            raise exceptions.ReviewCommentNotFound()

        return db.session.query(EventReviewComment).options(
            joinedload(EventReviewComment.upvotes),
            joinedload(EventReviewComment.downvotes),
            joinedload(EventReviewComment.author),
            joinedload(EventReviewComment.media)
        ).filter(EventReviewComment.review_id == self.id) \
            .filter(EventReviewComment.id == comment_id) \
            .first()

    def has_more_review_comments(self, cursor=None):
        _cursor = copy.copy(cursor)
        more_review_comments = self.get_review_comments(_cursor)
        return len(more_review_comments) > 0

    def get_review_comments(self, cursor):
        query = db.session.query(EventReviewComment).options(
            joinedload(EventReviewComment.upvotes),
            joinedload(EventReviewComment.downvotes),
            joinedload(EventReviewComment.author),
            joinedload(EventReviewComment.media)
        ).filter(EventReviewComment.review_id == self.id)

        if cursor and cursor.after:
            query = query.filter(
                func.round(cast(func.extract('EPOCH', EventReviewComment.created_at), Numeric), 3) < func.round(
                    cursor.get_after_as_float(), 3))

        elif cursor and cursor.before:
            query = query.filter(
                func.round(cast(func.extract('EPOCH', EventReviewComment.created_at), Numeric), 3) > func.round(
                    cursor.get_before_as_float()), 3)

        comments = query.order_by(EventReviewComment.created_at.desc()).limit(cursor.limit).all()
        if comments:
            cursor.set_before(comments[0].created_at)
            cursor.set_after(comments[-1].created_at)
            cursor.set_has_more(self.has_more_review_comments(cursor))
        else:
            cursor.set_before(None)
            cursor.set_after(None)
            cursor.set_has_more(False)

        return comments


class EventReviewMedia(db.Model):
    __tablename__ = 'event_review_media'

    id = db.Column(db.String, primary_key=True, default=uuid.uuid4)
    filename = db.Column(db.String)
    source_url = db.Column(db.String)
    media_type = db.Column(db.String)
    poster = Column(Boolean, default=False)
    review = relationship(EventReview)
    review_id = db.Column(db.String, db.ForeignKey('event_reviews.id', ondelete=CASCADE, onupdate=CASCADE))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    def __init__(self, source_url=None, format=None, event=None, is_poster=False):
        self.id = str(uuid.uuid4())
        self.filename = utils.gen_image_filename(self.id)
        self.source_url = source_url
        self.format = format
        self.event = event
        self.is_poster = is_poster
        self.created_at = datetime.now()

    @classmethod
    def create(cls, event=None, source_url=None, format=None, is_poster=False):
        media = cls(source_url=source_url, format=format, event=event, is_poster=is_poster)
        db.session.add(media)
        return media

    def add_source_url(self, url):
        self.source_url = url
        db.session.commit()

    def add_format(self, format):
        self.format = format

    def add_event(self, event):
        self.event = event
        db.session.commit()

    def is_poster(self, is_poster):
        self.is_poster = is_poster
        db.session.commit()

    def delete(self):
        db.session.query(EventMedia).filter(EventMedia.id == self.id).delete()
        db.session.commit()


class EventReviewUpvote(db.Model):
    __tablename__ = 'event_review_upvotes'

    id = db.Column(db.String, primary_key=True)
    author_id = db.Column(db.String, db.ForeignKey('users.id'))
    author = relationship(User)
    review_id = db.Column(db.String, db.ForeignKey('event_reviews.id', ondelete=CASCADE, onupdate=CASCADE))
    review = relationship(EventReview)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    def __init__(self, author=None, review=None):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()

        if author:
            self.author = author

        if review:
            self.review = review


class EventReviewDownvote(db.Model):
    __tablename__ = 'event_review_downvotes'

    id = db.Column(db.String, primary_key=True)
    author_id = db.Column(db.String, db.ForeignKey('users.id'))
    author = relationship(User)
    review_id = db.Column(db.String, db.ForeignKey('event_reviews.id', ondelete=CASCADE, onupdate=CASCADE))
    review = relationship(EventReview)
    created_at = db.Column(db.DateTime)

    def __init__(self, author=None, review=None):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()

        if author:
            self.author = author

        if review:
            self.review = review


class EventStream(db.Model):
    __tablename__ = 'event_streams'

    id = db.Column(db.String, primary_key=True)
    content = db.Column(db.String)
    published_at = db.Column(db.DateTime, default=datetime.now())
    upvotes = relationship('EventStreamUpvote')
    downvotes = relationship('EventStreamDownvote')
    author_id = db.Column(db.String, db.ForeignKey('users.id'))
    author = relationship(User)
    media = relationship('EventStreamMedia', backref='event_streams')
    event_id = db.Column(db.String, db.ForeignKey('events.id', onupdate=CASCADE, ondelete=CASCADE))
    event = relationship(Event)

    def __init__(self, content=None, author_id=None, author=None, media=None, event_id=None, event=None):
        self.id = str(uuid.uuid4())
        self.published_at = datetime.now()

        if content:
            self.content = content

        if author:
            self.author = author

        if author_id:
            self.author_id = author_id

        if media:
            self.media = media

        if event:
            self.event = event

        if event_id:
            self.event_id = event_id


class EventStreamMedia(db.Model):
    __tablename__ = 'event_stream_media'

    id = db.Column(db.String, primary_key=True)
    type = db.Column(db.String, index=True)
    url = db.Column(db.String)
    stream_id = db.Column(db.String, db.ForeignKey('event_streams.id', ondelete=CASCADE, onupdate=CASCADE))
    stream = relationship(EventStream)

    def __init__(self, type=None, url=None):
        if type:
            self.type = type

        if url:
            self.url = url

        self.id = str(uuid.uuid4())


class EventStreamUpvote(db.Model):
    __tablename__ = 'event_stream_upvotes'

    id = db.Column(db.String, primary_key=True)
    author_id = db.Column(db.String, db.ForeignKey('users.id'))
    author = relationship(User)
    stream_id = db.Column(db.String, db.ForeignKey('event_streams.id', ondelete=CASCADE, onupdate=CASCADE))
    stream = relationship(EventStream)
    created_at = db.Column(db.DateTime, default=datetime.now())

    def __init__(self, author=None, author_id=None, stream=None, stream_id=None):
        self.id = str(uuid.uuid4())

        if author:
            self.author = author

        if author_id:
            self.author_id = author_id

        if stream:
            self.stream = stream

        if stream_id:
            self.stream_id = stream_id


class EventStreamDownvote(db.Model):
    __tablename__ = 'event_stream_downvotes'

    id = db.Column(db.String, primary_key=True)
    author_id = db.Column(db.String, db.ForeignKey('users.id'))
    author = relationship(User)
    stream_id = db.Column(db.String, db.ForeignKey('event_streams.id', ondelete=CASCADE, onupdate=CASCADE))
    stream = relationship(EventStream)
    created_at = db.Column(db.DateTime, default=datetime.now())

    def __init__(self, author=None, author_id=None, stream=None, stream_id=None):
        self.id = str(uuid.uuid4())

        if author:
            self.author = author

        if author_id:
            self.author_id = author_id

        if stream:
            self.stream = stream

        if stream_id:
            self.stream_id = stream_id


class EventReviewComment(db.Model):
    __tablename__ = 'event_review_comments'

    id = db.Column(db.String, primary_key=True)
    content = db.Column(db.String)
    published_at = db.Column(db.DateTime)
    upvotes = relationship('EventReviewCommentUpvote')
    downvotes = relationship('EventReviewCommentDownvote')
    author_id = db.Column(db.String, db.ForeignKey('users.id'))
    author = relationship(User)
    review_id = db.Column(db.String, db.ForeignKey('event_reviews.id', ondelete=CASCADE, onupdate=CASCADE))
    review = relationship(EventReview)
    media = relationship('EventReviewCommentMedia')
    responses = relationship('EventReviewCommentResponse')
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    def __init__(self, content=None, author=None, media=None):
        self.id = str(uuid.uuid4())
        self.published_at = datetime.now()
        self.created_at = datetime.now()

        if content:
            self.content = content

        if author:
            self.author = author

        if media:
            self.media = media

    @classmethod
    def has_comment(cls, comment_id):
        return db.session.query(db.session.query(EventReviewComment)
                                .filter(EventReviewComment.id == comment_id).exists()).scalar()

    def is_upvoted_by(self, author):
        return db.session.query(db.session.query(EventReviewCommentUpvote) \
                                .filter(EventReviewCommentUpvote.comment_id == self.id) \
                                .filter(EventReviewCommentUpvote.author_id == author.id).exists()
                                ).scalar()

    def is_downvoted_by(self, author):
        return db.session.query(db.session.query(EventReviewCommentDownvote) \
                                .filter(EventReviewCommentDownvote.comment_id == self.id) \
                                .filter(EventReviewCommentDownvote.author_id == author.id).exists()
                                ).scalar()

    def upvotes_count(self):
        return db.session.query(EventReviewCommentUpvote) \
            .filter(EventReviewCommentUpvote.comment_id == self.id) \
            .count()

    def downvotes_count(self):
        return db.session.query(EventReviewCommentDownvote) \
            .filter(EventReviewCommentDownvote.comment_id == self.id) \
            .count()

    def responses_count(self):
        return db.session.query(EventReviewCommentResponse) \
            .filter(EventReviewCommentResponse.comment_id == self.id) \
            .count()

    def upvote(self, author):
        if self.is_upvoted_by(author):
            raise exceptions.AlreadyUpvoted()
        if self.is_downvoted_by(author):
            raise exceptions.AlreadyDownvoted()
        upvote = EventReviewCommentUpvote(author=author)
        self.upvotes += [upvote]
        db.session.commit()

    def downvote(self, author):
        downvote = EventReviewCommentDownvote(author=author)
        if self.is_upvoted_by(author):
            raise exceptions.AlreadyUpvoted()
        if self.is_downvoted_by(author):
            raise exceptions.AlreadyDownvoted()
        self.downvotes += [downvote]
        db.session.commit()

    def remove_upvote(self, author):
        db.session.query(EventReviewCommentUpvote) \
            .filter(EventReviewCommentUpvote.comment_id == self.id) \
            .filter(EventReviewCommentUpvote.author_id == author.id) \
            .delete()
        db.session.commit()

    def remove_downvote(self, author):
        db.session.query(EventReviewCommentDownvote) \
            .filter(EventReviewCommentDownvote.comment_id == self.id) \
            .filter(EventReviewCommentDownvote.author_id == author.id) \
            .delete()
        db.session.commit()

    def has_response(self, response_id):
        return db.session.query(db.session.query(EventReviewCommentResponse) \
                                .filter(EventReviewCommentResponse.id == response_id).exists()).scalar()

    def add_response(self, response):
        self.responses += [response]
        db.session.commit()

    def remove_response(self, response_id):
        if not self.has_review_comment_response(response_id):
            raise exceptions.EventReviewCommentResponseNotFound()

        db.session.query(EventReviewCommentResponse) \
            .filter(EventReviewCommentResponse.comment_id == self.id) \
            .filter(EventReviewCommentResponse.id == response_id) \
            .delete()

    def get_response_only(self, response_id):
        if not self.has_response(response_id):
            raise exceptions.EventReviewCommentResponseNotFound()

        return db.session.query(EventReviewCommentResponse) \
            .filter(EventReviewCommentResponse.comment_id == self.id) \
            .filter(EventReviewCommentResponse.id == response_id) \
            .first()

    def get_response(self, response_id):

        if not self.has_response(response_id):
            raise exceptions.EventReviewCommentResponseNotFound()

        return db.session.query(EventReviewCommentResponse).options(
            joinedload(EventReviewCommentResponse.upvotes),
            joinedload(EventReviewCommentResponse.downvotes),
            joinedload(EventReviewCommentResponse.author),
            joinedload(EventReviewCommentResponse.media)
        ).filter(EventReviewCommentResponse.id == response_id) \
            .first()

    def has_more_responses(self, cursor=None):
        _cursor = copy.copy(cursor)
        more_responses = self.get_responses(_cursor)
        return len(more_responses) > 0

    def get_responses(self, cursor):
        query = db.session.query(EventReviewCommentResponse).options(
            joinedload(EventReviewCommentResponse.upvotes),
            joinedload(EventReviewCommentResponse.downvotes),
            joinedload(EventReviewCommentResponse.author),
            joinedload(EventReviewCommentResponse.media)
        ).filter(EventReviewCommentResponse.comment_id == self.id)

        if cursor and cursor.after:
            query = query.filter(
                func.round(cast(func.extract('EPOCH', EventReviewCommentResponse.created_at), Numeric), 3) < func.round(
                    cursor.get_after_as_float(), 3))

        elif cursor and cursor.before:
            query = query.filter(
                func.round(cast(func.extract('EPOCH', EventReviewCommentResponse.created_at), Numeric), 3) > func.round(
                    cursor.get_before_as_float(), 3))

        responses = query.order_by(EventReviewCommentResponse.created_at.desc()).limit(cursor.limit).all()

        if responses:
            cursor.set_before(responses[0].created_at)
            cursor.set_after(responses[-1].created_at)
            cursor.set_has_more(self.has_more_responses(cursor))
        else:
            cursor.set_before(None)
            cursor.set_after(None)
            cursor.set_has_more(False)

        return responses

    def get_total_responses(self):
        return db.session.query(EventReviewCommentResponse). \
            filter(EventReviewCommentResponse.comment_id == self.id) \
            .count()


class EventReviewCommentMedia(db.Model):
    __tablename__ = 'event_review_comment_media'

    id = db.Column(db.String, primary_key=True, default=uuid.uuid4)
    filename = db.Column(db.String)
    source_url = db.Column(db.String)
    media_type = db.Column(db.String)
    poster = Column(Boolean, default=False)
    comment_id = db.Column(db.String, db.ForeignKey('event_review_comments.id', ondelete=CASCADE, onupdate=CASCADE))
    comment = relationship(EventReviewComment)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    def __init__(self, source_url=None, format=None, event=None, is_poster=False):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.filename = utils.gen_image_filename(self.id)
        self.source_url = source_url
        self.format = format
        self.event = event
        self.is_poster = is_poster

    @classmethod
    def create(cls, event=None, source_url=None, format=None, is_poster=False):
        media = cls(source_url=source_url, format=format, event=event, is_poster=is_poster)
        db.session.add(media)
        return media

    def add_source_url(self, url):
        self.source_url = url
        db.session.commit()

    def add_format(self, format):
        self.format = format

    def add_event(self, event):
        self.event = event
        db.session.commit()

    def is_poster(self, is_poster):
        self.is_poster = is_poster
        db.session.commit()

    def delete(self):
        db.session.query(EventMedia).filter(EventMedia.id == self.id).delete()
        db.session.commit()


class EventReviewCommentUpvote(db.Model):
    __tablename__ = 'event_review_comment_upvotes'

    id = db.Column(db.String, primary_key=True)
    author_id = db.Column(db.String, db.ForeignKey('users.id'))
    author = relationship(User)
    comment_id = db.Column(db.String, db.ForeignKey('event_review_comments.id', ondelete=CASCADE, onupdate=CASCADE))
    comment = relationship(EventReviewComment)
    created_at = db.Column(db.DateTime)

    def __init__(self, author=None, comment=None):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()

        if author:
            self.author = author

        if comment:
            self.comment = comment


class EventReviewCommentDownvote(db.Model):
    __tablename__ = 'event_review_comment_downvotes'

    id = db.Column(db.String, primary_key=True)
    author_id = db.Column(db.String, db.ForeignKey('users.id'))
    author = relationship(User)
    comment_id = db.Column(db.String, db.ForeignKey('event_review_comments.id', ondelete=CASCADE, onupdate=CASCADE))
    comment = relationship(EventReviewComment)
    created_at = db.Column(db.DateTime)

    def __init__(self, author=None, comment=None):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()

        if author:
            self.author = author

        if comment:
            self.comment = comment


class EventReviewCommentResponse(db.Model):
    __tablename__ = 'event_review_comment_responses'

    id = db.Column(db.String, primary_key=True)
    content = db.Column(db.String)
    published_at = db.Column(db.DateTime)
    upvotes = relationship('EventReviewCommentResponseUpvote')
    downvotes = relationship('EventReviewCommentResponseDownvote')
    author_id = db.Column(db.String, db.ForeignKey('users.id'))
    author = relationship(User)
    comment_id = db.Column(db.String, db.ForeignKey('event_review_comments.id', ondelete=CASCADE, onupdate=CASCADE))
    comment = relationship(EventReviewComment)
    media = relationship('EventReviewCommentResponseMedia')
    created_at = db.Column(db.DateTime)

    def __init__(self, content=None, author_id=None, author=None, media=None):
        self.id = str(uuid.uuid4())
        self.published_at = datetime.now();
        self.created_at = datetime.now()

        if content:
            self.content = content

        if author:
            self.author = author

        if author_id:
            self.author_id = author_id

        if media:
            self.media = media

    def is_upvoted_by(self, author):
        return db.session.query(db.session.query(EventReviewCommentResponseUpvote)
                                .filter(EventReviewCommentResponseUpvote.response_id == self.id)
                                .filter(EventReviewCommentResponseUpvote.author_id == author.id)
                                .exists()).scalar()

    def is_downvoted_by(self, author):
        return db.session.query(db.session.query(EventReviewCommentResponseDownvote)
                                .filter(EventReviewCommentResponseDownvote.response_id == self.id)
                                .filter(EventReviewCommentResponseDownvote.author_id == author.id).exists()).scalar()

    def upvotes_count(self):
        return db.session.query(EventReviewCommentResponseUpvote) \
            .filter(EventReviewCommentResponseUpvote.response_id == self.id) \
            .count()

    def downvotes_count(self):
        return db.session.query(EventReviewCommentResponseDownvote) \
            .filter(EventReviewCommentResponseDownvote.response_id == self.id) \
            .count()

    def upvote(self, author):
        upvote = EventReviewCommentResponseUpvote(author=author)
        if self.is_upvoted_by(author):
            raise exceptions.AlreadyUpvoted()
        if self.is_downvoted_by(author):
            raise exceptions.AlreadyDownvoted()
        self.upvotes.append(upvote)
        db.session.commit()

    def downvote(self, author):
        downvote = EventReviewCommentResponseDownvote(author=author)
        if self.is_upvoted_by(author):
            raise exceptions.AlreadyUpvoted()
        if self.is_downvoted_by(author):
            raise exceptions.AlreadyDownvoted()
        self.downvotes.append(downvote)
        db.session.commit()

    def remove_upvote_by(self, upvote_by):
        db.session.query(EventReviewCommentResponseUpvote) \
            .filter(EventReviewCommentResponseUpvote.response_id == self.id) \
            .filter(EventReviewCommentResponseUpvote.author_id == upvote_by.id) \
            .delete()

    def remove_downvote_by(self, downvoted_by):
        db.session.query(EventReviewCommentResponseDownvote) \
            .filter(EventReviewCommentResponseDownvote.response_id == self.id) \
            .filter(EventReviewCommentResponseDownvote.author_id == downvoted_by.id) \
            .delete()


class EventReviewCommentResponseMedia(db.Model):
    __tablename__ = 'event_review_comment_responses_media'

    id = db.Column(db.String, primary_key=True, default=uuid.uuid4)
    filename = db.Column(db.String)
    source_url = db.Column(db.String)
    media_type = db.Column(db.String)
    poster = Column(Boolean, default=False)
    response_id = db.Column(db.String,
                            db.ForeignKey('event_review_comment_responses.id', ondelete=CASCADE, onupdate=CASCADE))
    response = relationship(EventReviewCommentResponse)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    def __init__(self, source_url=None, format=None, event=None, is_poster=False):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.filename = utils.gen_image_filename(self.id)
        self.source_url = source_url
        self.format = format
        self.event = event
        self.is_poster = is_poster

    @classmethod
    def create(cls, event=None, source_url=None, format=None, is_poster=False):
        media = cls(source_url=source_url, format=format, event=event, is_poster=is_poster)
        db.session.add(media)
        return media

    def add_source_url(self, url):
        self.source_url = url
        db.session.commit()

    def add_format(self, format):
        self.format = format

    def add_event(self, event):
        self.event = event
        db.session.commit()

    def is_poster(self, is_poster):
        self.is_poster = is_poster
        db.session.commit()

    def delete(self):
        db.session.query(EventMedia).filter(EventMedia.id == self.id).delete()
        db.session.commit()


class EventReviewCommentResponseUpvote(db.Model):
    __tablename__ = 'event_review_comment_response_upvotes'

    id = db.Column(db.String, primary_key=True)
    author_id = db.Column(db.String, db.ForeignKey('users.id'))
    author = relationship(User)
    response_id = db.Column(db.String,
                            db.ForeignKey('event_review_comment_responses.id', ondelete=CASCADE, onupdate=CASCADE))
    response = relationship(EventReviewCommentResponse)
    created_at = db.Column(db.DateTime)

    def __init__(self, author=None, response=None):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()

        if author:
            self.author = author

        if response:
            self.response = response


class EventReviewCommentResponseDownvote(db.Model):
    __tablename__ = 'event_review_comment_response_downvotes'

    id = db.Column(db.String, primary_key=True)
    author_id = db.Column(db.String, db.ForeignKey('users.id'))
    author = relationship(User)
    response_id = db.Column(db.String,
                            db.ForeignKey('event_review_comment_responses.id', ondelete=CASCADE, onupdate=CASCADE))
    response = relationship(EventReviewCommentResponse)
    created_at = db.Column(db.DateTime)

    def __init__(self, author=None, response=None):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()

        if author:
            self.author = author

        if response:
            self.response = response


class EventStreamComment(db.Model):
    __tablename__ = 'event_stream_comments'

    id = db.Column(db.String, primary_key=True)
    content = db.Column(db.String)
    published_at = db.Column(db.DateTime)
    upvotes = relationship('EventStreamCommentUpvote')
    downvotes = relationship('EventStreamCommentDownvote')
    author_id = db.Column(db.String, db.ForeignKey('users.id'))
    author = relationship(User)
    stream_id = db.Column(db.String, db.ForeignKey('event_streams.id', ondelete=CASCADE, onupdate=CASCADE))
    stream = relationship(EventStream)
    media = relationship('EventStreamCommentMedia', backref='event_stream_comment_media')

    def __init__(self):
        self.id = str(uuid.uuid4())
        self.published_at = datetime.now()


class EventStreamCommentMedia(db.Model):
    __tablename__ = 'event_stream_comment_media'

    id = db.Column(db.String, primary_key=True)
    type = db.Column(db.String, index=True)
    url = db.Column(db.String)
    comment_id = db.Column(db.String, db.ForeignKey('event_stream_comments.id', ondelete=CASCADE, onupdate=CASCADE))
    comment = relationship(EventStreamComment)

    def __init__(self):
        self.id = str(uuid.uuid4())


class EventStreamCommentUpvote(db.Model):
    __tablename__ = 'event_stream_comment_upvotes'

    id = db.Column(db.String, primary_key=True)
    author_id = db.Column(db.String, db.ForeignKey('users.id'))
    author = relationship(User)
    commennt_id = db.Column(db.String, db.ForeignKey('event_stream_comments.id', ondelete=CASCADE, onupdate=CASCADE))
    comment = relationship(EventStreamComment)
    created_at = db.Column(db.DateTime)

    def __init__(self, author=None, author_id=None, comment=None, comment_id=None):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()

        if author:
            self.author = author

        if author_id:
            self.author_id = author_id

        if comment:
            self.comment = comment

        if comment_id:
            self.commennt_id = comment_id


class EventStreamCommentDownvote(db.Model):
    __tablename__ = 'event_stream_comment_downvotes'

    id = db.Column(db.String, primary_key=True)
    author_id = db.Column(db.String, db.ForeignKey('users.id'))
    author = relationship(User)
    comment_id = db.Column(db.String, db.ForeignKey('event_stream_comments.id', ondelete=CASCADE, onupdate=CASCADE))
    comment = relationship(EventStreamComment)
    created_at = db.Column(db.DateTime)

    def __init__(self, author=None, author_id=None, comment=None, comment_id=None):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()

        if author:
            self.author = author

        if author_id:
            self.author_id = author_id

        if comment:
            self.comment = comment

        if comment_id:
            self.comment_id = comment_id


class EventStreamCommentResponse(db.Model):
    __tablename__ = 'event_stream_comment_responses'

    id = db.Column(db.String, primary_key=True)
    content = db.Column(db.String)
    published_at = db.Column(db.DateTime)
    upvotes = relationship('EventStreamCommentResponseUpvote')
    downvotes = relationship('EventStreamCommentResponseDownvote')
    author_id = db.Column(db.String, db.ForeignKey('users.id'))
    author = relationship(User)
    comment_id = db.Column(db.String, db.ForeignKey('event_stream_comments.id', ondelete=CASCADE, onupdate=CASCADE))
    comment = relationship(EventStreamComment)

    def __init__(self):
        self.id = str(uuid.uuid4())
        self.published_at = datetime.now()


class EventStreamCommentResponseMedia(db.Model):
    __tablename__ = 'event_stream_comment_responses_media'

    id = db.Column(db.String, primary_key=True)
    type = db.Column(db.String, index=True)
    url = db.Column(db.String)
    response_id = db.Column(db.String,
                            db.ForeignKey('event_stream_comment_responses.id', ondelete=CASCADE, onupdate=CASCADE))
    response = relationship(EventStreamCommentResponse)

    def __init__(self):
        self.id = str(uuid.uuid4())


class EventStreamCommentResponseUpvote(db.Model):
    __tablename__ = 'event_stream_comment_response_upvotes'

    id = db.Column(db.String, primary_key=True)
    author_id = db.Column(db.String, db.ForeignKey('users.id'))
    author = relationship(User)
    response_id = db.Column(db.String,
                            db.ForeignKey('event_stream_comment_responses.id', ondelete=CASCADE, onupdate=CASCADE))
    response = relationship(EventStreamCommentResponse)
    created_at = db.Column(db.DateTime)

    def __init__(self, author=None, author_id=None, response=None, response_id=None):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()

        if author:
            self.author = author

        if author_id:
            self.author_id = author_id

        if response:
            self.response = response

        if response_id:
            self.response_id = response_id


class EventStreamCommentResponseDownvote(db.Model):
    __tablename__ = 'event_stream_comment_response_downvotes'

    id = db.Column(db.String, primary_key=True)
    author_id = db.Column(db.String, db.ForeignKey('users.id'))
    author = relationship(User)
    response_id = db.Column(db.String,
                            db.ForeignKey('event_stream_comment_responses.id', ondelete=CASCADE, onupdate=CASCADE))
    response = relationship(EventStreamCommentResponse)
    created_at = db.Column(db.DateTime)

    def __init__(self, author=None, author_id=None, response=None, response_id=None):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()

        if author:
            self.author = author

        if author_id:
            self.author_id = author_id

        if response:
            self.response = response

        if response_id:
            self.response_id = response_id


class BrandCategory(db.Model):
    __tablename__ = 'brand_categories'

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    slug = db.Column(db.String)
    brands = relationship('Brand', backref='brand_categories')

    def __init__(self, name=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.slug = generate_slug(name)

    @staticmethod
    def has_category(category_id):
        return db.session.query(
            db.session.query(BrandCategory).filter(BrandCategory.id == category_id).exists()).scalar()

    @staticmethod
    def get_categories():
        return db.session.query(BrandCategory).all()

    @staticmethod
    def get_category(category_id):
        return db.session.query(BrandCategory).filter(BrandCategory.id == category_id).first()

    @classmethod
    def remove_category(cls, category_id):
        if not cls.has_category(category_id):
            raise exceptions.BrandCategoryNotFound()
        db.session.query(BrandCategory).filter(BrandCategory.id == category_id).delete()
        db.session.commit()

    @staticmethod
    def add_category(category):
        db.session.add(category)
        db.session.commit()

    @staticmethod
    def add_categories(categories):
        db.session.add_all(categories)
        db.session.commit()

    def update(self, name):
        self.name = name
        db.session.commit()


class Brand(db.Model):
    __tablename__ = 'brands'

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    country = db.Column(db.String)
    image = relationship('BrandMedia', uselist=False, back_populates="brand")
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    creator = relationship(User)
    creator_id = db.Column(db.String, db.ForeignKey('users.id'))
    category = relationship('BrandCategory')
    category_id = db.Column(db.String, db.ForeignKey('brand_categories.id', ondelete=CASCADE, onupdate=CASCADE))
    endorsements = relationship('BrandValidation')
    founded_date = db.Column(db.String)
    founders = relationship('BrandFounder')
    website_link = db.Column(db.String)

    def __init__(self, name=None, description=None, country=None, creator=None, category=None, image=utils.NO_IMAGE, founders=None,
                 founded_date=None, website_link=None):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.name = name
        self.description = description
        self.country = country
        self.creator = creator
        self.category = category
        self.image = image
        self.founders = founders
        self.founded_date = founded_date
        self.website_link = website_link

    @classmethod
    def create(cls, name=None, description=None, country=None, creator=None, category=None, image=None, founders=None,
               founded_date=None, website_link=None):
        brand = cls(name=name, description=description, country=country, creator=creator, category=category,
                    image=image, founders=founders, founded_date=founded_date, website_link=website_link)
        db.session.add(brand)
        db.session.commit()
        return brand

    @classmethod
    def has_brand(cls, brand_id):
        return db.session.query(db.session.query(Brand).filter(Brand.id == brand_id).exists()).scalar()

    @classmethod
    def has_more_brands(cls, category_id=None, searchterm=None, cursor=None):
        _cursor = copy.copy(cursor)
        more_brands = cls.get_brands(category_id, searchterm, _cursor)
        return len(more_brands) > 0

    @classmethod
    def get_brands(cls, category_id=None, searchterm=None, cursor=None):
        query = db.session.query(Brand)

        if searchterm:
            query = query.filter(Brand.name.ilike("%" + searchterm + "%"))
        if category_id:
            query = query.filter(Brand.category_id == category_id)
        query = query.options(joinedload(Brand.endorsements))

        if cursor and cursor.after:
            query = query.filter(func.round(cast(func.extract('EPOCH', Brand.created_at), Numeric), 3) < func.round(
                cursor.get_after_as_float(), 3))

        elif cursor and cursor.before:
            query = query.filter(func.round(cast(func.extract('EPOCH', Brand.created_at), Numeric), 3) > func.round(
                cursor.get_before_as_float(), 3))

        brands = query.order_by(Brand.created_at.desc()).limit(cursor.limit).all()

        if brands:
            cursor.set_before(brands[0].created_at)
            cursor.set_after(brands[-1].created_at)
            cursor.set_has_more(cls.has_more_brands(category_id, searchterm, cursor))
        else:
            cursor.set_before(None)
            cursor.set_after(None)
            cursor.set_has_more(False)

        return brands

    @classmethod
    def get_brands_total(cls, category_id=None, searchterm=None):
        query = db.session.query(Brand)

        if searchterm:
            query = query.filter(Brand.name.ilike("%" + searchterm + "%"))
        if category_id:
            query = query.filter(Brand.category_id == category_id)
        query = query.options(joinedload(Brand.endorsements))
        return query.count()

    @classmethod
    def get_brand(cls, brand_id):
        if not cls.has_brand(brand_id):
            raise exceptions.BrandNotFound()
        return db.session.query(Brand).options(
            joinedload(Brand.endorsements)
        ).filter(Brand.id == brand_id).first()

    def is_validated_by_user(self, user):
        return db.session.query(
            db.session.query(BrandValidation)
                .filter(BrandValidation.validator_id == user.id)
                .filter(BrandValidation.brand_id == self.id)
                .exists()
        ).scalar()

    @classmethod
    def delete_brand(cls, brand_id):
        if not cls.has_brand(brand_id):
            raise exceptions.BrandNotFound()
        db.session.query(Brand).filter(Brand.id == brand_id).delete()
        db.session.commit()

    def get_brand_endorsements(self):
        return db.session.query(BrandValidation).filter(BrandValidation.brand_id == self.id).all()

    def add_validation(self, validation):
        if self.is_validated_by_user(validation.validator):
            raise exceptions.BrandAlreadyValidated()
        self.endorsements.append(validation)
        db.session.commit()

    def remove_validation_of_user(self, user):
        db.session.query(BrandValidation).filter(BrandValidation.validator_id == user.id).filter(
            BrandValidation.brand_id == self.id).delete()
        db.session.commit()

    def update(self):
        self.updated_at = datetime.now()
        db.session.add(self)
        db.session.commit()


class BrandMedia(db.Model):
    __tablename__ = 'brand_media'

    id = db.Column(db.String, primary_key=True, default=uuid.uuid4)
    filename = db.Column(db.String)
    source_url = db.Column(db.String)
    format = db.Column(db.String)
    brand = relationship(Brand)
    brand_id = db.Column(db.String, db.ForeignKey('brands.id', ondelete=CASCADE, onupdate=CASCADE))
    created_at = db.Column(db.DateTime)
    public_id = db.Column(db.String)

    def __init__(self, source_url=None, format=None, filename=None, public_id=None):
        self.id = str(uuid.uuid4())
        self.source_url = source_url
        self.format = format
        self.public_id = public_id
        self.filename = filename
        self.created_at = datetime.now()


class BrandFounder(db.Model):
    __tablename__ = 'brand_founders'

    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, index=True)
    url = db.Column(db.String)
    brand_id = db.Column(db.ForeignKey('brands.id', ondelete=CASCADE, onupdate=CASCADE))
    brand = relationship('Brand')

    def __init__(self, name=None, url=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.url = url


class BrandValidation(db.Model):
    __tablename__ = 'brand_validations'

    id = db.Column(db.String, primary_key=True)
    validator_id = db.Column(db.ForeignKey('users.id'))
    validator = relationship('User')
    created_at = db.Column(db.DateTime)
    brand_id = db.Column(db.ForeignKey('brands.id', ondelete=CASCADE, onupdate=CASCADE))
    brand = relationship('Brand')

    def __init__(self, validator):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.validator = validator


class UserFollower(db.Model):
    __tablename__ = 'user_followers'

    id = db.Column(db.String, primary_key=True)
    created_at = db.Column(db.DateTime)
    follower_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'))
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'))
    follower = relationship('User', foreign_keys=[follower_id])
    user = relationship('User', foreign_keys=[user_id])

    def __init__(self, user_id=None, user=None, follower_id=None, follower=None):
        self.id = str(uuid.uuid4())
        self.created = datetime.now()
        self.user_id = user_id
        self.user = user
        self.follower_id = follower_id
        self.follower = follower


class UserPaymentDetails(db.Model):
    __tablename__ = 'user_payment_details'

    id = db.Column(db.String, primary_key=True)
    mobile_network = db.Column(db.String)
    mobile_number = db.Column(db.String)
    card_name = db.Column(db.String)
    card_type = db.Column(db.String)
    card_number = db.Column(db.String)
    card_expiration_date = db.Column(db.DateTime)
    card_cv = db.Column(db.String)
    is_default_payment = db.Column(db.Boolean)
    payment_type = db.Column(db.String)
    user_id = db.Column(db.String, db.ForeignKey('users.id', ondelete=CASCADE, onupdate=CASCADE))
    user = relationship('User')
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    def __init__(self, user, payment_type, is_default_payment=False, mobile_payment_info=None, card_payment_info=None):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()

        self.user = user
        self.is_default_payment = is_default_payment
        self.payment_type = payment_type

        if mobile_payment_info:
            self.mobile_network = mobile_payment_info.mobile_network
            self.mobile_number = mobile_payment_info.mobile_number

        if card_payment_info:
            self.card_name = card_payment_info.card_name
            self.card_type = card_payment_info.card_type
            self.card_expiration_date = card_payment_info.card_expiration_date
            self.card_number = card_payment_info.card_number
            self.card_cv = card_payment_info.card_cv

    @classmethod
    def create_mobile_payment(cls, user, mobile_info, is_default_payment=False):
        payment_info = cls(user, payment_type=PaymentTypes.MOBILE_MONEY, is_default_payment=is_default_payment,
                           mobile_payment_info=mobile_info)
        db.session.add(payment_info)
        db.session.commit()
        cls.set_default_payment(payment_info)
        return payment_info

    @classmethod
    def create_card_payment(cls, user, card_info, is_default_payment=False):
        payment_info = cls(user, payment_type=PaymentTypes.CARD, is_default_payment=is_default_payment,
                           card_payment_info=card_info)
        db.session.add(payment_info)
        db.session.commit()
        cls.set_default_payment(payment_info)
        return payment_info

    def update_card_payment(self, card_info, is_default_payment=None):
        self.card_name = card_info.card_name or self.card_name
        self.card_number = card_info.card_number or self.card_number
        self.card_type = card_info.card_type or self.card_type
        self.card_cv = card_info.card_cv or self.card_cv
        self.card_expiration_date = card_info.card_expiration_date or self.card_expiration_date
        self.is_default_payment = is_default_payment or self.is_default_payment
        self.created_at = datetime.now()
        db.session.commit()
        self.set_default_payment(self)

    def update_mobile_payment(self, mobile_info, is_default_payment=None):
        self.mobile_network = mobile_info.mobile_network or self.mobile_network
        self.mobile_number = mobile_info.mobile_number or self.mobile_number
        self.is_default_payment = is_default_payment or self.is_default_payment
        self.updated_at = datetime.now()
        db.session.commit()
        self.set_default_payment(self)

    @classmethod
    def set_default_payment(cls, payment):
        query_text = text("""
            UPDATE user_payment_details SET is_default_payment = False  AND updated_at= :now WHERE id != :payment_id AND user_id = :user_id
        """).bindparams(payment_id=payment.id, user_id=payment.user_id, now=datetime.now())
        db.engine.execute(query_text)

    @classmethod
    def has_card_payment(cls, user):
        return db.session.query(
            db.session.query(UserPaymentDetails).filter(UserPaymentDetails.user_id == user.id).filter(
                UserPaymentDetails.payment_type == PaymentTypes.CARD).exists()).scalar()

    @classmethod
    def has_mobile_money_payment(cls, user):
        return db.session.query(
            db.session.query(UserPaymentDetails).filter(UserPaymentDetails.user_id == user.id).filter(
                UserPaymentDetails.payment_type == PaymentTypes.MOBILE_MONEY).exists()).scalar()

    @classmethod
    def get_payment(cls, user):
        return db.session.query(UserPaymentDetails).filter(UserPaymentDetails.user_id == user.id).first()

    @classmethod
    def get_card_payment(cls, user):
        return db.session.query(UserPaymentDetails).filter(UserPaymentDetails.user_id == user.id).filter(
            UserPaymentDetails.payment_type == PaymentTypes.CARD).first()

    @classmethod
    def get_mobile_payment(cls, user):
        return db.session.query(UserPaymentDetails).filter(UserPaymentDetails.user_id == user.id).filter(
            UserPaymentDetails.payment_type == PaymentTypes.MOBILE_MONEY).first()

    @classmethod
    def has_payment_account(cls, account_id):
        return db.session.query(
            db.session.query(UserPaymentDetails).filter(UserPaymentDetails.id == account_id).exists()).scalar()

    @classmethod
    def remove_payment_account(cls, account_id):
        db.session.query(UserPaymentDetails).filter(UserPaymentDetails.id == account_id).delete()
        db.session.commit()
        print("removePayment##")


class Notifications(Enum):
    EVENT_CREATED = "Event.created"
    EVENT_UPDATED = "Event.updated"
    EVENT_IS_DUE = "Event.is_due"
    EVENT_BOOKMARKED = "Event.bookmarked"
    EVENT_UNBOOKMARKED = "Event.unbookmarked"
    EVENT_RECOMMENDED = "Event.recommended"

    BRAND_UPDATED = "Brand.updated"
    BRAND_EVENT_AFFILIATE = "Brand.event_affiliated"

    USER_CREATED = "User.created"
    USER_PROFILE_UPDATED = "User.profile_updated"
    USER_PASSWORD_CHANGED = "User.password_changed"
    USER_ONBOARDING_EMAIL = "User.onboarding_email"

    PAYMENT_INFO_UPDATED = "payment_info.updated"
    PAYMENT_INFO_CLEARED = "payment_info.cleared"

    RELATION_CONNECTED = "Relation.connected"
    RELATION_DISCONNECTED = "Relation.disconnected"

    TICKET_ASSIGNED = "Ticket.assigned"
    TICKET_ASSIGNMENT_REVOKED = "Ticket.assigned_ticket_revoked"

    event_notifications = [EVENT_CREATED, EVENT_UPDATED, EVENT_IS_DUE, EVENT_BOOKMARKED, EVENT_UNBOOKMARKED,
                           EVENT_RECOMMENDED]
    brand_notifications = [BRAND_UPDATED, BRAND_EVENT_AFFILIATE]
    user_notifications = [USER_CREATED, USER_PROFILE_UPDATED, USER_PASSWORD_CHANGED, USER_ONBOARDING_EMAIL]
    payment_notifications = [PAYMENT_INFO_UPDATED, PAYMENT_INFO_CLEARED]
    relations_notifications = [RELATION_CONNECTED, RELATION_DISCONNECTED]
    tickets_notifications = [TICKET_ASSIGNED, TICKET_ASSIGNMENT_REVOKED]

    notifications = event_notifications + brand_notifications + payment_notifications + relations_notifications + tickets_notifications

    @classmethod
    def notification_exists(cls, notification):
        return notification in cls.notifications

    @staticmethod
    def ticket_assigned_message(ticket, assigned_by):
        return "{assigned_by_name} dashed you a free ticket for {event_name}".format(assigned_by_name=assigned_by.name,
                                                                                     event_name=ticket.event.name)

    @staticmethod
    def ticket_unassigned_message(ticket, assigned_by):
        return "{assigned_by_name} revoked a ticket dashed to you for the event, {event_name}".format(
            assigned_by_name=assigned_by.name,
            event_name=ticket.event.name)


class Notification(db.Model):
    __tablename__ = 'app_notifications'

    id = db.Column(db.String, primary_key=True)
    notification_type = db.Column(db.String, index=True)
    message = db.Column(db.String)
    created_at = db.Column(db.DateTime)
    recipient_id = db.Column(db.String, db.ForeignKey('users.id', onupdate=CASCADE, ondelete=CASCADE))
    recipient = relationship('User', foreign_keys=[recipient_id])
    actor_id = db.Column(db.String, db.ForeignKey('users.id', onupdate=CASCADE, ondelete=CASCADE))
    actor = relationship('User', foreign_keys=[actor_id])
    is_read = db.Column(db.Boolean, default=False)
    event_id = db.Column(db.String, db.ForeignKey('events.id', onupdate=CASCADE, ondelete=CASCADE))
    event = relationship('Event')
    brand_id = db.Column(db.String, db.ForeignKey('brands.id', onupdate=CASCADE, ondelete=CASCADE))
    brand = relationship('Brand')
    ticket_id = db.Column(db.String, db.ForeignKey('event_tickets.id', onupdate=CASCADE, ondelete=CASCADE))
    ticket = relationship('EventTicket')

    def __init__(self, notification_type, recipient, actor=None, event=None, brand=None, ticket=None):
        self.id = str(uuid.uuid4())
        self.notification_type = notification_type
        self.recipient = recipient
        self.actor = actor
        self.event = event
        self.brand = brand
        self.ticket = ticket
        self.created_at = datetime.now()

    @classmethod
    def create(cls, notification_type, recipient, actor=None, event=None, brand=None, ticket=None):
        notification = cls(notification_type, recipient, actor=actor, event=event, brand=brand, ticket=ticket)
        db.session.add(notification)
        db.session.commit()
        return notification

    @staticmethod
    def get_unread_notifications(user, cursor=None):

        query = db.session.query(Notification) \
            .filter(Notification.is_read == False) \
            .filter(Notification.recipient_id == user.id)

        if cursor and cursor.after:
            query = query.filter(func.round(cast(func.extract('EPOCH', Notification.created_at), Numeric), 3) < func.round(
                cursor.get_after_as_float(), 3))

        if cursor and cursor.before:
            query = query.filter(func.round(cast(func.extract('EPOCH', Notification.created_at), Numeric), 3) > func.round(
                cursor.get_before_as_float(), 3))

        notifications = query.order_by(Notification.created_at.desc()).limit(cursor.limit).all()

        if notifications:
            cursor.set_before(notifications[0].created_at)
            cursor.set_after(notifications[-1].created_at)
        else:
            cursor.set_before(None)
            cursor.set_after(None)

        return notifications

    @staticmethod
    def get_all_notifications(user, cursor):
        query = db.session.query(Notification).filter(Notification.recipient_id == user.id)

        if cursor and cursor.after:
            query = query.filter(func.round(cast(func.extract('EPOCH', Notification.created_at), Numeric), 3) < func.round(
                cursor.get_after_as_float(), 3))

        if cursor and cursor.before:
            query = query.filter(func.round(cast(func.extract('EPOCH', Notification.created_at), Numeric), 3) > func.round(
                cursor.get_before_as_float(), 3))

        notifications = query.order_by(Notification.created_at.desc()).limit(cursor.limit).all()
        if notifications:
            cursor.set_before(notifications[0].created_at)
            cursor.set_after(notifications[-1].created_at)
        else:
            cursor.set_before(None)
            cursor.set_after(None)

        return notifications

    @staticmethod
    def get_read_notifications(user, cursor=None):
        query = db.session.query(Notification) \
            .filter(Notification.recipient_id == user.id) \
            .filter(Notification.is_read == True)

        if cursor and cursor.after:
            query = query.filter(func.round(cast(func.extract('EPOCH', Notification.created_at), Numeric), 3) < func.round(
                cursor.get_after_as_float(), 3))

        if cursor and cursor.before:
            query = query.filter(func.round(cast(func.extract('EPOCH', Notification.created_at), Numeric), 3) > func.round(
                cursor.get_before_as_float(), 3))

        notifications = query.order_by(Notification.created_at.desc()).limit(cursor.limit).all()
        if notifications:
            cursor.set_before(notifications[0].created_at)
            cursor.set_after(notifications[-1].created_at)
        else:
            cursor.set_before(None)
            cursor.set_after(None)

        return notifications

    @staticmethod
    def get_total_notifications(user):
        return db.session.query(Notification) \
            .filter(Notification.recipient_id == user.id) \
            .count()

    @staticmethod
    def get_total_unread_notifications(user):
        return db.session.query(Notification) \
            .filter(Notification.recipient_id == user.id) \
            .filter(Notification.is_read == False) \
            .count()

    @staticmethod
    def get_total_read_notifications(user):
        return db.session.query(Notification) \
            .filter(Notification.recipient_id == user.id) \
            .filter(Notification.is_read == True) \
            .count()

    def mark_as_read(self):
        self.is_read = True
        db.session.commit()

    @staticmethod
    def get_notification(notification_id):
        return db.session.query(Notification).filter(Notification.id==notification_id).first()

    @staticmethod
    def get_notifications(notification_ids):
        return db.session.query(Notification).filter(Notification.id.in_(notification_ids)).all()