from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from api.repositories.base import Repository
from api.repositories import exceptions
from api.models.event import User, UserPaymentDetails, UserFollower, UserLoginSession


class UserRepository(Repository):

    def has_user(self, user_id):
        user = self.session.query(User).filter(User.id==user_id).first()
        return user

    def has_email(self, email):
        count = self.session.query(User).filter(User.email==email).count()
        return bool(count)

    def has_email_n_password(self, email, password):
        count = self.session.query(User).filter(User.email==email).filter(User.password==password).count()
        return bool(count)

    def add_user(self, user):
        if self.has_email(user.email):
            raise exceptions.UserAlreadyExists()

        self.session.add(user)
        self.session.commit()

    def update(self):
        self.session.commit()

    def get_user(self, user_id):
        return self.has_user(user_id)

    def get_user_by_email(self, email):
        return self.session.query(User).filter(User.email==email).one()

    def get_user_full(self, user_id):
        if not self.has_user(user_id):
            raise exceptions.UserNotFound()

        user = self.session.query(User).options(
                joinedload(User.events),
                joinedload(User.bookmarks)
        ).filter(User.id==user_id).first()

        return user

    def get_users(self):
        users = self.session.query(User).filter(User.is_ghost==False).all()
        return users

    def find_users_by_searchterm(self, searchterm=None):
        if searchterm is None:
            return []
        searchterm = '%' + searchterm + '%'
        users = self.session.query(User)\
                    .filter(User.is_ghost==False)\
                    .filter(or_(User.name.ilike(searchterm), User.email.ilike(searchterm)))\
                    .all()
        return users

    def create_ghost_user(self, email):
        user = User(email=email, is_ghost=True)
        self.session.add(user)
        self.session.commit()
        return user

    def has_payment_details(self, user_id):
        count = self.session.query(UserPaymentDetails).filter(UserPaymentDetails.user_id==user_id).count()
        return bool(count)

    def get_user_payment_details(self, user_id):
        return self.session.query(UserPaymentDetails).filter(UserPaymentDetails.user_id==user_id).first()

    def add_user_payment_details(self, user, payment_details):
        user.payment_details += [payment_details]
        self.session.commit()
        return self.get_user_payment_details(user.id)

    def has_followers(self, user_id):
        count = self.session.query(UserFollower).filter(UserFollower.user_id==user_id).count()
        return bool(count)

    def get_user_followers(self, user_id):
        followers = self.session.query(User).filter(User.id.in_(
                self.session.query(UserFollower.follower_id).filter(UserFollower.user_id == user_id).subquery()
        )).all()
        return followers

    def get_user_followings(self, user_id):
        followings = self.session.query(User).filter(User.id.in_(
                self.session.query(UserFollower.user_id).filter(UserFollower.follower_id == user_id).subquery()
        )).all()

        return followings

    def get_total_user_followings_count(self, user_id):
        return self.session.query(UserFollower.user_id).filter(UserFollower.follower_id == user_id).count()

    def get_total_user_followers_count(self, user_id):
        return self.session.query(UserFollower.follower_id).filter(UserFollower.user_id == user_id).count()


    def has_user_login_session(self, user_id):
        count = self.session.query(UserLoginSession).filter(UserLoginSession.user_id==user_id).count()
        return bool(count)

    def get_user_login_session(self, user_id):
        return self.session.query(UserLoginSession).filter(UserLoginSession.user_id==user_id).first()

    def remove_user_login_sessions(self, user_id):
        self.session.query(UserLoginSession).filter(UserLoginSession.user_id==user_id).delete()
        self.session.commit()


