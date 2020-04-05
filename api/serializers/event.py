from marshmallow import Schema, fields
from datetime import datetime, timedelta

from api.serializers.user import UserSummarySchema
from api.serializers.brand import BrandSummarySchema
from api.auth.authenticator import Authenticator


class JobSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)


class EventTicketTypeSchema(Schema):
    id = fields.String(required=True, dump_only=True)
    name = fields.String(required=True)
    price = fields.Float(required=True)
    total_qty = fields.Float(required=True)
    sold_qty = fields.Float()
    unsold_qty = fields.Float()
    discounts = fields.Function(lambda type: TicketTypeDiscountSchema().dump(type.get_discounts(), many=True))


class EventOrganizerSchema(Schema):
    id = fields.Function(lambda organizer: organizer.user_id, required=True)
    name = fields.Function(lambda organizer: organizer.user.email if organizer.user.is_ghost else organizer.user.name, required=True )
    image = fields.Function(lambda organizer: None if organizer.user.is_ghost else organizer.user.image, required=True)
    is_ghost = fields.Function(lambda organizer: organizer.user.is_ghost, required=True)
    email = fields.Function(lambda organizer: organizer.user.email, required=True)


class SocialAccountSchema(Schema):
    id = fields.String()
    name = fields.String()


class SpeakerSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    profession = fields.Nested(JobSchema)
    social_account = fields.Nested(SocialAccountSchema)
    social_account_handle = fields.String()
    image = fields.String(required=True)


class EventMediaSchema(Schema):
    id = fields.String(required=True)
    filename = fields.String(required=True)
    format = fields.String(required=True)
    source_url = fields.String(required=True)
    is_poster = fields.Boolean(required=True, default=False, attribute='poster')


class EventContactInfoSchema(Schema):
    id = fields.String(required=True)
    type = fields.String(required=True)
    info = fields.String(required=True)


class EventCategorySchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    image = fields.String()
    slug = fields.String()


class CreateEventBookmarkSchema(Schema):
    user_id = fields.String(required=True)
    event_id = fields.String(required=True)


class EventSchema(Schema):
    id = fields.String(required=True, dump_only=True)
    name = fields.String(required=True)
    description = fields.String(required=True)
    venue = fields.String(required=True)
    start_datetime = fields.DateTime(required=True)
    end_datetime = fields.DateTime(required=True)
    cover_image = fields.Function(lambda o: o.get_poster())
    organizers = fields.Nested(EventOrganizerSchema, many=True)
    speakers = fields.Nested(SpeakerSchema, many=True)
    media = fields.Nested(EventMediaSchema, many=True, default=[])
    contact_info = fields.Nested(EventContactInfoSchema, many=True)
    category = fields.Nested(EventCategorySchema)
    ticket_types = fields.Nested(EventTicketTypeSchema, many=True)
    is_bookmarked = fields.Function(lambda event: event.is_bookmarked_by(Authenticator.get_instance().get_auth_user()))
    is_attending = fields.Function(lambda event: Authenticator.get_instance().get_auth_user().has_tickets_for_event(event))
    is_shareable_during_event = fields.Boolean()
    is_shareable_after_event = fields.Boolean()
    sponsors = fields.Nested('EventSponsorSchema', many=True)
    has_purchased_tickets = fields.Function(lambda event: Authenticator.get_instance().get_auth_user().has_purchased_tickets_for_event(event))
    creator = fields.Nested('UserSummarySchema', attribute='user')
    created_at = fields.DateTime()
    ticket_types = fields.Nested(EventTicketTypeSchema, many=True)
    is_published = fields.Boolean(default=False)
    ref = fields.String()


class EventSponsorSchema(Schema):
    id = fields.Function(lambda obj: obj.brand.id)
    event_id = fields.String(required=True)
    brand = fields.Nested('BrandSummarySchema', required=True)


