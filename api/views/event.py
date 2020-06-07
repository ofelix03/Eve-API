from marshmallow import ValidationError
from api.views.auth_base import AuthBaseView
from api.auth.authenticator import Authenticator
from api.models.event import db
from api.models import event_periods
from api.models.event import (
    Event, EventOrganizer, EventRecommendation,
    EventSpeaker, EventContactInfo,
    EventReview, EventReviewMedia,
    EventReviewUpvote, EventReviewDownvote,
    EventReviewCommentMedia,
    EventReviewComment, EventReviewCommentResponseMedia,
    EventSponsor, EventReviewCommentResponse,
)
from api.models import event as models
from api.libs.cloudinary import upload as cloudinary_upload
from api.libs.cloudinary import api as cloudinary_api

from api.repositories import exceptions
import api.serializers as serializers
from api.utils import TicketDiscountOperator, TicketDiscountType
from api.models.domain.user_payment_info import DiscountTypes
from . import *
from ..models.pagination_cursor import PaginationCursor
from .. import decorators


class EventView(AuthBaseView):

    def index(self):
        output_query = False
        period_query = False
        category = None
        payload = {}
        auth_user = Authenticator.get_instance().get_auth_user_without_auth_check()
        cursor = self.get_cursor(request)
        if request.args:
            if 'output' in request.args:
                output_query = request.args['output']

            if 'period' in request.args:
                period_query = request.args['period']

            if 'category_slug' in request.args:
                category_slug = request.args['category_slug']
                if category_slug:
                    category = models.EventCategory.find_category_by_slug(category_slug)

        if output_query and output_query == 'detail':
            if period_query:
                if ',' in period_query:  # we have multiple period_query.eg. today,tomorrow,this_week
                    date = [p.strip() for p in period_query.split(',')]
                    events = {}
                    for period in period_query:
                        date = event_periods.EventPeriods.get_date(date)
                        period_events = models.Event.get_events(period=date, category_id=category.id, cursor=cursor)
                        events[period] = serializers.event_schema.dump(period_events, many=True)
                else:
                    date = event_periods.EventPeriods.get_date(period_query)
                    events = models.Event.get_events(period=date, category_id=category.id, cursor=cursor)
                    if auth_user:
                        events = serializers.event_schema.dump(events, many=True)
                    else:
                        events = serializers.event_anon_schema.dump(events, many=True)
            else:
                events = models.Event.get_events(category_id=category.id, cursor=cursor)
                if auth_user:
                    events = serializers.event_schema.dump(events, many=True)
                else:
                    event = serializers.event_anon_schema.dump(events, many=True)
            payload.update({
                'events': events,
                'metadata': {
                    'cursor': {
                        'before': cursor.before,
                        'after': cursor.after,
                        'limit': cursor.limit
                    }
                }
            })
            return response(payload)
        else:
            # summary of events
            if period_query:
                if ',' in period_query:  # we have multiple period_query.eg. today,tomorrow,this_week
                    period_querys = [p.strip() for p in period_query.split(',')]
                    events = {}
                    for period_query in period_querys:
                        cursor = PaginationCursor()
                        date = event_periods.EventPeriods.get_date(period_query)
                        fetched_events = models.Event.get_events_summary(period=date, cursor=cursor)
                        if auth_user:
                            fetched_events = serializers.event_summary_schema.dump(fetched_events, many=True)
                        else:
                            fetched_events = serializers.event_summary_anon_schema.dump(fetched_events, many=True)
                        events[period_query] = {
                            'data': fetched_events,
                            'metadata': {
                                'cursor': {
                                    'before': cursor.before,
                                    'after': cursor.after,
                                    'limit': cursor.limit
                                },
                            }
                        }
                    events_count = None
                    payload.update({
                        'ok': True,
                        'events': events,
                        'events_count': events_count,
                    })
                    return response(payload)
                else:
                    date = event_periods.EventPeriods.get_date(period_query)
                    events = models.Event.get_events_summary(category=category, period=date, cursor=cursor)
                    if auth_user:
                        events = serializers.event_summary_schema.dump(events, many=True)
                    else:
                        events = serializers.event_summary_anon_schema.dump(events, many=True)
                    events_count = models.Event.get_events_total(category=category, period=date)
                    payload.update({
                        'ok': True,
                        'events': events,
                        'events_count': events_count,
                        'metadata': {
                            'cursor': {
                                'before': cursor.before,
                                'after': cursor.after,
                                'limit': cursor.limit
                            },
                        }
                    })
                    return response(payload)

            else:
                events = models.Event.get_events_summary(category=category, cursor=cursor)
                if auth_user:
                    events = serializers.event_summary_schema.dump(events, many=True)
                else:
                    events = serializers.event_summary_anon_schema.dump(events, many=True)
                events_count = models.Event.get_events_total(category=category)

                payload.update({
                    'ok': True,
                    'events': events,
                    'events_count': events_count,
                    'metadata': {
                        'cursor': {
                            'before': cursor.before,
                            'after': cursor.after,
                            'limit': cursor.limit
                        },
                    }
                })
                return response(payload)

    def get(self, event_id):
        auth_user = Authenticator.get_instance().get_auth_user_without_auth_check()
        if not models.Event.has_event(event_id):
            return response({
                "ok": True,
                "code": "CONTENT_NOT_FOUND",
            }, 204)
        event = models.Event.get_event(event_id)
        if auth_user:
            event = serializers.event_schema.dump(event)
        else:
            event = serializers.event_anon_schema.dump(event)
        return response(event)

    def delete(self, event_id=None):
        try:
            models.Event.delete_event(event_id)
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 204)

        return response('')

    @route('/<string:event_id>/ticket_types', methods=['GET'])
    def get_ticket_types(self, event_id):
        event = models.Event.get_event_only(event_id)
        return response({
            "ok": True,
            "ticket_types": serializers.event_ticket_type_schema.dump(event.ticket_types, many=True)
        })

    @route('/<string:event_id>/ticket_types/<string:ticket_type_id>', methods=['DELETE'])
    def delete_ticket_type(self, event_id, ticket_type_id):
        try:
            event = models.Event.get_event_only(event_id)
            models.EventTicketType.delete_ticket_type(ticket_type_id)
            return response(None)
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.TicketNotFound:
            return response({
                "ok": False,
                "code": "TICKET_TYPE_NOT_FOUND"
            }, 400)

    @route('/<string:event_id>/tickets/<string:ticket_id>', methods=['PUT'])
    def update_ticket_type(self, event_id, ticket_id):
        return 'putting TICKET'

    @route('/<string:event_id>/ticket_types', methods=['POST'])
    def create_ticket_type(self, event_id):
        data = request.get_json()

        try:
            serializers.event_ticket_type_schema.load(data)
            event = models.Event.get_event_only(event_id)
            name = data['name']
            price = data['price']
            total_qty = data['total_qty']
            ticket_type = models.EventTicketType.create(name=name, price=price, total_qty=total_qty, event=event)

            return response({
                'ok': True,
                "created_id": ticket_type.id,
                "ticket_type": serializers.event_ticket_type_schema.dump(ticket_type)
            }, 201)
        except ValidationError as e:
            return response({
                'ok': False,
                'code': 'VALIDATION_ERROR',
                'errors': e.messages
            }, 400)
        except exceptions.EventNotFound:
            return response({
                'ok': False,
                'code': 'EVENT_NOT_FOUND'
            }, 400)

    @route('/<string:event_id>/ticket_types/<string:ticket_type_id>/discounts', methods=['POST'])
    def create_ticket_type_discount(self, event_id, ticket_type_id):
        try:
            data = request.get_json()
            models.Event.get_event_only(event_id)
            ticket_type = models.EventTicketType.get_ticket_type(ticket_type_id)
            data = serializers.create_ticket_type_discount_schema.load(data)

            name = data.get('name')
            from_datetime = data.get('from_datetime')
            to_datetime = data.get('to_datetime')
            rate = data.get('rate')
            operator = data.get('operator')
            discount_type = data.get('type')
            ticket_qty = None
            min_ticket_qty = None
            max_ticket_qty = None
            if not DiscountTypes.has_type(discount_type):
                raise exceptions.TicketTypeDiscountTypeNotFound()

            if not TicketDiscountOperator.has_operator(operator) and \
                    discount_type in TicketDiscountType.NUMBER_OF_PURCHASES:
                return response({
                    'ok': False,
                    "code": "BAD_REQUEST",
                    "message": "Invalid value for operator field"
                }, 400)

            if operator in [TicketDiscountOperator.EQUAL_TO,
                            TicketDiscountOperator.GREATER_THAN,
                            TicketDiscountOperator.GREATER_THAN_OR_EQUAL_TO]:
                ticket_qty = data.get('ticket_qty')
            elif operator == TicketDiscountOperator.BETWEEN:
                min_ticket_qty = data.get('min_ticket_qty')
                max_ticket_qty = data.get('max_ticket_qty')

            discount = models.EventTicketDiscount.create(name=name,
                                                         from_datetime=from_datetime,
                                                         to_datetime=to_datetime,
                                                         operator=operator,
                                                         min_ticket_qty=min_ticket_qty,
                                                         max_ticket_qty=max_ticket_qty,
                                                         ticket_qty=ticket_qty,
                                                         rate=rate,
                                                         discount_type=discount_type
                                                         )
            discount = ticket_type.add_discount(discount)
            return response({
                "ok": True,
                "message": "Discount created",
                "created_id": discount.id,
                "discount": serializers.ticket_type_discount_schema.dump(discount)
            })
        except ValidationError as e:
            return response({
                'code': 'BAD_REQUEST',
                'message': e.messages
            })
        except exceptions.EventNotFound:
            return response({
                'ok': False,
                'code': 'EVENT_NOT_FOUND',
            }, 400)
        except exceptions.TicketTypeNotFound:
            return response({
                'ok': False,
                'code': 'TICKET_TYPE_NOT_FOUND'
            }, 400)
        except exceptions.TicketTypeDiscountTypeNotFound:
            return response({
                'ok': False,
                'code': 'TICKET_TYPE_DISCOUNT_TYPE_NOT_FOUND'
            })

    @route('/<string:event_id>/ticket_types/<string:ticket_type_id>/discounts/<string:discount_id>', methods=['PUT'])
    def update_ticket_type_discount(self, event_id, ticket_type_id, discount_id):
        try:
            discount_data = request.get_json()
            event = models.Event.get_event_only(event_id)
            discount = event.get_ticket_type_discount(ticket_type_id, discount_id)

            if 'name' in discount_data and discount.name != discount_data.get('name'):
                discount.name = discount_data.get('name')

            if 'from_datetime' in discount_data and discount.from_datetime != discount_data.get('from_datetime'):
                discount.from_datetime = discount_data.get('from_datetime')

            if 'to_datetime' in discount_data and discount.to_datetime != discount_data.get('to_datetime'):
                discount.to_datetime = discount_data.get('to_datetime')

            if 'rate' in discount_data and discount.rate != discount_data.get('rate'):
                discount.rate = discount_data.get('rate')

            if 'type_id' in discount_data and discount.type_id != discount_data.get('type_id'):
                discount.type_id = discount_data.get('type_id')

            if 'operator' in discount_data:
                ticket_qty = None
                min_ticket_qty = None
                max_ticket_qty = None

                operator = discount_data.get('operator')
                if operator in (TicketDiscountOperator.EQUAL_TO, TicketDiscountOperator.GREATER_THAN,
                                TicketDiscountOperator.GREATER_THAN_OR_EQUAL_TO):
                    ticket_qty = discount_data.get('ticket_qty')
                elif operator == TicketDiscountOperator.BETWEEN:
                    min_ticket_qty = discount_data.get('min_ticket_qty')
                    max_ticket_qty = discount_data.get('max_ticket_qty')

                discount.ticket_qty = ticket_qty
                discount.min_ticket_qty = min_ticket_qty
                discount.max_ticket_qty = max_ticket_qty
                discount.operator = operator
            discount.update()
            return response({
                "ok": True,
                "updated_id": discount.id,
                "discount": serializers.ticket_type_discount_schema.dump(discount)
            })

        except exceptions.EventNotFound:
            return response({
                'ok': False,
                'code': 'EVENT_NOT_FOUND',
            }, 400)
        except exceptions.TicketDiscountNotFound:
            return response({
                'ok': False,
                'code': 'DISCOUNT_NOT_FOUND'
            }, 400)

    @route('/<string:event_id>/ticket_types/<string:ticket_type_id>/discounts', methods=['GET'])
    def get_ticket_type_discount(self, event_id, ticket_type_id):
        try:
            event = models.Event.get_event_only(event_id)
            discounts = event.get_ticket_type_with_discounts(ticket_type_id)
            return response({
                'ok': True,
                'ticket_type_discounts': serializers.ticket_type_discount_schema.dump(discounts, many=True)
            })
        except exceptions.EventNotFound:
            return response({
                'ok': False,
                'code': 'EVENT_NOT_FOUND'
            }, 400)
        except exceptions.TicketTypeNotFound:
            return response({
                'ok': False,
                'code': 'TICKET_TYPE_NOT_FOUND'
            }, 400)

    @route('/<string:event_id>/ticket_types/<string:ticket_type_id>/discounts/<string:discount_id>', methods=['DELETE'])
    def delete_ticket_type_discount(self, event_id, ticket_type_id, discount_id):
        try:
            event = models.Event.get_event_only(event_id)
            event.remove_ticket_type_discount(ticket_type_id, discount_id)
            return response({
                "ok": True,
            })
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.TicketNotFound:
            return response({
                "ok": False,
                "code": "TICKET_NOT_FOUND"
            }, 400)

    @route('/<string:event_id>/reserve-tickets', methods=['POST'])
    def reserve_tickets(self, event_id):
        try:
            data = request.get_json()
            data = serializers.ticket_reservation_req_schema.load(data, many=True)
            event = models.Event.get_event_only(event_id)
            auth_user = Authenticator.get_instance().get_auth_user()

            reservation_lines = []
            ticket_types = []
            for d in data:
                ticket_type = models.EventTicketType.get_ticket_type(d['ticket_type_id'])
                ticket_qty = d['ticket_qty']
                reservation_lines.append([ticket_type, ticket_qty])
                ticket_types.append(ticket_type)

            try:
                created_reservation = models.EventTicketReservation.create_reservation(reservation_lines=reservation_lines,
                                                                                       reservation_by=auth_user)
            except exceptions.AlreadyHasTicketReservation as e:
                created_reservation = e.reservation
            except exceptions.InsufficientTicketsAvailable:
                messages = []
                for ticket_type in ticket_types:
                    message = "Only {available_qty} {ticket_type_name} are remaining".format(
                        available_qty=ticket_type.get_available_qty(), ticket_type_name=ticket_type.name)
                    messages.append(message)
                return response({
                    "ok": False,
                    "code": "INSUFFICENT_TICKETS",
                    "message": "\n".join(messages)
                }, 400)

            return response({
                "ok": True,
                "reservation": serializers.ticket_reservation_schema.dump(created_reservation)
            })
        except ValidationError as e:
            return response({
                "ok": False,
                "error": e.messages,
            }, 400)
        except exceptions.EventNotFound:
            return response({
                'ok': False,
                'code': 'EVENT_NOT_FOUND'
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('/<string:event_id>/remove-reserved-tickets', methods=['DELETE'])
    def remove_ticket_reservations(self, event_id):

        try:
            event = models.Event.get_event_only(event_id)
            auth_user = Authenticator.get_instance().get_auth_user()
            models.EventTicketReservation.remove_reservations_from(auth_user)
            return response({
                "ok": True
            })
        except exceptions.NotAuthUser:
            return self.not_auth_response()
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            })

    # @route('/<string:event_id>/attendees')
    # def get_event_attendees(self, event_id):
    #     if event_id:
    #         pass

    @route('/<string:event_id>/recommendations')
    def get_event_recommendations(self, event_id):
        try:
            event = models.Event.get_event_only(event_id)
            recommendations = event.get_event_recommendations()
            return response({
                'ok': True,
                'total': len(recommendations),
                'recommendations': serializers.event_recommendation_schema.dump(recommendations, many=True)
            })
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)

    @route('/<string:event_id>/recommendations', methods=['POST'])
    def add_new_recommendations(self, event_id):
        try:
            data = request.get_json()
            event = models.Event.get_event_only(event_id)
            recommended_by = Authenticator.get_instance().get_auth_user()
            for recommendation in data:
                email = recommendation['email'] if 'email' in recommendation else None
                phone_number = recommendation['phone_number'] if 'phone_number' in recommendation else None

                if 'recommended_to_id' in recommendation:
                    recommended_to = models.User.get_user(recommendation['recommended_to_id'])
                else:
                    recommended_to = None

                event_recommendation = EventRecommendation(event=event, email=email, phone_number=phone_number,
                                                           recommended_by=recommended_by, recommended_to=recommended_to)

                if event_recommendation.is_not_user:
                    search_term = event_recommendation.email or event_recommendation.phone_number
                    if event.has_recommendation_for(event_recommendation.recommended_by.id, search_term=search_term):
                        continue
                elif event.has_recommendation_for(event_recommendation.recommended_by.id,
                                                  recommended_to_id=event_recommendation.recommended_to.id):
                    continue
                event.recommendations.append(event_recommendation)
                event.update()

                models.Notification.create(notification_type=models.Notifications.EVENT_RECOMMENDED.value,
                                           recipient=event_recommendation.recommended_to,
                                           actor=recommended_by,
                                           event=event)
            # @todo send an email if user has opted for email notification

            return response(serializers.event_recommendation_schema.dump(event.get_event_recommendations(), many=True))
        except ValidationError as e:
            return response({
                "ok": False,
                "code": "REQUEST_VALIDATION_FAILED",
                "errors": e.messages
            }, 400)
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND",
            }, 400)
        except exceptions.UserNotFound:
            return response({
                "ok": False,
                "code": "USER_NOT_FOUND"
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/speakers', methods=['GET'])
    def get_speakers(self, event_id):
        try:
            event = models.Event.get_event_only(event_id)
            speakers = event.get_speakers()
            return response({
                "ok": True,
                "total_speakers": len(speakers),
                "speakers": serializers.event_speaker_schema.dump(speakers, many=True)
            })
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)

    @route('<string:event_id>/speakers', methods=['POST'])
    def add_speaker(self, event_id):
        speaker = request.get_json()
        try:
            event = models.Event.get_event_only(event_id)
            speaker = serializers.create_speaker_schema.load(speaker)
            name = speaker['name']
            social_account_handle = speaker['social_account_handle']

            if models.Job.has_job(speaker['profession_id']):
                profession = models.Job.get_job(speaker['profession_id'])

            if models.SocialMedia.has_social_account(speaker['social_account_id']):
                social_account = models.SocialMedia.get_social_account(speaker['social_account_id'])

            speaker_obj = EventSpeaker(name=name, social_account=social_account,
                                       social_account_handle=social_account_handle, profession=profession)
            event.add_speaker(speaker_obj)

            return response({
                "ok": True,
                "speaker": serializers.event_speaker_schema.dump(speaker_obj)
            })

        except ValidationError as e:
            return response({
                "ok": True,
                "errors": e.messages
            }, 400)
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)

    @route('<string:event_id>/speakers/<string:speaker_id>', methods=['PUT'])
    def update_speaker(self, event_id, speaker_id):
        try:
            data = request.get_json()
            event = models.Event.get_event_only(event_id)
            speaker = event.get_speaker(speaker_id)

            if 'name' in data:
                speaker.name = data['name']

            if 'social_account_id' in data:
                social_account = models.SocialMedia.get_social_account(data['social_account_id'])
                speaker.add_social_account(social_account)

            if 'social_account_handle' in data:
                speaker.social_account_handle = data['social_account_handle']

            if 'profession_id' in data:
                profession = models.Job.get_job(data['profession_id'])
                speaker.add_profession(profession)
            speaker.update()

            speaker = event.get_speaker(speaker.id)

            return response({
                "ok": True,
                "speaker": serializers.event_speaker_schema.dump(speaker)
            })

        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            })
        except exceptions.EventSpeakerNotFound:
            return response({
                "ok": False,
                "code": "EVENT_SPEAKER_NOT_FOUND"
            })
        except exceptions.JobNotFound:
            return response({
                "ok": False,
                "code": "JOB_NOT_FOUND"
            })
        except exceptions.SocialAccountNotFound:
            return response({
                "ok": False,
                "code": "SOCIAL_ACCOUNT_NOT_FOUND"
            })

    @route('<string:event_id>/speakers/<string:speaker_id>', methods=['DELETE'])
    def remove_speaker(self, event_id, speaker_id):
        try:
            event = models.Event.get_event_only(event_id)
            event.remove_speaker(speaker_id)
            return response({
                "ok": True,
            })
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventSpeakerNotFound:
            return response({
                "ok": False,
                "code": "EVENT_SPEAKER_NOT_FOUND"
            }, 400)

    @route('<string:event_id>/sponsors', methods=['POST'])
    def add_sponsor(self, event_id):
        try:
            data = request.get_json()
            event = models.Event.get_event_only(event_id)
            sponsor = models.EventSponsor.create(models.Brand.get_brand(data['brand_id']))
            event.sponsors.append(sponsor)
            event.update()
            return response(serializers.event_sponsor_schema.dump(sponsor))
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.BrandNotFound:
            return response({
                "ok": False,
                "code": "BRAND_NOT_FOUND"
            }, 400)

    @route('<string:event_id>/sponsors', methods=['GET'])
    def get_sponsors(self, event_id):
        try:
            event = models.Event.get_event_only(event_id)
            sponsors = event.get_sponsors()
            return response({
                "ok": True,
                "sponsors": serializers.event_sponsor_schema.dump(sponsors, many=True)
            })
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)

    @route('<string:event_id>/bookmarks', methods=['POST'])
    def create_bookmark(self, event_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            event = models.Event.get_event_only(event_id)
            event.bookmark(auth_user)
            models.Notification.create(notification_type=models.Notifications.EVENT_BOOKMARKED.value,
                                       recipient=event.user,
                                       actor=auth_user,
                                       event=event)
            return response({
                "ok": True,
                "event_id": event_id,
                "is_bookmarked": event.is_bookmarked_by(auth_user)
            }, 201)
        except exceptions.EventNotFound:
            return response({
                "ok":False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.BookmarkAlreadyExist:
            event.unbookmark(auth_user)
            models.Notification.create(notification_type=models.Notifications.EVENT_UNBOOKMARKED.value,
                                       recipient=event.user,
                                       actor=auth_user,
                                       event=event)
            return response({
                "ok": True,
                "event_id": event_id,
                "is_bookmarked": event.is_bookmarked_by(auth_user)
            }, 201)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/delete-bookmark', methods=['DELETE'])
    def delete_bookmark(self, event_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            event = models.Event.get_event_only(event_id)
            event.bookmark(auth_user)
            models.Notification.create(notification_type=models.Notifications.EVENT_UNBOOKMARKED.value,
                                       recipient=event.user,
                                       actor=auth_user,
                                       event=event)
            return response({
                "ok": True
            })
        except exceptions.BookmarkNotFound:
            bad_request = {
                "ok": True,
                "code": "EVENT_NOT_BOOKMARKED"
            }
            return response(bad_request)
        except exceptions.EventNotFound:
            bad_request = {
                "ok": True,
                "code": "EVENT_NOT_FOUND"
            }
            return response(bad_request)

        except exceptions.NotAuthUser:
            return self.not_auth_response()

    def post(self):
        try:
            data = request.get_json(0)

            if not data:
                return response({
                    "ok": True,
                    "code": "BAD_REQUEST"
                }, 400)

            event = Event()
            event.user = Authenticator.get_instance().get_auth_user()
            if 'name' in data:
                event.name = data.get('name')

            if 'venue' in data:
                event.venue = data.get('venue')

            if 'start_datetime' in data:
                event.start_datetime = data.get('start_datetime')

            if 'end_datetime' in data:
                event.end_datetime = data.get('end_datetime')

            if 'description' in data:
                event.description = data.get('description')

            if 'is_published' in data:
                event.is_published = data['is_published']

            if 'category_id' in data:
                category = models.EventCategory.get_category(data['category_id'])
                if category:
                    event.category = category

            if 'organizers' in data:
                for organizer in data['organizers']:
                    if 'id' in organizer:
                        user = models.User.get_user(organizer['id'])
                        event.organizers.append(EventOrganizer(user=user))
                    elif 'email' in organizer:  # this is a ghost user
                        user = models.User.create_ghost_user(organizer['email'])
                        event.organizers.append(EventOrganizer(user=user))

            if 'contact_info' in data:
                for contact in data.get('contact_info'):
                    if 'type' in contact and contact['type']:
                        event.contact_info.append(EventContactInfo(type=contact['type'], info=contact['info']))

            if 'sponsors' in data:
                for id in data['sponsors']:
                    event.sponsors.append(EventSponsor(models.Brand.get_brand(id)))

            event = models.Event.add_event(event)
            return response(serializers.event_schema.dump(event))
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    def put(self, event_id):
        try:
            data = request.get_json()
            auth_user = Authenticator.get_instance().get_auth_user()

            if data:
                event = models.Event.get_event(event_id)

                if event.user.id != auth_user.id:
                    return response({
                        "ok": False,
                        "code": "UNATHORIZED_USER_ACTION"
                    }, 400)

                if 'name' in data:
                    event.name = data.get('name')

                if 'venue' in data:
                    event.venue = data.get('venue')

                if 'start_datetime' in data:
                    event.start_datetime = data.get('start_datetime')

                if 'end_datetime' in data:
                    event.end_datetime = data.get('end_datetime')

                if 'description' in data:
                    event.description = data.get('description')

                if 'category_id' in data:
                    event.clear_categories()
                    category = models.EventCategory.get_category(data['category_id'])
                    if category:
                        event.category = category

                if 'organizers' in data:
                    if data['organizers']:
                        event.clear_organizers()

                    for organizer in data['organizers']:
                        if 'id' in organizer:
                            user = models.User.get_user(organizer['id'])
                            event.organizers.append(EventOrganizer(user=user))
                        elif 'email' in organizer:  # this is a ghost user
                            user = models.User.create_ghost_user(organizer['email'])
                            event.organizers.append(EventOrganizer(user=user))

                if 'contact_info' in data:
                    if data['contact_info']:
                        event.clear_contact_infos()

                    for contact in data.get('contact_info'):
                        if 'type' in contact and contact['type']:
                            event.contact_info.append(EventContactInfo(type=contact['type'], info=contact['info']))

                if 'sponsors' in data:
                    if data['sponsors']:
                        event.clear_sponsors()

                    for id in data['sponsors']:
                        event.sponsors.append(EventSponsor(brand=models.Brand.get_brand(id)))

                if 'is_published' in data:
                    event.is_published = data['is_published']

                event.update()

            event = models.Event.get_event(event.id)
            return response(serializers.event_schema.dump(event))
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/privacy_terms/is_shareable_during_event', methods=['PUT'])
    def update_is_shareable_during_event_privacy_terms(self, event_id):

        try:
            data = request.get_json()
            event = models.Event.get_event_only(event_id)
            if 'status' in data and data['status'] not in [True, False, 1, 0]:
                return response({
                    "ok": False,
                    "code": "status field is required"
                }, 400)

            status = data['status']
            event.is_shareable_during_event = bool(status)
            event.update()
            return response({
                "ok": True,
                "status": status,
                "event_id": event.id
            })

        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)

    @route('<string:event_id>/privacy_terms/is_shareable_after_event', methods=['PUT'])
    def update_is_shareable_after_event_privacy_terms(self, event_id):

        try:
            data = request.get_json()
            if 'status' in data and data['status'] not in [True, False, 1, 0]:
                return response({
                    "message": "Bad request",
                    "errors": {
                        "status": "invalid field value"
                    }
                })

            status = data['status']
            event = models.Event.get_event_only(event_id)
            event.is_shareable_after_event = bool(status)
            event.update()

            return response({
                "ok": True,
                "event_id": event.id,
                "status": event.is_shareable_after_event
            })
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)

    @route('<string:event_id>/publish', methods=['PUT'])
    def publish_event(self, event_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            event = models.Event.get_event_only(event_id)

            if auth_user.id != event.user_id:
                return response({
                    "ok": False,
                    "code": "UNAUTHORIZED_USER_ACTION"
                }, 400)

            event.publish()
            return response({
                "ok": True,
                "is_published": True
            })
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/reviews', methods=['POST'])
    def add_event_review(self, event_id):
        try:
            data = request.get_json()
            data = serializers.create_event_review_schema.load(data)
            print('data###', data)
            content = data['content']
            author = Authenticator.get_instance().get_auth_user()
            media = []
            if 'media' in data:
                for m in data['media']:
                    media.append(EventReviewMedia(source_url=m['source_url'], format=m['format']))
            event = models.Event.get_event_only(event_id)
            review = EventReview(content=content, author_id=author.id, media=media)
            event.reviews.append(review)
            db.session.commit()
            return response(serializers.event_review_schema.dump(review), 201)
        except ValidationError as e:
            return response({
                "ok": False,
                "code": "BAD_REQUEST",
                "errors": e.messages
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/reviews/<string:review_id>', methods=['PUT'])
    def update_event_review(self, event_id, review_id):
        try:
            data = request.get_json()
            event = models.Event.get_event_only(event_id)
            review = event.get_review(review_id)
            if 'content' in data:
                review.content = data['content']
            event.reviews.append(review)
            event.update()
            return response(serializers.event_review_schema.dump(review))
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "REVIEW_NOT_FOUND"
            }, 400)

    @route('<string:event_id>/reviews/<string:review_id>', methods=['DELETE'])
    def delete_event_review(self, event_id, review_id):
        try:
            event = models.Event.get_event_only(event_id)
            event.delete_review(review_id)
            return response("")
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "REVIEW_NOT_FOUND"
            }, 400)

    @route('<string:event_id>/reviews', methods=['GET'])
    def get_event_reviews(self, event_id):
        try:
            cursor = self.get_cursor(request)
            event = models.Event.get_event_only(event_id)
            reviews = event.get_reviews(cursor)
            total_reviews = event.get_total_event_reviews()
            return response({
                'total_reviews': total_reviews,
                'reviews': serializers.event_review_schema.dump(reviews, many=True),
                "metadata": {
                    "cursor": {
                        "before": cursor.before,
                        "after": cursor.after,
                        "limit": cursor.limit
                    }
                }
            })
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)

    @route('<string:event_id>/reviews/<string:review_id>', methods=['GET'])
    def get_event_review(self, event_id, review_id):

        try:
            event = models.Event.get_event_only(event_id)
            review = event.get_review(review_id)
            return response(serializers.event_review_schema.dump(review))
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_NOT_FOUND"
            }, 400)

    @route('<string:event_id>/reviews/<string:review_id>/upvotes', methods=['POST'])
    def upvote_event_review(self, event_id, review_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            event = models.Event.get_event_only(event_id)
            review = event.get_review_only(review_id)
            upvote = EventReviewUpvote(author=auth_user, review=review)
            review.upvote(upvote)
            return response({
                'review_id': review.id,
                'upvotes_count': review.upvotes_count(),
                'is_upvoted': review.is_upvoted_by(auth_user)
            })
        except exceptions.AlreadyUpvoted:
            review.remove_upvote_by(auth_user)
            return response({
                'review_id': review.id,
                'upvotes_count': review.upvotes_count(),
                'is_upvoted': review.is_upvoted_by(auth_user)
            })
        except exceptions.AlreadyDownvoted:
            return response({
                "ok": False,
                "code": "REVIEW_ALREADY_DOWNVOTED"
            }, 400)
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_NOT_FOUND"
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/reviews/<string:review_id>/upvotes', methods=['DELETE'])
    def remove_event_review_upvote(self, event_id, review_id):
        try:
            auth_user = Authenticator().get_instance().get_auth_user()
            event = models.Event.get_event_only(event_id)
            review = event.get_review_only(review_id)
            review.remove_upvote_by(auth_user)
            return response({
                'review_id': review.id,
                'upvotes_count': review.upvotes_count(),
                'is_upvoted': review.is_upvoted_by(auth_user)
            })
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_NOT_FOUND"
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/reviews/<string:review_id>/downvotes', methods=['POST'])
    def downvote_event_review(self, event_id, review_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            event = models.Event.get_event_only(event_id)
            review = event.get_review_only(review_id)
            downvote = EventReviewDownvote(author=auth_user, review=review)
            review.downvote(downvote)
            return response({
                'review_id': review.id,
                'downvotes_count': review.downvotes_count(),
                'is_downvoted': True
            })
        except exceptions.AlreadyDownvoted:
            review.remove_downvote_by(auth_user)
            return response({
                'review_id': review.id,
                'downvotes_count': review.downvotes_count(),
                'is_downvoted': False
            })
        except exceptions.AlreadyUpvoted:
            return response({
                "ok": False,
                "code": "ALREADY_DOWNVOTED_REVIEW"
            }, 400)
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_NOT_FOUND"
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/reviews/<string:review_id>/downvotes', methods=['DELETE'])
    def remove_event_review_downvote(self, event_id, review_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            event = models.Event.get_event_only(event_id)
            review = event.get_review_only(review_id)
            review.remove_downvote_by(auth_user)
            return response({
                'review_id': review.id,
                'downvotes_count': review.downvotes_count(),
                'is_downvoted': review.is_downvoted(),
                'is_downvoted': review.is_downvoted_by(auth_user)
            })
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_NOT_FOUND"
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/reviews/<string:review_id>/comments', methods=['POST'])
    def add_review_comment(self, event_id, review_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            event = models.Event.get_event_only(event_id)
            review = event.get_review_only(review_id)
            data = serializers.create_event_review_comment_schema.load(request.get_json())
            content = data['content']
            media = []
            for m in data['media'] if 'media' in data else []:
                media.append(EventReviewCommentMedia(format=m['format'], source_url=m['source_url']))
            comment = EventReviewComment(content=content, author=auth_user, media=media)
            review.add_review_comment(comment)
            return response(serializers.event_review_comment_schema.dump(comment))
        except ValidationError as e:
            return response({
                "ok": False,
                "errors": e.messages
            })
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_NOT_FOUND"
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/reviews/<string:review_id>/comments/<string:comment_id>', methods=['PUT'])
    def update_review_comment(self, event_id, review_id, comment_id):
        pass

    @route('<string:event_id>/reviews/<string:review_id>/comments/<string:comment_id>', methods=['DELETE'])
    def delete_review_comment(self, event_id, review_id, comment_id):
        pass

    @route('<string:event_id>/reviews/<string:review_id>/comments/<string:comment_id>', methods=['GET'])
    def get_review_comment(self, event_id, review_id, comment_id):
        try:
            event = models.Event.get_event_only(event_id)
            review = event.get_review_only(review_id)
            comment = review.get_comment_only(comment_id)
            return response(serializers.event_review_comment_schema.dump(comment))
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_NOT_FOUND"
            }, 400)
        except exceptions.ReviewCommentNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_NOT_FOUND"
            }, 400)

    @route('<string:event_id>/reviews/<string:review_id>/comments', methods=['GET'])
    def get_review_comments(self, event_id, review_id):
        try:
            cursor = self.get_cursor(request)
            event = models.Event.get_event_only(event_id)
            review = event.get_review_only(review_id)
            comments = review.get_review_comments(cursor)
            return response({
                "total_comments": review.get_total_event_review_comments(),
                "comments": serializers.event_review_comment_schema.dump(comments, many=True),
                'metadata': {
                    'cursor': {
                        'before': cursor.before,
                        'after': cursor.after,
                        'limit': cursor.limit
                    }
                }
            })
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_NOT_FOUND"
            }, 400)
        except exceptions.ReviewCommentNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_NOT_FOUND"
            }, 400)

    @route('<string:event_id>/reviews/<string:review_id>/comments/<string:comment_id>/upvotes', methods=['POST'])
    def upvote_event_review_comment(self, event_id, review_id, comment_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            event = models.Event.get_event_only(event_id)
            review = event.get_review_only(review_id)
            comment = review.get_comment_only(comment_id)
            comment.upvote(auth_user)
            return response({
                'ok': True,
                'comment_id': comment.id,
                'upvotes_count': comment.upvotes_count(),
                'is_upvoted': comment.is_upvoted_by(auth_user)
            })
        except exceptions.AlreadyUpvoted:
            comment.remove_upvote(auth_user)
            return response({
                'ok': True,
                'comment_id': comment.id,
                'upvote_count': comment.upvotes_count(),
                'is_upvoted': comment.is_upvoted_by(auth_user)
            })
        except exceptions.AlreadyDownvoted:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_ALREADY_DOWNVOTED"
            }, 400)
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_NOT_FOUND"
            }, 400)
        except exceptions.ReviewCommentNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_NOT_FOUND"
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/reviews/<string:review_id>/comments/<string:comment_id>/upvotes', methods=['DELETE'])
    def remove_event_review_comment_upvote(self, event_id, review_id, comment_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            event = models.Event.get_event_only(event_id)
            review = event.get_review_only(review_id)
            comment = review.get_comment_only(comment_id)
            comment.remove_upvote(auth_user)
            return response({
                'comment_id': comment.id,
                'upvote_counts': comment.upvotes_count(),
                'is_upvoted': comment.is_upvoted_by(auth_user)
            })
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_NOT_FOUND"
            }, 400)
        except exceptions.ReviewCommentNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_NOT_FOUND"
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/reviews/<string:review_id>/comments/<string:comment_id>/downvotes', methods=['POST'])
    def downvote_event_review_comment(self, event_id, review_id, comment_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            event = models.Event.get_event_only(event_id)
            review = event.get_review_only(review_id)
            comment = review.get_comment_only(comment_id)
            comment.downvote(auth_user)
            return response({
                'ok': True,
                'comment_id': comment.id,
                'downvotes_count': comment.downvotes_count(),
                'is_downvoted': comment.is_downvoted_by(auth_user)
            })
        except exceptions.AlreadyDownvoted:
            comment.remove_downvote(auth_user)
            return response({
                'ok': False,
                'comment_id': comment.id,
                'downvotes_count': comment.downvotes_count(),
                'is_downvoted': comment.is_downvoted_by(auth_user)
            })
        except exceptions.AlreadyUpvoted:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_UPVOTED"
            }, 400)
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_NOT_FOUND"
            }, 400)
        except exceptions.ReviewCommentNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_NOT_FOUND"
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/reviews/<string:review_id>/comments/<string:comment_id>/downvotes', methods=['DELETE'])
    def remove_event_review_comment_downvote(self, event_id, review_id, comment_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            event = models.Event.get_event_only(event_id)
            review = event.get_review_only(review_id)
            comment = review.get_comment_only(comment_id)
            comment.remove_downvote(auth_user)
            return response({
                'comment_id': comment.id,
                'downvotes_count': comment.downvotes_count(),
                'is_downvoted': comment.is_downvoted_by(auth_user)
            })
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_NOT_FOUND"
            }, 400)
        except exceptions.ReviewCommentNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_NOT_FOUND"
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/reviews/<string:review_id>/comments/<string:comment_id>/responses', methods=['POST'])
    def add_event_review_comment_response(self, event_id, review_id, comment_id):
        data = request.get_json()
        try:
            content = data['content']
            author = Authenticator.get_instance().get_auth_user()
            media = []
            if 'media' in data:
                for m in data['media']:
                    media.append(EventReviewCommentResponseMedia(format=m['format'], source_url=m['source_url']))
            comment_response = EventReviewCommentResponse(content=content, author=author, media=media)
            event = models.Event.get_event_only(event_id)
            review = event.get_review_only(review_id)
            comment = review.get_comment_only(comment_id)
            comment.add_response(comment_response)
            return response(serializers.event_review_comment_response_schema.dump(comment_response))
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_NOT_FOUND"
            }, 400)
        except exceptions.ReviewCommentNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_NOT_FOUND"
            }, 400)
        except ValidationError as e:
            return response({
                "ok": False,
                "code": "BAD_REQUEST",
                "errors": e.message
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/reviews/<string:review_id>/comments/<string:comment_id>/responses/<string:response_id>', methods=['PUT'])
    def update_event_review_comment_response(self, event_id, review_id, comment_id, response_id):
        pass

    @route('<string:event_id>/reviews/<string:review_id>/comments/<string:comment_id>/responses/<string:response_id>',
           methods=['DELETE'])
    def delete_event_review_comment_response(self, event_id, review_id, comment_id, response_id):
        pass

    @route('<string:event_id>/reviews/<string:review_id>/comments/<string:comment_id>/responses/<string:response_id>',
           methods=['GET'])
    def get_event_review_comment_response(self, event_id, review_id, comment_id, response_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            event = models.Event.get_event_only(event_id)
            review = event.get_review_only(review_id)
            comment = review.get_comment_only(comment_id)
            comment_response = comment.get_response(response_id)
            return response(serializers.event_review_comment_response_schema.dump(comment_response))
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_NOT_FOUND"
            }, 400)
        except exceptions.ReviewCommentNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_NOT_FOUND"
            }, 400)
        except ValidationError as e:
            return response({
                "ok": False,
                "code": "BAD_REQUEST",
                "errors": e.message
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/reviews/<string:review_id>/comments/<string:comment_id>/responses',
           methods=['GET'])
    def get_event_review_comment_responses(self, event_id, review_id, comment_id):
        try:
            cursor = self.get_cursor(request)
            event = models.Event.get_event_only(event_id)
            review = event.get_review_only(review_id)
            comment = review.get_comment_only(comment_id)
            comment_responses = comment.get_responses(cursor)
            return response({
                'ok': True,
                'total_responses': comment.get_total_responses(),
                'responses': serializers.event_review_comment_response_schema.dump(comment_responses, many=True),
                "metadata": {
                    "cursor": {
                        "before": cursor.before,
                        "after": cursor.after,
                        "limit": cursor.limit
                    }
                }
            })
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_NOT_FOUND"
            }, 400)
        except exceptions.ReviewCommentNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_NOT_FOUND"
            }, 400)
        except ValidationError as e:
            return response({
                "ok": False,
                "code": "BAD_REQUEST",
                "errors": e.message
            }, 400)

    @route('<string:event_id>/reviews/<string:review_id>/comments/<string:comment_id>/responses/<string:response_id>/upvotes',
           methods=['POST'])
    def upvote_event_review_comment_response(self, event_id, review_id, comment_id, response_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            event = models.Event.get_event_only(event_id)
            review = event.get_review_only(review_id)
            comment = review.get_comment_only(comment_id)
            comment_response = comment.get_response(response_id)
            comment_response.upvote(auth_user)
            return response({
                'ok': True,
                'response_id': comment_response.id,
                'upvotes_count': comment_response.upvotes_count(),
                'is_upvoted': comment_response.is_upvoted_by(auth_user)
            })
        except exceptions.AlreadyUpvoted:
            comment_response.remove_upvote_by(auth_user)
            return response({
                "ok": True,
                'response_id': comment_response.id,
                'upvotes_count': comment_response.upvotes_count(),
                'is_upvoted': comment_response.is_upvoted_by(auth_user)
            })
        except exceptions.AlreadyDownvoted:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_RESPONSE_DOWNVOTED"
            }, 400)
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_NOT_FOUND"
            }, 400)
        except exceptions.ReviewCommentNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewCommentResponseNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_RESPONSE_NOT_FOUND"
            }, 400)
        except ValidationError as e:
            return response({
                "ok": False,
                "code": "BAD_REQUEST",
                "errors": e.message
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route(
        '<string:event_id>/reviews/<string:review_id>/comments/<string:comment_id>/responses/<string:response_id>/upvotes',
        methods=['DELETE'])
    def remove_upvote_on_event_review_comment_response(self, event_id, review_id, comment_id, response_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            event = models.Event.get_event_only(event_id)
            review = event.get_review_only(review_id)
            comment = review.get_comment_only(comment_id)
            comment_response = comment.get_response(response_id)
            comment_response.remove_upvote_by(auth_user)
            return response({
                'response_id': comment_response.id,
                'upvotes_count': comment_response.upvotes_count(),
                'is_upvoted': comment_response.is_upvoted_by(auth_user)
            })
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_NOT_FOUND"
            }, 400)
        except exceptions.ReviewCommentNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewCommentResponseNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_RESPONSE_NOT_FOUND"
            }, 400)
        except ValidationError as e:
            return response({
                "ok": False,
                "code": "BAD_REQUEST",
                "errors": e.message
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/reviews/<string:review_id>/comments/<string:comment_id>/responses/<string:response_id>/downvotes',
           methods=['POST'])
    def downvote_event_review_comment_response(self, event_id, review_id, comment_id, response_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            event = models.Event.get_event_only(event_id)
            review = event.get_review_only(review_id)
            comment = review.get_comment_only(comment_id)
            comment_response = comment.get_response(response_id)
            comment_response.downvote(auth_user)
            return response({
                'ok': True,
                'response_id': comment_response.id,
                'downvotes_count': comment_response.downvotes_count(),
                'is_downvoted': comment_response.is_downvoted_by(auth_user)
            })
        except exceptions.AlreadyDownvoted:
            comment_response.remove_downvote_by(auth_user)
            return response({
                'ok': True,
                'response_id': comment_response.id,
                'downvotes_count': comment_response.downvotes_count(),
                'is_downvoted': comment_response.is_downvoted_by(auth_user)
            })
        except exceptions.AlreadyUpvoted:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_RESPONSE_UPVOTED"
            }, 400)
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_NOT_FOUND"
            }, 400)
        except exceptions.ReviewCommentNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewCommentResponseNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_RESPONSE_NOT_FOUND"
            }, 400)
        except ValidationError as e:
            return response({
                "ok": False,
                "code": "BAD_REQUEST",
                "errors": e.message
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/reviews/<string:review_id>/comments/<string:comment_id>/responses/<string:response_id>/downvotes',
           methods=['DELETE'])
    def remove_downvote_on_event_review_comment_response(self, event_id, review_id, comment_id, response_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            event = models.Event.get_event_only(event_id)
            review = event.get_review_only(review_id)
            comment = review.get_comment_only(comment_id)
            comment_response = comment.get_response(response_id)
            comment_response.remove_downvote(auth_user)
            return response({
                'response_id': comment_response.id,
                'downvotes_count': comment_response.downvotes_count(),
                'is_downvoted': comment_response.is_downvoted_by(auth_user)
            })
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_NOT_FOUND"
            }, 400)
        except exceptions.ReviewCommentNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_NOT_FOUND"
            }, 400)
        except exceptions.EventReviewCommentResponseNotFound:
            return response({
                "ok": False,
                "code": "EVENT_REVIEW_COMMENT_RESPONSE_NOT_FOUND"
            }, 400)
        except ValidationError as e:
            return response({
                "ok": False,
                "code": "BAD_REQUEST",
                "errors": e.message
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/purchase-tickets', methods=['POST'])
    def buy_event_tickets(self, event_id):
        try:
            data = request.get_json()
            event = models.Event.get_event_only(event_id)
            payment_info = data['payment_info']
            ticket_types = data['ticket_types']
            customer = Authenticator.get_instance().get_auth_user()
            tickets = []
            for ticket_type in ticket_types:
                ticket_type_id = ticket_type['ticket_type_id']
                ticket_qty = ticket_type['qty']
                tickets.append({
                    'ticket_type': models.EventTicketType.get_ticket_type(ticket_type_id),
                    'ticket_qty': int(ticket_qty)
                })
            models.EventTicketSaleOrder.create_order(customer, event, tickets)

            return response("")
        except exceptions.EventNotFound:
            return response({
                'ok': False,
                'code': "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.UnvailableTickets:
            return response({
                "ok": False,
                'code': 'TICKETS_UNAVAILABLE',
            }, 400)
        except ValidationError as e:
            return response({
                "ok": False,
                "code": "BAD_REQUEST",
                "errors": e.messages
            })
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/purchased-tickets', methods=['GET'])
    def get_purchased_tickets(self, event_id):
        try:
            auth_user = Authenticator.get_instance().get_auth_user()
            event = models.Event.get_event_only(event_id)
            tickets = []
            for ticket_type in event.ticket_types:
                print("ticket_types##",ticket_type.id)
                tickets.append({
                    'ticket_type': ticket_type,
                    'assigned_tickets': models.EventTicket.get_assigned_tickets_of_type(ticket_type, auth_user),
                    'unassigned_tickets': models.EventTicket.get_unassigned_tickets_of_type(ticket_type, auth_user),
                    'gifted_tickets': models.EventTicket.get_gifted_tickets(ticket_type, auth_user)
                })
            grouped_tickets = serializers.attendee_ticket_grouped_by_type_schema.dump(tickets, many=True)
            return response({
                "ok": True,
                "tickets": grouped_tickets
            })
        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)
        except exceptions.NotAuthUser:
            return self.not_auth_response()

    @route('<string:event_id>/attendees', methods=['GET'])
    def get_event_attendees(self, event_id):
        try:
            cursor = self.get_cursor(request)
            event = models.Event.get_event_only(event_id)
            attendees = event.get_attendees(cursor=cursor)
            total_attendees_count = event.get_total_attendees()

            return response({
                "ok": True,
                "attendees": serializers.user_schema.dump(attendees, many=True),
                "attendees_count": total_attendees_count,
                "metadata": {
                    "cursor": {
                        "before": cursor.before,
                        "after": cursor.after,
                        "limit": cursor.limit
                    }
                }
            })

        except exceptions.EventNotFound:
            return response({
                "ok": False,
                "code": "EVENT_NOT_FOUND"
            }, 400)

    @route('/search', methods=['GET'])
    def search_events(self):
        auth_user = Authenticator.get_instance().get_auth_user_without_auth_check()
        cursor = self.get_cursor(request)
        query = request.args.get('q')
        category = request.args.get('category')
        country = request.args.get('country')
        period = request.args.get('time')

        if query:
            category = models.EventCategory.find_category_by_slug(category)

            search_result = models.Event.search_for_events(query, category=category, country=country, period=period,
                                                           cursor=cursor)
            search_result_total = models.Event.search_for_events_total(query, category=category, country=country,
                                                                       period=period)
            if auth_user:
                events = serializers.event_schema.dump(search_result, many=True)
            else:
                events = serializers.event_anon_schema.dump(search_result, many=True)
        else:
            # @todo show popular events
            events = None
            search_result_total = 0

        return response({
            "ok": True,
            "events": events,
            "total_events": search_result_total,
            "metadata": {
                "cursor": {
                    "before": cursor.before,
                    "after": cursor.after,
                    "limit": cursor.limit
                }
            }
        })


    @route('/<string:event_id>/media', methods=['POST'])
    def upload_media(self, event_id):
        try:
            event = models.Event.get_event_only(event_id)
            if request.method == 'POST':
                uploaded_media = []
                for key in request.files:
                    file_to_upload = request.files[key]
                    media_file = models.EventMedia.create()
                    resp = cloudinary_upload(file_to_upload, public_id=media_file.filename)
                    print('resp##', resp)
                    media_file.add_format(resp['format'])
                    media_file.add_source_url(resp['url'])
                    media_file.add_public_id(resp['public_id'])
                    event.media.append(media_file)
                    uploaded_media.append(media_file)
                db.session.commit()
                return response(serializers.event.EventMediaSchema().dump(uploaded_media, many=True))
        except exceptions.EventNotFound:
            return response({
                'ok': False,
                'code': 'EVENT_NOT_FOUND'
            }, 400)
        except KeyError:
            return response({
                'ok': False,
                'code': "IMAGE field 'image' NOT FOUND"
            }, 400)

    @route('/<string:event_id>/media/<string:media_id>', methods=['DELETE'])
    def delete_media(self, event_id, media_id):

        try:
            event = Event.get_event_only(event_id)
            file = event.get_media_file(media_id)
            file.delete()
            cloudinary_api.delete_resources([file.public_id])
            return response(None)
        except exceptions.EventNotFound:
            return response({
                'ok': False,
                'code': 'EVENT_NOT_FOUND'
            }, 400)
        except exceptions.MediaNotFound:
            return response({
                'ok': False,
                'code': 'MEDIA_NOT_FOUND'
            }, 400)

    @route('/<string:event_id>/media/<string:media_id>', methods=['PUT'])
    def make_media_file_cover_image(self, event_id, media_id):
        try:
            event = Event.get_event_only(event_id)
            file = event.get_media_file(media_id)
            event.set_as_poster(file)
            return response(serializers.event.EventMediaSchema().dump(file))
        except exceptions.EventNotFound:
            return response({
                'ok': False,
                'code': 'EVENT_NOT_FOUND'
            }, 400)
        except exceptions.MediaNotFound:
            return response({
                'ok': False,
                'code': 'MEDIA_NOT_FOUND'
            }, 400)