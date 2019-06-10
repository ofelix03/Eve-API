from . import brand
from . import event
from . import job
from . import social_media
from . import user

event_schema = event.EventSchema()
event_summary_schema = event.EventSummarySchema()
event_response_schema = event.EventResponseSchema()
event_update_schema = event.EventUpdateSchema()
event_ticket_type_schema = event.EventTicketTypeSchema()
event_recommendation_schema = event.EventRecommendationSchema()
create_event_recommendation_schema = event.CreateEventRecommendationSchema()
attendee_ticket_grouped_by_type_schema = event.AttendeeTicketGroupedByTypeSchema()
create_speaker_schema = event.CreateEventSpeakerSchema()
event_speaker_schema = event.EventSpeakerSchema()
create_event_bookmark_schema = event.CreateEventBookmarkSchema()
ticket_type_discount_schema = event.TicketTypeDiscountSchema()
create_ticket_type_discount_schema = event.CreateTicketTypeDiscountSchema()
update_ticket_type_discount_schema = event.UpdateTicketTypeDiscountSchema()
event_review_schema = event.EventReviewSchema()
create_event_review_schema = event.CreateEventReviewSchema()
event_review_media_schema = event.EventReviewMediaSchema
create_event_review_media_schema = event.CreateEventReviewSchema()
event_review_comment_schema = event.EventReviewCommentSchema()
create_event_review_comment_schema = event.CreateEventReviewCommentSchema()
event_review_comment_response_schema = event.EventStreamCommentResponseSchema()
create_event_review_comment_response_schema = event.CreateEventReviewCommentResponseSchema()
event_sponsor_schema = event.EventSponsorSchema()
ticket_reservation_req_schema = event.TicketReservationRequestSchema()
remove_ticket_reservation_req_schema = event.RemoveTicketReservationRequestSchema()
ticket_reservation_schema = event.TicketReservationSchema()

user_schema = user.UserSummarySchema()

user_schema = user.UserSchema()
user_summary_schema = user.UserSummarySchema()
logged_in_user_schema = user.LoggedInUserSchema()
user_full_schema = user.UserSchemaFull()
create_user_schema = user.CreateUserSchema()
change_user_password_schema = user.ChangeUserPasswordSerliazer()
user_payment_details_schema = user.UserPaymentDetailsSchema()
login_user_schema = user.LoginUserSchema()
mobile_payment_info_schema = user.MobilePaymentInfoSchema()
card_payment_info_schema = user.CardPaymentInfoSchema()
notification_schema = event.NotificationSchema()
