from sqlalchemy.orm import load_only, joinedload
from sqlalchemy import func, or_
from sqlalchemy.types import INTEGER


from api.repositories.base import Repository
from api.repositories.ticket import TicketRepository as TicketTypeRepository
from api.repositories.brand import BrandRepository
from api.repositories.ticket import TicketTypeNotFound
from api.models.event_periods import EventPeriods
from api.models.event import (Event, EventRecommendation, EventSpeaker, EventBookmark, EventTicketType,
                              EventTicketDiscount, EventReview, EventReviewUpvote, EventReviewDownvote,
                              EventReviewCommentResponse, EventReviewCommentResponseUpvote, EventReviewCommentResponseDownvote,
                              EventReviewCommentResponseMedia, EventReviewComment, EventReviewCommentDownvote, EventReviewCommentUpvote,
                              EventReviewCommentMedia, EventSponsor,
                              EventTicketSaleOrder, EventTicketSaleLine, EventTicketTypeAssignment,
                              EventCategory, User

                              )

from api.repositories import exceptions

brand_repo = BrandRepository()


class EventRepository(Repository):

    def update(self, event):
        self.session.commit()

    def get_ticket_type_repository(self):
        return TicketTypeRepository().set_session(self.session)

    def get_events_summary(self, category_id=None, period=None, limit=None):

        query = self.query(Event)
            # .options(
            #     load_only('id', 'name', 'start_datetime'),
        # )

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
                query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))

        if category_id:
            query = query.filter(Event.category_id==category_id)

        if self.cursor and self.cursor.after:
            query = query.filter(func.extract('EPOCH', Event.created_at) > self.cursor.get_after_as_float())

        query = query.order_by(Event.created_at.asc())
        if limit or self.cursor and self.cursor.limit:
            limit = limit or self.cursor.limit
            query = query.limit(limit)

        events = query.all()
        if events:
            self.cursor.set_next_after(events[-1].created_at)
        return events

    def get_events(self, period=None, category_id=None, creator_id=None, limit=None):
        query = self.query(Event).options(
                joinedload(Event.recommendations),
                joinedload(Event.organizers),
                joinedload(Event.user),
                joinedload(Event.category),
                joinedload(Event.ticket_types),
                joinedload(Event.contact_info),
                joinedload(Event.speakers),
                joinedload(Event.media),
        )

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
            query = query.filter(Event.user_id==creator_id)

        if category_id:
            query = query.filter(Event.category_id==category_id)

        if self.cursor and self.cursor.after:
            query = query.filter(func.extract('EPOCH', Event.created_at) > self.cursor.after)

        if limit or self.cursor and self.cursor.limit:
            limit = limit or self.cursor.limit
            query = query.order_by(Event.created_at).limit(limit)

        events = query.all()
        if events:
            self.cursor.set_next_after(events[-1].created_at)
        return events

    def get_event_only(self, event_id):
        event = self.session.query(Event).filter(Event.id==event_id).first()
        return event

    def get_event(self, event_id):
        event = self.query(Event).options(
                joinedload(Event.recommendations),
                joinedload(Event.organizers),
                joinedload(Event.user),
                joinedload(Event.category),
                joinedload(Event.ticket_types),
                joinedload(Event.contact_info),
                joinedload(Event.speakers),
                joinedload(Event.media),
        ).filter_by(id=event_id).first()
        return event

    def get_event_summary(self, event_id):
        return self.query(Event).options(
                load_only('id', 'name', 'start_datetime', 'organizers'),
                joinedload('ticket_types')
        ).filter_by(id=event_id).first()

    def update_event(self, event_id=None, data=None):
        if data:
            self.query(Event).filter_by(id=event_id).update(data)
        self.session.commit()

    def has_event(self, event_id):
        return self.query(Event).filter_by(id=event_id).first()

    def remove_event(self, event_id):
        is_deleted = self.query(Event).filter_by(id=event_id).delete()
        self.session.commit()
        return is_deleted

    def add_event(self, event):
        self.session.add(event)
        self.session.commit()
        return event

    def add_ticket_type(self, event_id, ticket_type):
        if self.has_event(event_id):
            print("eventID##", ticket_type.event_id)
            event = self.get_event(event_id)
            event.ticket_types.append(ticket_type)
            self.session.commit()

    def remove_ticket_type(self, event_id, ticket_type_id):
        if not self.has_event(event_id):
            raise exceptions.EventNotFound()

        if not self.get_ticket_type_repository().has_ticket_type(ticket_type_id):
            raise TicketTypeNotFound()


    def get_ticket_types(self, event_id):
        if not self.has_event(event_id):
            raise exceptions.EventNotFound()
        return self.query(EventTicketType).filter(EventTicketType.event_id==event_id).all()

    def get_ticket_type_discount(self, event_id, ticket_type_id, discount_id):
        if not self.has_event(event_id):
            raise exceptions.EventNotFound()

        if not self.get_ticket_type_repository().has_ticket_type(ticket_type_id):
            raise TicketTypeNotFound()

        if not self.has_tickt_type_discount(event_id, ticket_type_id, discount_id):
            raise exceptions.TicketDiscountNotFound()

        return self.query(EventTicketDiscount).filter(EventTicketDiscount.id==discount_id, EventTicketDiscount.ticket_type_id==ticket_type_id).first()

    def has_tickt_type_discount(self, event_id, ticket_type_id, discount_id):
        discount = self.query(EventTicketDiscount).filter(EventTicketDiscount.id==discount_id, EventTicketDiscount.ticket_type_id==ticket_type_id).first()
        return bool(discount)

    def get_ticket_type_discounts(self, event_id, ticket_type_id):
        if not self.has_event(event_id):
            raise exceptions.EventNotFound()

        if not self.get_ticket_type_repository().has_ticket_type(ticket_type_id):
            raise TicketTypeNotFound()

        return self.query(EventTicketDiscount).filter(EventTicketDiscount.ticket_type_id==ticket_type_id).all()

    def add_ticket_type_discounts(self, event_id, ticket_type_id, discount):
        if not self.has_event(event_id):
            raise exceptions.EventNotFound()

        if not self.get_ticket_type_repository().has_ticket_type(ticket_type_id):
            raise TicketTypeNotFound()

        ticket_type = self.get_ticket_type_repository().get_ticket_type(ticket_type_id)
        ticket_type.discounts.append(discount)
        # self.session.add(discount)
        self.session.add(ticket_type)
        self.session.commit()

    def remove_ticket_type_discount(self, event_id, ticket_type_id, discount_id):
        if not self.has_event(event_id):
            raise exceptions.EventNotFound()

        if not self.get_ticket_type_repository().has_ticket_type(ticket_type_id):
            raise TicketTypeNotFound()

        self.query(EventTicketDiscount).filter(EventTicketDiscount.id==discount_id).delete()
        self.session.commit()

    def update_ticket_type_discount(self, event_id, ticket_type_id, discount):
        self.session.add(discount)
        self.session.commit()

    def get_event_recommendations(self, event_id):
        recommendations = self.query(EventRecommendation).filter(EventRecommendation.event_id==event_id).all()
        return recommendations

    def add_event_recommendations(self, event, recommendations):
        if not isinstance(event, Event):
            event = self.has_event(event)
            if not event:
                raise exceptions.EventNotFound()

        event.recommendations.append(recommendations)
        self.session.commit()
        return recommendations

    def add_event_recommendation(self, event_id, recommendation):
        event = self.get_event_only(event_id)
        if not event:
            raise exceptions.EventNotFound()
        event.recommendations.append(recommendation)
        self.session.commit()

    def has_recommendation_for(self, event_id, recommended_by_id, search_term=None, recommended_to_id=None):
        query = self.session.query(EventRecommendation) \
            .filter(EventRecommendation.event_id==event_id)

        if search_term:
            query = query.filter(
                    or_(EventRecommendation.email == search_term, EventRecommendation.phone_number == search_term))
        elif recommended_to_id:
            query = query.filter(EventRecommendation.recommended_to_id == recommended_to_id)
        else:
            raise Exception("A searchterm or recommend_to_id is required")

        return query.filter(EventRecommendation.recommended_by_id==recommended_by_id) \
            .count()

    # def has_sponsor(self, event_id, sponsor_id=None):
    #     if not self.has_event(event_id):
    #         raise exceptions.EventNotFound()
    #
    #     count = self.session.query(EventSponsor).filter(EventSponsor.event_id==event_id).filter(EventSponsor.id==sponsor_id).count()
    #     return bool(count)
    #
    # def add_sponsor(self, event_id, sponsor):
    #     if not self.has_event(event_id):
    #         raise exceptions.EventNotFound()
    #
    #     event = self.get_event_only(event_id)
    #     event.sponsors += [sponsor]
    #     self.session.commit()
    #
    # def remove_sponsor(self, event_id, sponsor_id):
    #     if not self.has_event(event_id):
    #         raise exceptions.EventNotFound()
    #
    #     if not self.has_sponsor(sponsor_id):
    #         raise exceptions.EventSponsorNotFound()
    #
    #     self.session.query(EventSponsor).filter(EventSponsor.id==sponsor_id).filter(EventSponsor.event_id==event_id).delete()

    # def update_sponsor(self, event_id, sponsor):
    #     self.session.commit()
    #
    # def get_sponsors(self, event_id):
    #     if not self.has_event(event_id):
    #         raise exceptions.EventNotFound()
    #
    #     return self.session.query(EventSponsor).filter(EventSponsor.event_id==event_id).all()
    #
    # def get_sponsor(self, event_id, sponsor_id):
    #     if not self.has_event(event_id):
    #         raise exceptions.EventNotFound()
    #
    #     if not self.has_sponsor(sponsor_id):
    #         raise exceptions.EventSponsorNotFound()
    #
    #     return self.session.query(EventSponsor).filter(EventSponsor.event_id == event_id).filter(EventSponsor.id==sponsor_id).first()


    # def add_speaker(self, event_id, speaker):
    #     if not self.has_event(event_id):
    #         raise exceptions.EventNotFound()
    #
    #     print("speaker##", speaker.event_id)
    #     event = self.get_event(event_id)
    #     event.speakers.append(speaker)
    #     self.session.commit()
    #
    # def remove_speaker(self, event_id, speaker_id):
    #     if self.has_speaker(event_id, speaker_id):
    #         self.session.query(EventSpeaker).filter(EventSpeaker.event_id==event_id).filter(EventSpeaker.id==speaker_id).delete()
    #         self.session.commit()
    #     else:
    #         raise exceptions.EventSpeakerNotFound()
    #
    # def has_speaker(self, event_id, speaker_id):
    #     count = self.session.query(EventSpeaker).filter(EventSpeaker.event_id==event_id).filter(EventSpeaker.id==speaker_id).count()
    #     return count
    #
    # def get_speaker(self, event_id, speaker_id):
    #     return self.session.query(EventSpeaker).filter(EventSpeaker.event_id==event_id).filter(EventSpeaker.id==speaker_id).first()
    #
    # def get_speakers(self, event_id):
    #     if not self.has_event(event_id):
    #         raise exceptions.EventNotFound()
    #
    #     speakers = self.session.query(EventSpeaker).filter(EventSpeaker.event_id==event_id).all()
    #     return speakers

    # def add_bookmark(self, event_id, bookmark):
    #     event = self.get_event(event_id)
    #     if not event:
    #         raise exceptions.EventNotFound()
    #
    #     if self.event_bookmarked_by_user(event_id, bookmark.user.id):
    #         raise exceptions.BookmarkAlreadyExist()
    #
    #     event.bookmarks += [bookmark]
    #     self.session.commit()
    #
    # def remove_bookmark(self, event_id, user_id):
    #     if not self.event_bookmarked_by_user(event_id, user_id):
    #         raise exceptions.BookmarkNotFound()
    #     self.session.query(EventBookmark).filter(EventBookmark.user_id==user_id).filter(EventBookmark.event_id==event_id).delete()
    #     self.session.commit()
    #
    # def event_bookmarked_by_user(self, event_id, user_id):
    #     event = self.get_event(event_id)
    #     if not event:
    #         raise exceptions.EventNotFound()
    #     count = self.session.query(EventBookmark).filter(EventBookmark.user_id==user_id).filter(EventBookmark.event_id==event_id).count()
    #     return bool(count)
    #
    # def get_bookmarks(self, event_id):
    #     event = self.get_event(event_id)
    #     if not event:
    #         raise exceptions.EventNotFound()
    #     bookmarks = self.session.query(EventBookmark).filter(EventBookmark.event_id==event_id)
    #     return bookmarks
    #
    # def get_events_bookmarked_by_user(self, user_id):
    #     events = self.session.query(Event).filter(Event.bookmarks.any(EventBookmark.user_id==user_id)).all()
    #     return events
    #
    # def get_total_events_bookmarked_by_user(self, user_id):
    #     count = self.session.query(Event).filter(Event.bookmarks.any(EventBookmark.user_id==user_id)).count()
    #     return count

    def update_is_shareable_during_event_status(self, event_id, status):
        event = self.get_event(event_id)
        if not event:
            raise exceptions.EventNotFound()

        event.is_shareable_during_event = status
        self.session.commit()

    def update_is_shareable_after_event_status(self, event_id, status):
        event = self.has_event(event_id)
        if not event:
            raise exceptions.EventNotFound()

        event.is_shareable_after_event = status
        self.session.commit()

    # def add_review(self, event_id, review):
    #     if not self.has_event(event_id):
    #         raise exceptions.EventNotFound()
    #
    #     event = self.get_event_only(event_id)
    #     event.reviews.append(review)
    #     self.session.commit()
    #
    # def update_review(self, review=None):
    #     self.session.commit()
    #
    # def remove_review(self, event_id, review_id):
    #     self.session.query(EventReview) \
    #         .filter(EventReview.event_id == event_id) \
    #         .filter(EventReview.review_id == review_id) \
    #         .delete()
    #
    # def has_review(self, review_id):
    #     count = self.session.query(EventReview) \
    #         .filter(EventReview.id == review_id) \
    #         .count()
    #     return bool(count)
    #
    # def get_total_event_reviews(self, event_id):
    #     return self.session.query(EventReview).filter(EventReview.event_id==event_id).count()
    #
    # def get_review_only(self, review_id):
    #     if not self.has_review(review_id):
    #         raise exceptions.EventReviewNotFound()
    #
    #     return self.session.query(EventReview) \
    #         .filter(EventReview.id == review_id) \
    #         .first()
    #
    # def get_review(self, review_id):
    #     if not self.has_review(review_id):
    #         raise exceptions.EventReviewNotFound()
    #
    #     return self.session.query(EventReview).options(
    #             joinedload(EventReview.author),
    #             joinedload(EventReview.media),
    #             joinedload(EventReview.upvotes),
    #             joinedload(EventReview.downvotes)
    #     ).filter(EventReview.id == review_id).first()
    #
    # def get_reviews(self, event_id):
    #     if not self.has_event(event_id):
    #         raise exceptions.EventNotFound()
    #
    #     return self.session.query(EventReview).options(
    #             joinedload(EventReview.author),
    #             joinedload(EventReview.media),
    #             joinedload(EventReview.upvotes),
    #             joinedload(EventReview.downvotes),
    #             joinedload(EventReview.comments),
    #             joinedload(EventReview.event),
    #     ).filter(EventReview.event_id==event_id).all()

    # def has_upvoted_review(self, review_id, author_id):
    #     if not self.has_review(review_id):
    #         raise exceptions.EventReviewNotFound()
    #
    #     count = self.session.query(EventReviewUpvote) \
    #         .filter(EventReviewUpvote.review_id == review_id) \
    #         .filter(EventReviewUpvote.author_id == author_id) \
    #         .count()
    #     return bool(count)
    #
    # def add_review_upvote(self, review_id, upvote):
    #     if not self.has_review(review_id):
    #         raise exceptions.EventReviewNotFound()
    #
    #     if self.has_upvoted_review(review_id=review_id, author_id=upvote.author.id):
    #         raise exceptions.AlreadyUpvoted()
    #
    #     if self.has_downvoted_review(review_id=review_id, author_id=upvote.author.id):
    #         raise exceptions.AlreadyDownvoted()
    #
    #     review = self.get_review_only(review_id)
    #     review.upvotes.append(upvote)
    #     self.session.commit()
    #
    # def remove_review_upvote(self, review_id, author_id):
    #     if not self.has_review(review_id):
    #         raise exceptions.EventReviewNotFound()
    #
    #     self.session.query(EventReviewUpvote) \
    #         .filter(EventReviewUpvote.review_id == review_id) \
    #         .filter(EventReviewUpvote.author_id == author_id) \
    #         .delete()
    #
    # def has_downvoted_review(self, review_id, author_id):
    #     if not self.has_review(review_id):
    #         raise exceptions.EventReviewNotFound()
    #
    #     count = self.session.query(EventReviewDownvote) \
    #         .filter(EventReviewDownvote.review_id == review_id) \
    #         .filter(EventReviewDownvote.author_id == author_id) \
    #         .count()
    #     return bool(count)
    #
    # def add_review_downvote(self, review_id, downvote):
    #     if not self.has_review(review_id):
    #         raise exceptions.EventReviewNotFound()
    #
    #     if self.has_downvoted_review(review_id, downvote.author.id):
    #         raise exceptions.AlreadyDownvoted()
    #
    #     if self.has_upvoted_review(review_id, downvote.author.id):
    #         raise exceptions.AlreadyUpvoted()
    #
    #     review = self.get_review_only(review_id)
    #     review.downvotes += [downvote]
    #     self.session.commit()
    #
    # def remove_review_downvote(self, review_id, author_id):
    #     if not self.has_review(review_id):
    #         raise exceptions.EventReviewNotFound()
    #
    #     self.session.query(EventReviewDownvote) \
    #         .filter(EventReviewDownvote.review_id == review_id) \
    #         .filter(EventReviewDownvote.author_id == author_id) \
    #         .delete()
    #
    # def has_review_comment(self, review_id, comment_id):
    #     count = self.session.query(EventReviewComment) \
    #         .filter(EventReviewComment.id == comment_id) \
    #         .filter(EventReviewComment.review_id == review_id) \
    #         .count()
    #
    #     return bool(count)
    #
    # def add_review_comment(self, review_id, comment):
    #     if not self.has_review(review_id):
    #         raise exceptions.EventReviewNotFound()
    #
    #     review = self.get_review_only(review_id)
    #     review.comments += [comment]
    #     self.session.commit()
    #
    # def remove_review_comment(self, review_id, comment_id):
    #     if not self.has_review_comment(review_id, comment_id):
    #         raise exceptions.ReviewCommentNotFound()
    #     self.session.query(EventReviewComment).filter(EventReviewComment.id == comment_id).delete()
    #
    # def get_total_event_review_comments(self, review_id):
    #     return self.session.query(EventReviewComment) \
    #         .filter(EventReviewComment.review_id == review_id) \
    #         .count()
    #
    # def get_review_comment_only(self, comment_id):
    #
    #     return self.session.query(EventReviewComment) \
    #         .filter(EventReviewComment.id == comment_id) \
    #         .first()
    #
    # def get_review_comment(self, review_id, comment_id):
    #     if not self.has_review_comment(review_id, comment_id):
    #         raise exceptions.ReviewCommentNotFound()
    #
    #     if not self.has_review(review_id):
    #         raise exceptions.EventReviewNotFound()
    #
    #     return self.session.query(EventReviewComment).options(
    #             joinedload(EventReviewComment.upvotes),
    #             joinedload(EventReviewComment.downvotes),
    #             joinedload(EventReviewComment.author),
    #             joinedload(EventReviewComment.media)
    #     ).filter(EventReviewComment.review_id == review_id) \
    #         .filter(EventReviewComment.id == comment_id) \
    #         .first()
    #
    # def get_review_comments(self, review_id):
    #     if not self.has_review(review_id):
    #         raise exceptions.EventReviewNotFound()
    #
    #     return self.session.query(EventReviewComment).options(
    #             joinedload(EventReviewComment.upvotes),
    #             joinedload(EventReviewComment.downvotes),
    #             joinedload(EventReviewComment.author),
    #             joinedload(EventReviewComment.media)
    #     ).filter(EventReviewComment.review_id == review_id) \
    #         .all()

    # def add_review_comment_upvote(self, review_id, comment_id, upvote):
    #     if not self.has_review(review_id):
    #         raise exceptions.EventReviewNotFound()
    #
    #     if self.has_upvoted_review_comment(review_id=review_id, comment_id=comment_id, author_id=upvote.author.id):
    #         raise exceptions.AlreadyUpvoted()
    #
    #     if self.has_downvoted_review_comment(review_id=review_id, comment_id=comment_id, author_id=upvote.author.id):
    #         raise exceptions.AlreadyDownvoted()
    #
    #     comment = self.get_review_comment_only(comment_id)
    #     comment.upvotes += [upvote]
    #     self.session.commit()
    #
    # def add_review_comment_downvote(self, review_id, comment_id, downvote):
    #     if not self.has_review(review_id):
    #         raise exceptions.EventReviewNotFound()
    #
    #     if self.has_upvoted_review_comment(review_id, comment_id, downvote.author.id):
    #         raise exceptions.AlreadyUpvoted()
    #
    #     if self.has_downvoted_review_comment(review_id=review_id, comment_id=comment_id, author_id=downvote.author.id):
    #         raise exceptions.AlreadyDownvoted()
    #
    #     comment = self.get_review_comment(review_id, comment_id)
    #     comment.downvotes += [downvote]
    #     self.session.commit()
    #
    # def remove_review_comment_upvote(self, review_id, comment_id, author_id):
    #     if not self.has_review(review_id):
    #         raise exceptions.EventReviewNotFound()
    #
    #     if not self.has_review_comment(review_id, comment_id):
    #         raise exceptions.ReviewCommentNotFound()
    #
    #     self.session.query(EventReviewCommentUpvote) \
    #         .filter(EventReviewCommentUpvote.comment_id == comment_id) \
    #         .filter(EventReviewCommentUpvote.author_id == author_id) \
    #         .delete()
    #
    # def remove_review_comment_downvote(self, review_id, comment_id, author_id):
    #     if not self.has_review(review_id):
    #         raise exceptions.EventReviewNotFound()
    #
    #     if not self.has_review_comment(review_id, comment_id):
    #         raise exceptions.ReviewCommentNotFound()
    #
    #     self.session.query(EventReviewCommentDownvote) \
    #         .filter(EventReviewCommentDownvote.comment_id == comment_id) \
    #         .filter(EventReviewCommentDownvote.author_id == author_id) \
    #         .delete()
    #
    # def has_downvoted_review_comment(self, review_id, comment_id, author_id):
    #     if not self.has_review(review_id):
    #         raise exceptions.EventReviewNotFound()
    #
    #     if not self.has_review_comment(review_id, comment_id):
    #         raise exceptions.ReviewCommentNotFound()
    #
    #     count = self.session.query(EventReviewCommentDownvote) \
    #         .filter(EventReviewCommentDownvote.comment_id == comment_id) \
    #         .filter(EventReviewCommentDownvote.author_id == author_id) \
    #         .count()
    #     return bool(count)
    #
    # def has_upvoted_review_comment(self, review_id, comment_id, author_id):
    #     if not self.has_review(review_id):
    #         raise exceptions.EventReviewNotFound()
    #
    #     if not self.has_review_comment(review_id, comment_id):
    #         raise exceptions.ReviewCommentNotFound()
    #
    #     count = self.session.query(EventReviewCommentUpvote) \
    #         .filter(EventReviewCommentUpvote.comment_id == comment_id) \
    #         .filter(EventReviewCommentUpvote.author_id == author_id) \
    #         .count()
    #     return bool(count)
    #
    # def has_review_comment_response(self, response_id):
    #     count = self.session.query(EventReviewCommentResponse) \
    #         .filter(EventReviewCommentResponse.id == response_id) \
    #         .count()
    #     return bool(count)
    #
    # def add_review_comment_response(self, comment_id, response):
    #
    #     comment = self.get_review_comment_only(comment_id)
    #     comment.responses += [response]
    #     self.session.commit()
    #
    # def remove_review_comment_response(self, comment_id, response_id):
    #     if not self.has_review_comment_response(response_id):
    #         raise exceptions.EventReviewCommentResponseNotFound()
    #
    #     if not self.has_review_comment(comment_id):
    #         raise exceptions.ReviewCommentNotFound()
    #
    #     self.session.query(EventReviewCommentResponse) \
    #         .filter(EventReviewCommentResponse.id == response_id) \
    #         .delete()
    #
    # def get_review_comment_response_only(self, response_id):
    #
    #     if not self.has_review_comment_response(response_id):
    #         raise exceptions.EventReviewCommentResponseNotFound()
    #
    #     return self.session.query(EventReviewCommentResponse) \
    #         .filter(EventReviewCommentResponse.id == response_id) \
    #         .first()
    #
    # def get_review_comment_response(self, response_id):
    #
    #     if not self.has_review_comment_response(response_id):
    #         raise exceptions.EventReviewCommentResponseNotFound()
    #
    #     return self.session.query(EventReviewCommentResponse).options(
    #             joinedload(EventReviewCommentResponse.upvotes),
    #             joinedload(EventReviewCommentResponse.downvotes),
    #             joinedload(EventReviewCommentResponse.author),
    #             joinedload(EventReviewCommentResponse.media)
    #     ).filter(EventReviewCommentResponse.id == response_id) \
    #         .first()
    #
    # def get_review_comment_responses(self, review_id, comment_id):
    #     if not self.has_review_comment(review_id, comment_id):
    #         raise exceptions.ReviewCommentNotFound()
    #
    #     return self.session.query(EventReviewCommentResponse).options(
    #             joinedload(EventReviewCommentResponse.upvotes),
    #             joinedload(EventReviewCommentResponse.downvotes),
    #             joinedload(EventReviewCommentResponse.author),
    #             joinedload(EventReviewCommentResponse.media)
    #     ).filter(EventReviewCommentResponse.comment_id == comment_id) \
    #         .all()
    #
    # def get_total_review_comment_responses(self, review_id, comment_id):
    #
    #     if not self.has_review_comment(review_id, comment_id):
    #         raise exceptions.ReviewCommentNotFound()
    #
    #     return self.session.query(EventReviewCommentResponse). \
    #         filter(EventReviewCommentResponse.comment_id==comment_id) \
    #         .count()
    #
    # def add_review_comment_response_upvote(self, response_id, upvote):
    #     if not self.has_review_comment_response(response_id):
    #         raise exceptions.EventReviewCommentResponseNotFound()
    #
    #     if self.has_upvoted_review_comment_response(response_id, upvote.author.id):
    #         raise exceptions.AlreadyUpvoted()
    #
    #     if self.has_downvoted_review_comment_response(response_id, upvote.author.id):
    #         raise exceptions.AlreadyDownvoted()
    #
    #     response = self.get_review_comment_response(response_id)
    #     response.upvotes += [upvote]
    #     self.session.commit()
    #
    # def add_review_comment_response_downvote(self, response_id, downvote):
    #
    #     if not self.has_review_comment_response(response_id):
    #         raise exceptions.EventReviewCommentResponseNotFound()
    #
    #     if self.has_upvoted_review_comment_response(response_id, downvote.author.id):
    #         raise exceptions.AlreadyUpvoted()
    #
    #     if self.has_downvoted_review_comment_response(response_id, downvote.author.id):
    #         raise exceptions.AlreadyDownvoted()
    #
    #     response = self.get_review_comment_response(response_id)
    #     response.downvotes += [downvote]
    #     self.session.commit()
    #
    # def remove_review_comment_response_upvote(self, response_id, author_id):
    #     if not self.has_review_comment_response(response_id):
    #         raise exceptions.EventReviewCommentResponseNotFound()
    #
    #     self.session.query(EventReviewCommentResponseUpvote) \
    #         .filter(EventReviewCommentResponseUpvote.response_id == response_id) \
    #         .filter(EventReviewCommentResponseUpvote.author_id == author_id) \
    #         .delete()
    #
    # def remove_review_comment_response_downvote(self, response_id, author_id):
    #     print("removing comment response downvote", response_id, author_id)
    #     if not self.has_review_comment_response(response_id):
    #         raise exceptions.EventReviewCommentResponseNotFound()
    #
    #     self.session.query(EventReviewCommentResponseDownvote) \
    #         .filter(EventReviewCommentResponseDownvote.response_id == response_id) \
    #         .filter(EventReviewCommentResponseDownvote.author_id == author_id) \
    #         .delete()
    #
    # def has_downvoted_review_comment_response(self, response_id, author_id):
    #     if not self.has_review_comment_response(response_id):
    #         raise exceptions.EventReviewCommentResponseNotFound()
    #
    #     count = self.session.query(EventReviewCommentResponseDownvote) \
    #         .filter(EventReviewCommentResponseDownvote.response_id == response_id) \
    #         .filter(EventReviewCommentResponseDownvote.author_id == author_id) \
    #         .count()
    #
    #     return bool(count)
    #
    # def has_upvoted_review_comment_response(self, response_id, author_id):
    #     if not self.has_review_comment_response(response_id):
    #         raise exceptions.EventReviewCommentResponseNotFound()
    #
    #     count = self.session.query(EventReviewCommentResponseUpvote) \
    #         .filter(EventReviewCommentResponseUpvote.response_id == response_id) \
    #         .filter(EventReviewCommentResponseUpvote.author_id == author_id) \
    #         .count()
    #
    #     return bool(count)

    def add_ticket_sales(self, event_id, sale):
        if not self.has_event(event_id):
            raise exceptions.EventNotFound()

        event = self.get_event_only(event_id)
        event.ticket_sales += [sale]
        self.session.commit()

    def user_has_ticket_for_event(self, event_id, user):
        if not user:
            return False

        purchased_tickets_count = self.session.query(Event).filter(Event.id.in_(
                self.session.query(EventTicketSaleOrder.event_id).filter(EventTicketSaleOrder.id.in_(
                        self.session.query(EventTicketSaleLine.sale_id) \
                            .filter(~EventTicketSaleLine.assignment.any(
                                EventTicketTypeAssignment.sale_line_id == EventTicketSaleLine.id)) \
                            .filter(EventTicketSaleOrder.customer_id == user.id) \
                            .filter(EventTicketSaleOrder.event_id==event_id) \
                            .subquery()
                )
                ).subquery()
        )).count()

        ticket_assignments_count = self.query(Event).filter(Event.id.in_(
                self.session.query(EventTicketTypeAssignment.event_id) \
                    .distinct(EventTicketTypeAssignment.assigned_to_user_id) \
                    .filter(EventTicketTypeAssignment.assigned_to_user_id == user.id) \
                    .filter(EventTicketTypeAssignment.event_id==event_id) \
                    .subquery()
        )).count()

        return bool(purchased_tickets_count + ticket_assignments_count)

    def has_purchased_tickets_for_event(self, event_id, user):
        if not user:
            return False
        count = self.session.query(EventTicketSaleOrder) \
            .filter(EventTicketSaleOrder.customer_id==user.id) \
            .filter(EventTicketSaleOrder.event_id==event_id) \
            .count()
        return bool(count)

    def event_has_been_bookmarked_by(self, event_id, user):
        if not user:
            return False

        count = self.session.query(EventBookmark) \
            .filter(EventBookmark.event_id==event_id) \
            .filter(EventBookmark.user_id==user.id).count()
        return bool(count)

    def get_event_sale_by(self, event_id=None, customer_id=None):
        if not self.has_event(event_id):
            raise exceptions.EventNotFound()

        return self.session.query(EventTicketSaleOrder).options(
                joinedload(EventTicketSaleOrder.sale_lines),
        ).filter(EventTicketSaleOrder.customer_id==customer_id) \
            .filter(EventTicketSaleOrder.event_id==event_id) \
            .all()

    def get_total_event_attendees_count(self, event_id=None):
        attendees_total_by_purchased_tickets = self.session.query(User).filter(User.id.in_(
                self.session.query(EventTicketSaleOrder.customer_id).filter(EventTicketSaleOrder.id.in_(
                        self.session.query(EventTicketSaleLine.sale_id) \
                            .filter(~EventTicketSaleLine.assignment.any(
                                EventTicketTypeAssignment.sale_line_id == EventTicketSaleLine.id)) \
                            .filter(EventTicketSaleOrder.event_id == event_id) \
                            .subquery()
                )
                ).subquery()
        )).count()

        attendees_total_by_ticket_assignments = self.query(User).filter(User.id.in_(
                self.session.query(EventTicketTypeAssignment.assigned_to_user_id) \
                    .distinct(EventTicketTypeAssignment.assigned_to_user_id) \
                    .filter(EventTicketTypeAssignment.event_id == event_id) \
                    .subquery()
        )).count()

        return attendees_total_by_purchased_tickets + attendees_total_by_ticket_assignments

    def get_event_attendees(self, event_id=None):
        """
        1. Find all users who have purchased ticket to event, with at lease 1 unassigned ticket
        2. Find all users assigned with a ticket
        :param event_id:
        :return:
        """
        attendees_by_purchased_tickets = self.session.query(User).filter(User.id.in_(
                self.session.query(EventTicketSaleOrder.customer_id).filter(EventTicketSaleOrder.id.in_(
                        self.session.query(EventTicketSaleLine.sale_id) \
                            .filter(~EventTicketSaleLine.assignment.any(
                                EventTicketTypeAssignment.sale_line_id == EventTicketSaleLine.id)) \
                            .filter(EventTicketSaleOrder.event_id == event_id) \
                            .subquery()
                )
                ).subquery()
        )).all()

        attendees_by_ticket_assignments = self.query(User).filter(User.id.in_(
                self.session.query(EventTicketTypeAssignment.assigned_to_user_id) \
                    .distinct(EventTicketTypeAssignment.assigned_to_user_id) \
                    .filter(EventTicketTypeAssignment.event_id == event_id) \
                    .subquery()
        )).all()

        return attendees_by_purchased_tickets + attendees_by_ticket_assignments

    def get_events_attending_by_user(self, user_id):
        pass

        # events_by_purchased_tickets = self.session.query(Event).filter(Event.id.in_(
        #         self.session.query(EventTicketSaleOrder.event_id).filter(EventTicketSaleOrder.id.in_(
        #                 self.session.query(EventTicketSaleLine.sale_id) \
        #                     .filter(~EventTicketSaleLine.assignment.any(
        #                         EventTicketTypeAssignment.sale_line_id == EventTicketSaleLine.id)) \
        #                     .filter(EventTicketSaleOrder.customer_id == user_id) \
        #                     .subquery()
        #         )
        #         ).subquery()
        # )).order_by(Event.created_at.asc()).all()
        #
        # events_by_ticket_assignments = self.query(Event).filter(Event.id.in_(
        #         self.session.query(EventTicketTypeAssignment.event_id) \
        #             .distinct(EventTicketTypeAssignment.assigned_to_user_id) \
        #             .filter(EventTicketTypeAssignment.assigned_to_user_id == user_id) \
        #             .subquery()
        # )).order_by(Event.created_at.asc()).all()
        #
        # events = (events_by_purchased_tickets + events_by_ticket_assignments)
        # return events

    def get_total_events_attending_by_user(self, user_id):
        events_total_by_purchased_tickets = self.session.query(Event).filter(Event.id.in_(
                self.session.query(EventTicketSaleOrder.event_id).filter(EventTicketSaleOrder.id.in_(
                        self.session.query(EventTicketSaleLine.sale_id) \
                            .filter(~EventTicketSaleLine.assignment.any(
                                EventTicketTypeAssignment.sale_line_id == EventTicketSaleLine.id)) \
                            .filter(EventTicketSaleOrder.customer_id == user_id) \
                            .subquery()
                )).subquery()
        )).count()

        events_total_by_ticket_assignments = self.query(Event).filter(Event.id.in_(
                self.session.query(EventTicketTypeAssignment.event_id) \
                    .distinct(EventTicketTypeAssignment.assigned_to_user_id) \
                    .filter(EventTicketTypeAssignment.assigned_to_user_id == user_id) \
                    .subquery()
        )).count()

        return (events_total_by_purchased_tickets + events_total_by_ticket_assignments)

    def get_events_created_by_user(self, user_id):
        events = self.session.query(Event).filter(Event.user_id==user_id).all()
        return events

    def get_total_events_created_by_user(self, user_id):
        return self.session.query(Event).filter(Event.user_id==user_id).count()

    # def get_event_

    # def get_assigned_tickets(self, event_id=None, customer_id=None):
    #     if not self.has_event(event_id):
    #         raise exceptions.EventNotFound()
    #
    #     self.session.query(EventTicketSaleOrder).options(
    #         joinedload(EventTicketSaleOrder.sale_lines, EventTicketSaleOrder.event_id),
    #     ).filter(EventTicketSaleOrder.customer_id==customer_id).filtr

    def gt_unassigned_tickets(self, event_id=None, customer_id=None):
        pass

    # def search_for_events(self, searchterm=None, category=None, period=None, country=None):
    #     # @todo use a more advance text search tool
    #     query = self.session.query(Event).filter(Event.name.ilike('%' + searchterm + '%'))
    #     if category and category != 'all':
    #         query = query.filter(Event.category_id==category)
    #
    #     if period and period != 'any':
    #         period_value = EventPeriods.get_date(period)['value']
    #
    #         if period == EventPeriods.TODAY:
    #             query = query.filter(func.DATE(Event.start_datetime) == period_value)
    #         elif period == EventPeriods.TOMORROW:
    #             query = query.filter(func.DATE(Event.start_datetime) == period_value)
    #         elif period == EventPeriods.THIS_WEEK:
    #             start_date = period_value[0]
    #             end_date = period_value[1]
    #             query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))
    #         elif period == EventPeriods.THIS_MONTH:
    #             start_date = period_value[0]
    #             end_date = period_value[1]
    #             query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))
    #         elif period == EventPeriods.NEXT_MONTH:
    #             start_date = period_value[0]
    #             query = query.filter(func.DATE(Event.start_datetime) >= start_date)
    #         elif period == EventPeriods.THIS_YEAR:
    #             start_date = period_value[0]
    #             end_date = period_value[1]
    #             query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))
    #         elif period == EventPeriods.NEXT_YEAR:
    #             start_date = period_value[0]
    #             end_date = period_value[1]
    #             query = query.filter(func.DATE(Event.start_datetime).between(start_date, end_date))
    #
    #     if country:
    #         pass
    #
    #     return query.order_by(Event.start_datetime).all()
    #
    #
    #
















