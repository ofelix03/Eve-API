"""update event_sponsors table

Revision ID: b5e94155e96e
Revises: 02cfc347cd34
Create Date: 2018-12-15 08:13:36.766721

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5e94155e96e'
down_revision = '02cfc347cd34'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('event_sponsors', sa.Column('email', sa.String(), nullable=True))
    op.add_column('event_sponsors', sa.Column('phone_number', sa.String(), nullable=True))
    op.create_index(op.f('ix_event_sponsors_email'), 'event_sponsors', ['email'], unique=False)
    op.create_index(op.f('ix_event_sponsors_phone_number'), 'event_sponsors', ['phone_number'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_event_sponsors_phone_number'), table_name='event_sponsors')
    op.drop_index(op.f('ix_event_sponsors_email'), table_name='event_sponsors')
    op.drop_column('event_sponsors', 'phone_number')
    op.drop_column('event_sponsors', 'email')
    # ### end Alembic commands ###
