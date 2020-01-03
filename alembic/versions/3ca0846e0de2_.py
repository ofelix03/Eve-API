"""empty message

Revision ID: 3ca0846e0de2
Revises: 9631284ddb87
Create Date: 2019-12-30 12:53:24.146571

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3ca0846e0de2'
down_revision = '9631284ddb87'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('event_media', sa.Column('public_id', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('event_media', 'public_id')
    # ### end Alembic commands ###