class EventUpdateSchema(Schema):
    name = fields.String()
    description = fields.String()
    venue = fields.String()
    start_datetime = fields.DateTime()
    end_datetime = fields.DateTime()
    cover_image = fields.String()
    organizers = fields.Nested(EventOrganizerSchema, many=True)
    speakers = fields.Nested(SpeakerSchema, many=True)
    media = fields.Nested(EventMediaSchema, many=True)
    contact_info = fields.Nested(EventContactInfoSchema, many=True)
    categories = fields.Nested(EventCategorySchema, many=True)
    tickets = fields.Nested(EventTicketTypeSchema, many=True)


class EventResponseSchema(EventSchema):
    pass


class EventSummarySchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    start_datetime = fields.DateTime(required=True)
    cover_image = fields.String(required=True)
    ticket_price = fields.Function(lambda event: event.ticket_types[0].price if event.ticket_types else 0)
    is_bookmarked = fields.Function(lambda event: event.is_bookmarked_by(Authenticator.get_instance().get_auth_user()))
    is_attending = fields.Function(lambda event: Authenticator.get_instance().get_auth_user().has_tickets_for_event(event))
    is_shareable_during_event = fields.Boolean()
    is_shareable_after_event = fields.Boolean()
    has_purchased_tickets = fields.Function(lambda event: Authenticator.get_instance().get_auth_user().has_purchased_tickets_for_event(event))
    created_at = fields.DateTime()


class AttendeeTicketSchema(Schema):
    id = fields.String(required=True)
    event = fields.Nested(EventSummarySchema),
    owner = fields.Nested(UserSummarySchema)
    assigned_to = fields.Function(lambda obj: UserSummarySchema().dump(obj.assignment[0].assigned_to) if obj.assignment else None)


class AttendeeTicketGroupedByTypeSchema(Schema):
    ticket_type_id = fields.Function(lambda obj: obj['ticket_type'].id)
    ticket_type_name = fields.Function(lambda obj: obj['ticket_type'].name)
    total_qty = fields.Function(lambda obj: len(obj['unassigned_tickets']) + len(obj['assigned_tickets']))
    assigned_tickets = fields.Nested(AttendeeTicketSchema, many=True)
    unassigned_tickets = fields.Nested(AttendeeTicketSchema, many=True)
    assigned_tickets_count = fields.Function(lambda obj: len(obj['assigned_tickets']))
    unassigned_tickets_count = fields.Function(lambda obj: len(obj['unassigned_tickets']))
    gifted_tickets = fields.Nested(AttendeeTicketSchema, many=True)
    gifted_tickets_count = fields.Function(lambda obj: len(obj['gifted_tickets']))


class CreateEventRecommendationSchema(Schema):
    recommended_by_id = fields.String(required=True)
    recommended_to_id = fields.String(required=True)
    email = fields.String()
    phone_number = fields.String()


class EventRecommendationSchema(Schema):
    id = fields.String(required=True)
    recommended_by = fields.Nested(UserSummarySchema, required=True)
    recommended_to = fields.Function(lambda obj: UserSummarySchema().dump(obj.recommended_to) if obj.recommended_to else {"email": obj.email, "phone_number": obj.phone_number})
    event_id = fields.String(required=True)
    is_not_user = fields.Boolean()


class CreateEventSpeakerSchema(Schema):
    name = fields.String(required=True)
    social_account_id = fields.String()
    social_account_handle = fields.String()
    image = fields.String()
    profession_id = fields.String(required=True)


class EventSpeakerSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    social_account = fields.Nested(SocialAccountSchema)
    social_account_handle = fields.String()
    event_id = fields.String()
    image = fields.String()
    profession = fields.Nested(JobSchema)


class EventTicketDiscountTypeSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)


class CreateTicketTypeDiscountSchema(Schema):
    name = fields.String(required=True)
    type_id = fields.String(required=True, attribute="type")
    from_datetime = fields.DateTime(required=True)
    to_datetime = fields.DateTime(required=True)
    rate = fields.Integer(required=True)
    operator = fields.String(allow_none=True)
    min_ticket_qty = fields.Integer(allow_none=True)
    max_ticket_qty = fields.Integer(allow_none=True)
    ticket_qty = fields.Integer(allow_none=True)


