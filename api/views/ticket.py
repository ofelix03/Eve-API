from . import *
from api.views.auth_base import AuthBaseView
from api.serializers.event import AttendeeTicketGroupedByTypeSchema, CreateTicketTypeDiscountSchema
from api.repositories.ticket import TicketRepository
from api.models import event as models
from api.serializers.event import EventTicketDiscountTypeSchema, AttendeeTicketSchema
from api.auth.authenticator import Authenticator
from api.repositories import exceptions
from api.models.event import db
from api.models.domain.user_payment_info import DiscountTypes

session = db.session

event_ticket_discount_type_schema = EventTicketDiscountTypeSchema()
create_ticket_discount_schema = CreateTicketTypeDiscountSchema()
attendee_ticket_schema = AttendeeTicketSchema()


class TicketsView(AuthBaseView):

    def index(self):
        """
        Get tickets using all or either of ticket_owner_id and event_id parameters

        Parameters:
            ticket_owner_id
            event_id
        """
        ticket_owner_id = None
        event_id = None

        response_payload = {
            'tickets': []
        }

        if request.args:
            if 'ticket_owner_id' in request.args:
                ticket_owner_id = request.args.get('ticket_owner_id')

            if 'event_id' in request.args:
                event_id = request.args.get('event_id')

            if ticket_owner_id and event_id:
                tickets = TicketRepository(session=session).for_attendee(ticket_owner_id).for_event(event_id).get_tickets()
            elif ticket_owner_id:
                tickets = TicketRepository(session=session).for_attendee(ticket_owner_id).get_tickets()

            grouped_tickets = []
            if tickets:
                ticket_types = tickets[0].event.tickets
                for ticket_type in ticket_types:
                    grouped_ticket = models.AttendeeTicketGroupedByType(type=ticket_type.name)
                    grouped_ticket.add_assigned_tickets(
                        filter(lambda ticket: ticket.is_assigned and ticket.type.id == ticket_type.id, tickets))
                    grouped_ticket.add_unassigned_tickets(
                        filter(lambda ticket: not ticket.is_assigned and ticket.type.id == ticket_type.id, tickets))
                    grouped_tickets.append(grouped_ticket)
            response_payload['tickets'] = AttendeeTicketGroupedByTypeSchema().dump(grouped_tickets, many=True)
            return response(response_payload)
        else:
            response_payload = {
                'message': 'Bad request',
                'errors': 'Required parameter missing. Either ticket_owner_id or event_id parameter',
            }
            return response(response_payload)

    @route('/assign', methods=['POST'])
    def assign_ticket(self):

        req_payload = request.get_json()
        auth_user = Authenticator.get_instance().get_auth_user()

        if req_payload:
            if 'assign_to_id' not in req_payload and 'email' not in req_payload:
                return response({
                    "errors": {
                        "message": "assign_to_id or email field required"
                    }
                }, 400)

            if 'assign_to_id' in req_payload:
                assign_to = models.User.get_user((req_payload['assign_to_id']))
                if not assign_to:
                    return response({
                        "ok": False,
                        "code": "ASSIGN_TO_USER_NOT_FOUND"
                    }, 400)

            if 'email' in req_payload:
                # create a ghost user and use id to proceed with ticket assignmnet
                # send an email to ghost user to officially signup to Eve
                assign_to = models.User.create_ghost_user(req_payload['email'])

            if 'ticket_type_id' not in req_payload:
                return response({
                    "ok": False,
                    "code": "TICKET_TYPE_NOT_FOUND",
                }, 400)

            try:
                ticket_type = models.EventTicketType.get_ticket_type(req_payload['ticket_type_id'])
                unassigned_tickets = models.EventTicket.get_user_unassigned_tickets_for_event(ticket_type.event, auth_user)
                if unassigned_tickets:
                    ticket = unassigned_tickets[0]
                    ticket.assign_to(assign_to)
                    models.Notification.create(notification_type=models.Notifications.TICKET_ASSIGNED.value,
                                                              recipient=assign_to,
                                                              actor=auth_user,
                                                              event=ticket.event)
                    if assign_to.is_ghost:
                        # @todo send an email to ghost to signup and redeem is assigned ticket for event
                        pass
                return response(attendee_ticket_schema.dump(ticket))
            except exceptions.TicketTypeNotFound:
                return response({
                    "ok": False,
                    "code": "TICKET_TYPE_NOT_FOUND"
                }, 400)
            except exceptions.AlreadyHasTicketsForEvent:
                return response({
                    "ok": False,
                    "code": "USER_ALREADY_HAS_TICKETS"
                }, 400)

    @route('/<string:ticket_id>/unassign', methods=['PUT'])
    def unassign_ticket(self, ticket_id):
        req_payload = request.get_json()
        auth_user = Authenticator.get_instance().get_auth_user()
        if req_payload:
            if 'assigned_to_id' not in req_payload:
                return response({
                    "ok": False,
                    "code": "ASSIGN_TO_USER_NOT_FOUND"
                }, 400)

            if 'assigned_to_id' in req_payload:
                assigned_to = models.User.get_user(req_payload['assigned_to_id'])
                if not assigned_to:
                    return response({
                        "ok": False,
                        "code": "ASSIGN_TO_USER_NOT_FOUND"
                    }, 400)

            ticket = models.EventTicket.get_ticket(ticket_id)
            if not ticket.is_owned_by(auth_user):
                return response({
                    "ok": False,
                    "code": "NOT_TICKET_OWNER"
                }, 400)

            try:
                ticket.unassign_from(assigned_to)
                models.Notifications.ticket_unassigned_message(ticket, auth_user)
                models.Notification.create(notification_type=models.Notifications.TICKET_ASSIGNMENT_REVOKED.value,
                                           recipient=assigned_to,
                                           actor=auth_user,
                                           event=ticket.event)
            except exceptions.TicketNotAssignedToUser:
                return response({
                    "ok": False,
                    "code": "TICKET_NOT_ASSIGNED"
                }, 400)
            ticket = models.EventTicket.get_ticket(ticket.id)
            return response(attendee_ticket_schema.dump(ticket))

    @route('/discount_types', methods=['GET'])
    def get_discount_types(self):
        discount_types = [{
            'id': DiscountTypes.EARLY_PURCHASE,
            'name': 'Early Purchase'
        }, {
            'id': DiscountTypes.NUMBER_OF_PURCHASED_TICKETS,
            'name': 'Number of Purchased Tickets'
        }]
        # discount_types = TicketRepository().set_session(session).get_discount_types()
        return response({
            "ok": True,
            "discount_types": event_ticket_discount_type_schema.dump(discount_types, many=True)
        })