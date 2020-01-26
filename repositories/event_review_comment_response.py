from sqlalchemy.orm import load_only, joinedload


from api.repositories import exceptions
from api.repositories.base import Repository
from api.repositories.event_review_comment import EventReviewCommentRepository
from api.models.event import (EventReviewCommentResponse, EventReviewCommentResponseDownvote, EventReviewCommentResponseUpvote)

event_review_comment_repo = EventReviewCommentRepository()


class EventReviewCommentResponseRepository(Repository):

    def has_review_comment_response(self, response_id):
        count = self.session.query(EventReviewCommentResponse) \
            .filter(EventReviewCommentResponse.id == response_id) \
            .count()
        return bool(count)

    def add_review_comment_response(self, comment_id, response):
        if not event_review_comment_repo.has_comment(comment_id):
            raise exceptions.EventReviewCommentResponseNotFound()

        comment = self.get_review_comment_only(comment_id)
        comment.responses += [response]
        self.session.commit()

    def remove_review_comment_response(self, comment_id, response_id):
        if not self.has_review_comment_response(response_id):
            raise exceptions.EventReviewCommentResponseNotFound()

        if not event_review_comment_repo.has_comment(comment_id):
            raise exceptions.ReviewCommentNotFound()

        self.session.query(EventReviewCommentResponse) \
            .filter(EventReviewCommentResponse.id == response_id) \
            .delete()

    def get_review_comment_response_only(self, response_id):

        if not self.has_review_comment_response(response_id):
            raise exceptions.EventReviewCommentResponseNotFound()

        return self.session.query(EventReviewCommentResponse) \
            .filter(EventReviewCommentResponse.id == response_id) \
            .first()

    def get_review_comment_response(self, response_id):

        if not self.has_review_comment_response(response_id):
            raise exceptions.EventReviewCommentResponseNotFound()

        return self.session.query(EventReviewCommentResponse).options(
            joinedload(EventReviewCommentResponse.upvotes),
            joinedload(EventReviewCommentResponse.downvotes),
            joinedload(EventReviewCommentResponse.author),
            joinedload(EventReviewCommentResponse.media)
        ).filter(EventReviewCommentResponse.id == response_id) \
            .first()

    def get_review_comment_responses(self, comment_id):
        if not event_review_comment_repo.has_comment(comment_id):
            raise exceptions.ReviewCommentNotFound()

        return self.session.query(EventReviewCommentResponse).options(
            joinedload(EventReviewCommentResponse.upvotes),
            joinedload(EventReviewCommentResponse.downvotes),
            joinedload(EventReviewCommentResponse.author),
            joinedload(EventReviewCommentResponse.media)
        ).filter(EventReviewCommentResponse.comment_id == comment_id) \
            .all()

    def add_review_comment_response_upvote(self, response_id, upvote):
        if not self.has_review_comment_response(response_id):
            raise exceptions.EventReviewCommentResponseNotFound()

        if self.has_upvoted_review_comment_response(response_id, upvote.author.id):
            raise exceptions.AlreadyDownvoted()

        if self.has_downvoted_review_comment_response(response_id, upvote.author.id):
            raise exceptions.AlreadyDownvoted()

        response = self.get_review_comment_response(response_id)
        response.upvotes += [upvote]
        self.session.commit()

    def add_review_comment_response_downvote(self, response_id, downvote):
        if not self.has_review_comment_response(response_id):
            raise exceptions.EventReviewCommentResponseNotFound()

        if self.has_upvoted_review_comment_response(response_id, downvote.author.id):
            raise exceptions.AlreadyDownvoted()

        if self.has_downvoted_review_comment_response(response_id, downvote.author.id):
            raise exceptions.AlreadyDownvoted()

        response = self.get_review_comment_response(response_id)
        response.downvotes += [downvote]
        self.session.commit()

    def remove_review_comment_response_upvote(self, response_id, author_id):
        if not self.has_review_comment_response(response_id):
            raise exceptions.EventReviewCommentResponseNotFound()

        self.session.query(EventReviewCommentResponseUpvote) \
            .filter(EventReviewCommentResponseUpvote.response_id == response_id) \
            .filter(EventReviewCommentResponseUpvote.author_id == author_id) \
            .delete()

    def remove_review_comment_response_downvote(self, response_id, author_id):
        if not self.has_review_comment_response(response_id):
            raise exceptions.EventReviewCommentResponseNotFound()

        self.session.query(EventReviewCommentResponseDownvote) \
            .filter(EventReviewCommentResponseDownvote.response_id == response_id) \
            .filter(EventReviewCommentResponseDownvote.author_id == author_id) \
            .delete()

    def has_downvoted_review_comment_response(self, response_id, author_id):
        if not self.has_review_comment_response(response_id):
            raise exceptions.EventReviewCommentResponseNotFound()

        count = self.session.query(EventReviewCommentResponseDownvote) \
            .filter(EventReviewCommentResponseDownvote.id == response_id) \
            .filter(EventReviewCommentResponseDownvote.author_id == author_id) \
            .count()
        return bool(count)

    def has_upvoted_review_comment_response(self, response_id, author_id):
        if not self.has_review_comment_response(response_id):
            raise exceptions.EventReviewCommentResponseNotFound()

        count = self.session.query(EventReviewCommentResponseUpvote) \
            .filter(EventReviewCommentResponseUpvote.response_id == response_id) \
            .filter(EventReviewCommentResponseUpvote.author_id == author_id) \
            .count()

        return bool(count)