class UpdateTicketTypeDiscountSchema(Schema):
    name = fields.String()
    type_id = fields.String(attribute="type")
    from_datetime = fields.DateTime()
    to_datetime = fields.DateTime()
    rate = fields.Decimal()
    operator = fields.String()
    min_ticket_qty = fields.Integer()
    max_ticket_qty = fields.Integer()
    ticket_qty = fields.Integer()


class TicketTypeDiscountSchema(CreateTicketTypeDiscountSchema):
    id = fields.String(required=True)


class EventReviewSchema(Schema):
    id = fields.String(required=True)
    content = fields.String(required=True)
    published_at = fields.DateTime(required=True)
    upvotes = fields.Function(lambda obj: obj.upvotes_count())
    downvotes = fields.Function(lambda obj: obj.downvotes_count())
    author = fields.Nested(UserSummarySchema)
    media = fields.Nested('EventReviewMediaSchema', many=True, required=True)
    event_id = fields.String(required=True)
    event_name = fields.Function(lambda obj: obj.event.name, required=True)
    is_upvoted = fields.Function(lambda obj: obj.is_upvoted_by(Authenticator.get_instance().get_auth_user()), required=True)
    is_downvoted = fields.Function(lambda obj: obj.is_downvoted_by(Authenticator.get_instance().get_auth_user()), required=True)
    comments_count = fields.Function(lambda obj:  obj.comments_count(), required=True)


class CreateEventReviewSchema(Schema):
    content = fields.String(required=True)
    media = fields.Nested('CreateEventReviewMediaSchema', many=True)


class EventReviewMediaSchema(Schema):
    id = fields.String(required=True)
    format = fields.String(required=True)
    source_url = fields.String(required=True)
    filename = fields.String()
    review_id = fields.String(required=True)


class CreateEventReviewMediaSchema(Schema):
    format = fields.String(required=True)
    source_url = fields.String(required=True)
    filename = fields.String()


class EventStreamSchema(Schema):
    id = fields.String(required=True)
    content = fields.String(required=True)
    published_at = fields.DateTime(required=True)
    upvotes = fields.Function(lambda obj: len(obj.upvotes))
    downvotes = fields.Function(lambda obj: len(obj.downvotes))
    author = fields.Nested(UserSummarySchema)
    media = fields.Nested('EventReviewMediaSchema', many=True, required=True)


class EventStreamMediaSchema(Schema):
    id = fields.String(required=True)
    format = fields.String(required=True)
    source_url = fields.String(required=True)
    stream_id = fields.String(required=True)


class EventReviewCommentSchema(Schema):
    id = fields.String(required=True)
    content = fields.String(required=True)
    published_at = fields.DateTime(required=True)
    upvotes = fields.Function(lambda obj: len(obj.upvotes))
    downvotes = fields.Function(lambda obj: len(obj.downvotes))
    is_upvoted = fields.Function(lambda obj: obj.is_upvoted_by(obj.author))
    is_downvoted = fields.Function(lambda obj: obj.is_downvoted_by(obj.author))
    author = fields.Nested(UserSummarySchema)
    media = fields.Nested('EventReviewMediaSchema', many=True)
    review_id = fields.String(required=True)
    responses_count = fields.Function(lambda obj: obj.responses_count())


class CreateEventReviewCommentSchema(Schema):
    content = fields.String(required=True)
    media = fields.Nested('CreateEventReviewCommentMediaSchema', many=True)


class EventReviewCommentMediaSchema(Schema):
    id = fields.String(required=True)
    format = fields.String(required=True)
    source_url = fields.String(required=True)
    comment_id = fields.String(required=True)


class CreateEventReviewCommentMediaSchema(Schema):
    format = fields.String(required=True)
    source_url = fields.String(required=True)
    filename = fields.String()


