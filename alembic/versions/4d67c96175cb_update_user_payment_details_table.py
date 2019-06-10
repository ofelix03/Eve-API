"""update user payment details table

Revision ID: 4d67c96175cb
Revises: f4c0bb94f7b5
Create Date: 2019-05-19 14:21:23.373577

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d67c96175cb'
down_revision = 'f4c0bb94f7b5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_payment_details', sa.Column('payment_type', sa.String(), nullable=True))
    op.drop_column('user_payment_details', 'type')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_payment_details', sa.Column('type', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('user_payment_details', 'payment_type')
    # ### end Alembic commands ###
