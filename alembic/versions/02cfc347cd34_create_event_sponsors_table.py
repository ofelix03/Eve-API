"""create event_sponsors table

Revision ID: 02cfc347cd34
Revises: 3c9fb7cb8285
Create Date: 2018-12-15 08:01:43.180862

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '02cfc347cd34'
down_revision = '3c9fb7cb8285'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('event_sponsors',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('brand_id', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('event_id', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('event_sponsors')
    # ### end Alembic commands ###
