from sqlalchemy.orm import load_only, joinedload

from api.repositories.base import Repository
from api.repositories.event import EventRepository
from api.models.event import EventTicket


class EventTicketRepository(Repository):

    def has_ticket(self, event_id, ticket_id):
       return self.session.query(EventTicket).filter_by(id=ticket_id, event_id=event_id).count()

    def add_ticket(self, ticket):
        self.session.add(ticket)
        self.session.commit()
        return ticket

    def remove_ticket(self, ticket_id):
        return self.query(EventTicket).filter_by(id=ticket_id).delete()

    def update_ticket(self, ticket_id, data):
        return self.query(EventTicket).filter_by(id=ticket_id).update(data)


