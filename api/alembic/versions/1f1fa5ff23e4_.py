"""empty message

Revision ID: 1f1fa5ff23e4
Revises: caac35060cb9
Create Date: 2020-06-12 16:21:42.417230

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1f1fa5ff23e4'
down_revision = 'caac35060cb9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('venue_type', sa.String(), nullable=True))
    op.create_index(op.f('ix_events_venue_type'), 'events', ['venue_type'], unique=False)
    op.drop_index('ix_events_is_online', table_name='events')
    op.drop_column('events', 'is_online')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('is_online', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.create_index('ix_events_is_online', 'events', ['is_online'], unique=False)
    op.drop_index(op.f('ix_events_venue_type'), table_name='events')
    op.drop_column('events', 'venue_type')
    # ### end Alembic commands ###
