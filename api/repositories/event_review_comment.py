from sqlalchemy.orm import load_only, joinedload

from api.repositories.base import Repository
from api.repositories.event import EventRepository

from api.models.event import (EventReviewComment, EventReviewCommentUpvote, EventReviewCommentDownvote,
                              EventReviewCommentResponse, EventReviewCommentResponseUpvote,
                              EventReviewCommentResponseDownvote )
from api.repositories.event_review_comment_response import EventReviewCommentResponseRepository

from api.repositories import exceptions


event_repo = EventRepository()
event_review_comment_response_repo = EventReviewCommentResponseRepository()


class EventReviewCommentRepository(Repository):

    def has_review_comment(self, review_id, comment_id):
        count = self.session.query(EventReviewComment)\
            .filter(EventReviewComment.id==comment_id)\
            .filter(EventReviewComment.review_id==review_id)\
            .count()
        return bool(count)

    def add_review_comment(self, review_id, comment):
        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()

        review = self.get_review_only(review_id)
        review.comments += [comment]
        self.session.commit()

    def remove_review_comment(self, review_id, comment_id):
        if not self.has_review_comment(comment_id):
            raise exceptions.ReviewCommentNotFound()
        self.session.query(EventReviewComment).filter(EventReviewComment.id==comment_id).delete()

    def get_review_comment_only(self, comment_id):
        if not self.has_review_comment(comment_id):
            raise exceptions.ReviewCommentNotFound()

        return self.session.query(EventReviewComment)\
            .filter(EventReviewComment.id==comment_id) \
            .first()

    def get_review_comment(self, review_id, comment_id):
        if not self.has_review_comment(comment_id):
            raise exceptions.ReviewCommentNotFound()

        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()

        return self.session.query(EventReviewComment).options(
            joinedload(EventReviewComment.upvotes),
            joinedload(EventReviewComment.downvotes),
            joinedload(EventReviewComment.author),
            joinedload(EventReviewComment.media)
        ).filter(EventReviewComment.review_id==review_id) \
         .filter(EventReviewComment.id==comment_id) \
         .first()

    def get_review_comments(self, review_id):
        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()

        return self.session.query(EventReviewComment).options(
            joinedload(EventReviewComment.upvotes),
            joinedload(EventReviewComment.downvotes),
            joinedload(EventReviewComment.author),
            joinedload(EventReviewComment.media)
        ).filter(EventReviewComment.review_id==review_id) \
         .all()

    def add_review_comment_upvote(self, review_id, comment_id, upvote):
        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()

        if self.has_upvoted_review_comment(review_id=review_id, comment_id=comment_id, author_id=upvote.author.id):
            raise exceptions.AlreadyDownvoted()

        if self.has_downvoted_review_comment(review_id=review_id, comment_id=comment_id, author_id=upvote.author.id):
            raise exceptions.AlreadyDownvoted()

        comment = self.get_review_comment(review_id, comment_id)
        comment.upvotes += [upvote]
        self.session.commit()

    def add_review_comment_downvote(self, review_id, comment_id, downvote):
        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()

        if self.has_upvoted_review_comment(review_id, comment_id, downvote.author.id):
            raise exceptions.AlreadyDownvoted()

        if self.has_downvoted_review_comment(review_id=review_id, comment_id=comment_id, author_id=downvote.author.id):
            raise exceptions.AlreadyDownvoted()

        comment = self.get_review_comment(review_id, comment_id)
        comment.downvotes += [downvote]
        self.session.commit()

    def remove_review_comment_upvote(self, review_id, comment_id, author_id):
        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()

        if not self.has_review_comment(comment_id):
            raise exceptions.ReviewCommentNotFound()

        self.session.query(EventReviewCommentUpvote)\
            .filter(EventReviewCommentUpvote.comment_id == comment_id)\
            .filter(EventReviewCommentUpvote.author_id == author_id)\
            .delete()

    def remove_review_comment_downvote(self, review_id, comment_id, author_id):
        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()

        if not self.has_review_comment(comment_id):
            raise exceptions.ReviewCommentNotFound()

        self.session.query(EventReviewCommentDownvote) \
            .filter(EventReviewCommentDownvote.comment_id == comment_id) \
            .filter(EventReviewCommentDownvote.author_id == author_id)\
            .delete()

    def has_downvoted_review_comment(self, review_id, comment_id, author_id):
        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()

        if not self.has_review_comment(comment_id):
            raise exceptions.ReviewCommentNotFound()

        count = self.session.query(EventReviewCommentDownvote)\
            .filter(EventReviewCommentDownvote.comment_id == comment_id)\
            .filter(EventReviewCommentDownvote.author_id == author_id)\
            .count()
        return bool(count)

    def has_upvoted_review_comment(self, review_id, comment_id, author_id):
        if not self.has_review(review_id):
            raise exceptions.EventReviewNotFound()

        if not self.has_review_comment(comment_id):
            raise exceptions.ReviewCommentNotFound()

        count = self.session.query(EventReviewCommentUpvote)\
            .filter(EventReviewCommentUpvote.comment_id == comment_id)\
            .filter(EventReviewCommentUpvote.author_id == author_id)\
            .count()
        return bool(count)