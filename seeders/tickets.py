import random
import factory
from api.models import event as model
# from api.db_config import Session
from api.models.event import db


# session = Session()

session = db.session

events = session.query(model.Event).all()
users = session.query(model.User).all()


class EventTicketSaleLineFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = model.EventTicketSaleLine
        sqlalchemy_session = session   # the SQLAlchemy session object

    # ticket_type = factory.LazyFunction(lambda obj: factory.Iterator(obj.sale.event.tickets))
    ref = '#TICKET123'


class EventTicketSaleFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = model.EventTicketSale
        sqlalchemy_session = session   # the SQLAlchemy session object

    customer = factory.Iterator(users)
    event = factory.Iterator(events, cycle=False)
    total_qty = random.randint(1, 10)


def seed():

    sales = EventTicketSaleFactory.build_batch(20)

    print("sales", sales)

    for sale in sales:
        sale_lines = []
        for i in range(1, random.randint(2, 8)):
            if len(sale.event.ticket_types) > 0:
                ticket_type = sale.event.ticket_types[random.randint(0, len(sale.event.tickets) - 1)]
                line = model.EventTicketSaleLine(sale=sale, ticket_type=ticket_type, ref="REF####")
                sale_lines.append(line)
        sale.sale_lines = sale_lines
        sale.total_qty = len(sale_lines)

    session.add_all(sales)
    session.commit()


def seed_discount_types():
    discount_types = []
    for discount_type in ["Early Purchase", "Number of Purchased Tickets"]:
        discount_types.append(model.EventTicketDiscountType(name=discount_type))

    session.add_all(discount_types)
    session.commit()


if __name__ == "__main__":
    seed_discount_types()
    # seed()
    # event = session.query(model.Event).limit(5).first()
    # print("evnet", event)
    # sale = event.ticket_sales[0]
    # print('customer', sale.customer)
    # print('sales_lines', len(sale.sale_lines))
    # print('sale_tickets_sold', sale.total_qty)

    # result = session.query(model.EventTicketSaleLine).options(
    #     joinedload(model.EventTicketSaleLine.sale),
    # ).limit(1).all()
    #
    # print("result", result)