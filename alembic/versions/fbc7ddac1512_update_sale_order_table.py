"""update sale order table

Revision ID: fbc7ddac1512
Revises: 222acbfdd099
Create Date: 2019-05-28 15:38:00.325785

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fbc7ddac1512'
down_revision = '222acbfdd099'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ticket_sales', sa.Column('net_amount', sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ticket_sales', 'net_amount')
    # ### end Alembic commands ###
