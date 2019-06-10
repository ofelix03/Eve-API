"""update EventAttendee table

Revision ID: bec605ee2588
Revises: 17159eabe5bb
Create Date: 2019-03-18 22:09:25.457911

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bec605ee2588'
down_revision = '17159eabe5bb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('event_attendees', sa.Column('event_id', sa.String(), nullable=True))
    op.add_column('event_attendees', sa.Column('sale_order_id', sa.String(), nullable=True))
    op.drop_constraint('event_attendees_sale_line_id_fkey', 'event_attendees', type_='foreignkey')
    op.create_foreign_key(None, 'event_attendees', 'events', ['event_id'], ['id'], onupdate='CASCADE')
    op.create_foreign_key(None, 'event_attendees', 'ticket_sales', ['sale_order_id'], ['id'], onupdate='CASCADE')
    op.drop_column('event_attendees', 'sale_line_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('event_attendees', sa.Column('sale_line_id', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'event_attendees', type_='foreignkey')
    op.drop_constraint(None, 'event_attendees', type_='foreignkey')
    op.create_foreign_key('event_attendees_sale_line_id_fkey', 'event_attendees', 'ticket_sale_lines', ['sale_line_id'], ['id'], onupdate='CASCADE')
    op.drop_column('event_attendees', 'sale_order_id')
    op.drop_column('event_attendees', 'event_id')
    # ### end Alembic commands ###