class EventReviewCommentResponseSchema(Schema):
    id = fields.String(required=True)
    content = fields.String(required=True)
    published_at = fields.DateTime(required=True)
    upvotes = fields.Function(lambda obj: len(obj.upvotes))
    downvotes = fields.Function(lambda obj:len(obj.downvotes))
    author = fields.Nested(UserSummarySchema, required=True)
    comment_id = fields.String(required=True)
    media = fields.Nested('EventReviewCommentResponseMediaSchema', many=True)


class CreateEventReviewCommentResponseSchema(Schema):
    content = fields.String(required=True)
    media = fields.Nested('CreateEventReviewCommentResponseMediaSchema', many=True)


class CreateEventReviewCommentResponseMediaSchema(Schema):
    format = fields.String(required=True)
    source_url = fields.String(required=True)
    filename = fields.String()


class EventReviewCommentResponseMediaSchema(Schema):
    id = fields.String(required=True)
    format = fields.String(required=True)
    source_url = fields.String(required=True)
    response_id = fields.String(required=True)


class EventStreamCommentSchema(Schema):
    id = fields.String(required=True)
    content = fields.String(required=True)
    published_at = fields.DateTime(required=True)
    upvotes = fields.Function(lambda obj: len(obj.upvotes))
    downvotes = fields.Function(lambda obj: len(obj.downvotes))
    author = fields.Nested(UserSummarySchema, required=True)
    stream_id = fields.String(required=True)
    media = fields.Nested('EventStreamCommentMediaSchema', many=True, required=True)


class EventStreamCommentMediaSchema(Schema):
    id = fields.String(required=True)
    format = fields.String(required=True)
    source_url = fields.String(required=True)
    filename = fields.String()
    comment_id = fields.String(required=True)


class EventStreamCommentResponseSchema(Schema):
    id = fields.String(required=True)
    content = fields.String(required=True)
    published_at = fields.String(required=True)
    upvotes = fields.Function(lambda obj: len(obj.upvotes))
    downvotes = fields.Function(lambda obj: len(obj.downvotes))
    author_id = fields.String(required=True)
    author = fields.Nested(UserSummarySchema, required=True)
    comment_id = fields.String(required=True)
    media = fields.Nested('EventStreamCommentResponseMediaSchema', many=True, required=True)


class EventStreamCommentResponseMediaSchema(Schema):
    id = fields.String(required=True)
    format = fields.String(required=True)
    source_url = fields.String(required=True)
    filename = fields.String()
    response_id = fields.String(required=True)


class BuyTicket(Schema):
    payment_info = fields.Nested('BuyTicketPaymentInfo')
    ticket_info = fields.Nested('BuyTicketInfo', many=True)


class BuyTicketPaymentInfo(Schema):
    payment_type = fields.String(required=True)
    mobile_number = fields.String()
    card_number = fields.String()
    card_cv = fields.String
    card_expiration_date = fields.String()


class BuyTicketInfo(Schema):
    ticket_type_id = fields.String(required=True)
    qty = fields.String(required=True)


class TicketReservationRequestSchema(Schema):
    ticket_type_id = fields.String(required=True)
    ticket_qty = fields.Integer(required=True)


class RemoveTicketReservationRequestSchema(Schema):
    ticket_type_ids = fields.List(fields.String(), required=True)


class TicketReservationSchema(Schema):
    id = fields.String(required=True)
    reservation_by = fields.Nested(UserSummarySchema, required=True)
    ticket_qty = fields.String(required=True)
    created_at = fields.DateTime(required=True)
    expires_at = fields.DateTime(required=True)
    total_tickets_qty = fields.Integer()


class NotificationSchema(Schema):
    id = fields.String(required=True)
    type = fields.String(attribute='notification_type')
    is_read = fields.Boolean()
    created_at = fields.DateTime()
    message = fields.String()
    recipient = fields.Nested(UserSummarySchema)
    actor = fields.Nested(UserSummarySchema)
    event = fields.Nested(EventSummarySchema)
    brand = fields.Nested(BrandSummarySchema)
    ticket = fields.Nested(AttendeeTicketSchema)