from sqlalchemy.orm import load_only, joinedload
from sqlalchemy import func

from api.repositories.base import Repository

from api.models.event import (EventReview, EventReviewUpvote, EventReviewDownvote)

from api.repositories import exceptions
from api.repositories.event import EventRepository
from api.repositories.event_review_comment import EventReviewCommentRepository

event_repo = EventRepository()
event_review_comment_repo = EventReviewCommentRepository()


class EventReviewRepository(Repository):

    def add_review(self, review):
        if not event_repo.has_event(review.event_id):
            raise exceptions.EventNotFound()

        event = self.get_event_only(review.event_id)
        event.reviews += [review]
        self.session.commit()

    def update_review(self, review=None):
        self.session.commit()

    def remove_review(self, event_id, review_id):
        self.session.query(EventReview)\
            .filter(EventReview.event_id==event_id)\
            .filter(EventReview.review_id==review_id)\
            .delete()

    def has_review(self, review_id):
        count = self.session.query(EventReview)\
            .filter(EventReview.id==review_id)\
            .count()
        return bool(count)

    def get_review_only(self, review_id):
        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()

        return self.session.query(EventReview)\
            .filter(EventReview.id==review_id)\
            .first()

    def get_review(self, review_id):
        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()

        return self.session.query(EventReview).options(
            joinedload(EventReview.author),
            joinedload(EventReview.media),
            joinedload(EventReview.upvotes),
            joinedload(EventReview.downvotes)
        ).filter(EventReview.id == review_id).first()

    def get_reviews(self, event_id):
        if not self.has_event(event_id):
            raise exceptions.EventNotFound()

        return self.session.query(EventReview).options(
            joinedload(EventReview.author),
            joinedload(EventReview.media),
            joinedload(EventReview.upvotes),
            joinedload(EventReview.downvotes),
            joinedload(EventReview.comments),
        ).all()

    def has_upvoted_review(self, review_id, author_id):
        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()

        count = self.session.query(EventReviewUpvote)\
            .filter(EventReviewUpvote.review_id==review_id)\
            .filter(EventReviewUpvote.author_id==author_id).count()
        return bool(count)

    def add_review_upvote(self, review_id, upvote):
        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()

        if self.has_upvoted_review(review_id=review_id, author_id=upvote.author.id):
            raise exceptions.AlreadyDownvoted()

        if self.has_downvoted_review(review_id=review_id, author_id=upvote.author.id):
            raise exceptions.AlreadyDownvoted()

        review = self.get_review_only(review_id)
        review.upvotes += [upvote]
        self.session.commit()

    def remove_review_upvote(self, review_id, author_id):
        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()

        self.session.query(EventReviewUpvote)\
            .filter(EventReviewUpvote.review_id==review_id)\
            .filter(EventReviewUpvote.author_id==author_id)\
            .delete()

    def has_downvoted_review(self, review_id, author_id):
        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()

        count = self.session.query(EventReviewDownvote)\
            .filter(EventReviewDownvote.review_id == review_id)\
            .filter(EventReviewDownvote.author_id == author_id)\
            .count()
        return bool(count)

    def add_review_downvote(self, review_id, downvote):
        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()

        if self.has_downvoted_review(review_id, downvote.author.id):
            raise exceptions.AlreadyDownvoted()

        if self.has_upvoted_review(review_id, downvote.author.id):
            raise exceptions.AlreadyDownvoted()

        review = self.get_review_only(review_id)
        review.downvotes += [downvote]
        self.session.commit()

    def remove_review_downvote(self, review_id, author_id):
        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()

        self.session.query(EventReviewDownvote)\
            .filter(EventReviewDownvote.review_id==review_id)\
            .filter(EventReviewDownvote.author_id==author_id)\
            .delete()


