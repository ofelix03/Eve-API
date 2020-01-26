
from sqlalchemy.orm import joinedload
from api.repositories import exceptions
from api.repositories.base import Repository
from api.models.event import (
    EventTicketSaleOrder,
    EventTicketSaleLine,
    EventTicketType,
    EventTicketDiscountType,
    AttendeeTicket,
    EventTicketTypeAssignment,
    AttendeeTicketGroupedByType
)


class TicketTypeNotFound(Exception):
    pass


class TicketRepository(Repository):

    def transform_to_attendee_ticket(self, sale_line):
        return AttendeeTicket(sale_line)

    def __init__(self):
        self.attendee = None
        self.event = None
        super(TicketRepository, self).__init__()

    def assign_ticket(self, sale_line=None, assigned_by=None, assign_to=None):
        ticket_assignment = EventTicketTypeAssignment(assigned_by=assigned_by, assigned_to=assign_to)
        sale_line.assignment += [ticket_assignment]
        self.session.commit()

    def has_ticket(self, ticket_id):
        count = self.session.query(EventTicketSaleLine).filter(EventTicketSaleLine.id==ticket_id).count()
        return bool(count)

    def has_unassigned_tickets(self, ticket_type_id, owner_id):
        count = self.session.query(EventTicketSaleLine) \
            .options(joinedload(EventTicketSaleLine.sale)) \
            .filter(EventTicketSaleLine.ticket_type_id == ticket_type_id) \
            .filter(EventTicketSaleOrder.customer_id == owner_id) \
            .filter(
                ~EventTicketSaleLine.assignment.any(EventTicketTypeAssignment.sale_line_id == EventTicketSaleLine.id)) \
            .count()
        return bool(count)

    def get_unassigned_tickets(self, ticket_type_id, owner_id):
        count = self.session.query(EventTicketSaleLine) \
            .options(joinedload(EventTicketSaleLine.sale)) \
            .filter(EventTicketSaleLine.ticket_type_id == ticket_type_id) \
            .filter(EventTicketSaleOrder.customer_id == owner_id) \
            .filter(
                ~EventTicketSaleLine.assignment.any(EventTicketTypeAssignment.sale_line_id == EventTicketSaleLine.id)) \
            .count()
        return count

    def get_unassigned_tickets(self, ticket_type_id, owner_id):
        sale_lines = self.session.query(EventTicketSaleLine) \
            .options(joinedload(EventTicketSaleLine.sale)) \
            .filter(EventTicketSaleLine.ticket_type_id==ticket_type_id) \
            .filter(EventTicketSaleOrder.customer_id==owner_id) \
            .filter(~EventTicketSaleLine.assignment.any(EventTicketTypeAssignment.sale_line_id==EventTicketSaleLine.id)) \
            .all()

        return list(map(lambda line: self.transform_to_attendee_ticket(line), sale_lines))

    def get_ticket(self, ticket_id):

        if not self.has_ticket(ticket_id):
            raise exceptions.TicketNotFound()

        sale_line = self.session.query(EventTicketSaleLine) \
            .filter(EventTicketSaleLine.id==ticket_id) \
            .first()
        if not sale_line:
            raise exceptions.TicketNotFound()
        return AttendeeTicket(sale_line=sale_line)

    def has_ticket_type(self, ticket_type_id):
        count = self.session.query(EventTicketType).filter(EventTicketType.id == ticket_type_id).count()
        return bool(count)

    def get_ticket_type(self, ticket_type_id):
        if not self.has_ticket_type(ticket_type_id):
            raise exceptions.TicketTypeNotFound()
        return self.session.query(EventTicketType).filter(EventTicketType.id==ticket_type_id).first()

    def group_tickets_by_type(self, sales):
        groups = []
        if len(sales) == 0:
            return []

        event = sales[0].event
        ticket_types = event.ticket_types
        attendee_tickets = []
        sale_lines = []

        for sale in sales:
            sale_lines += sale.sale_lines

        print("saleLines##", sale_lines)

        for line in sale_lines:
            attendee_tickets.append(AttendeeTicket(line))

        for ticket_type in ticket_types:
            assigned_tickets = list(filter(lambda ticket: ticket.is_assigned and ticket.type.is_same(ticket_type),
                                           attendee_tickets))
            unassigned_tickets = list(filter(
                    lambda ticket: ticket.is_assigned is False and ticket.type.is_same(ticket_type),
                    attendee_tickets))


            print("assigned##", assigned_tickets)
            print("unassignd##", unassigned_tickets)

            groups.append(
                    AttendeeTicketGroupedByType(type=ticket_type,
                                                assigned_tickets=assigned_tickets,
                                                unassigned_tickets=unassigned_tickets
                                                )
            )
        return groups

    def for_attendee(self, attendee):
        self.attendee = attendee
        return self

    def for_event(self, event):
        self.event = event
        return self

    def get_ticket_type(self, ticket_type_id):
        ticket_type = self.query(EventTicketType).filter(EventTicketType.id==ticket_type_id).first()
        return ticket_type

    def has_ticket_type(self, ticket_type_id):
        ticket_type =  self.get_ticket_type(ticket_type_id)
        return bool(ticket_type)

    def get_tickets(self):
        if self.attendee and self.event:
            return self._get_user_event_tickets(self.attendee, self.event)
        elif self.attendee:
            return self._get_user_tickets(self.attendee)
        return False

    def _get_user_event_tickets(self, attendee, event):
        event_sales = self.session.query(EventTicketSaleOrder). \
            filter(EventTicketSaleOrder.user_id==attendee). \
            filter(EventTicketSaleOrder.event_id==event).options(
                joinedload(EventTicketSaleOrder.sale_lines, innerjoin=True)
                    .joinedload(EventTicketSaleLine.ticket_type, innerjoin=True),
                joinedload(EventTicketSaleOrder.event, innerjoin=True),
                joinedload(EventTicketSaleOrder.customer, innerjoin=True),
                    ).all()

        return self._build_attendee_ticket_objects(event_sales)

    def _get_user_tickets(self, attendee):
        event_sales = self.session.query(EventTicketSaleOrder) \
            .filter(EventTicketSaleOrder.user_id == attendee) \
            .options(
                joinedload(EventTicketSaleOrder.sale_lines, innerjoin=True)
                    .joinedload(EventTicketSaleLine.ticket_type, innerjoin=True),
                joinedload(EventTicketSaleOrder.event, innerjoin=True),
                joinedload(EventTicketSaleOrder.customer, innerjoin=True),
                    ).all()

        return self._build_attendee_ticket_objects(event_sales)

    def assign_ticket(self, ticket_id, assign_to_id):
        sale_line = self.session.query(EventTicketSaleLine).get(ticket_id)
        if sale_line:
            sale_line.assign_ticket(assign_to_id)
            return sale_line.assignment[0]
        else:
            return False

    def unassign_ticket(self, ticket_id, unassigned_from_id):
        if self.attendee:
            query = self.session.query(EventTicketTypeAssignment) \
                .filter(EventTicketTypeAssignment.sale_line_id==ticket_id) \
                .filter(EventTicketTypeAssignment.assigned_to_user_id==unassigned_from_id) \
                .filter(EventTicketTypeAssignment.assigned_by_user_id==self.attendee)

            assignment = query.first()
            if assignment:
                query.delete()
            else:
                # raise exception, assigned ticket not found
                pass

    def has_ticket(self, ticket_id):
        ticket = self.session.query(EventTicketSaleLine).get(ticket_id)
        return ticket

    def remove_ticket_type(self, ticket_type_id):
        if not self.has_ticket_type(ticket_type_id):
            raise TicketTypeNotFound()

        self.query(EventTicketType).filter(EventTicketType.id==ticket_type_id).delete()
        self.session.commit()

    def _build_attendee_ticket_objects(self, event_sales):
        tickets = []
        for sale in event_sales:
            sale_tickets = []
            for line in sale.sale_lines:
                ticket_data = {
                    'id': line.id,
                    'ref': line.ref,
                    'owner': sale.customer,
                    'type': line.ticket_type,
                    'event': sale.event,
                    'assigned_to': line.assignment[0].assigned_to if line.assignment else None,
                    'is_assigned': bool(line.assignment),
                }
                sale_tickets.append(AttendeeTicket(ticket_data))
            tickets += sale_tickets
        return tickets

    def get_discount_types(self):
        return self.session.query(EventTicketDiscountType).all()

    def has_ticket_discount_type(self, discount_type_id):
        type = self.query(EventTicketDiscountType) \
            .filter(EventTicketDiscountType.id==discount_type_id) \
            .first()
        return bool(type)

