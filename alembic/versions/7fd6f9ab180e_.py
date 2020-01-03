"""empty message

Revision ID: 7fd6f9ab180e
Revises: d05851a05863
Create Date: 2019-12-30 15:38:33.770731

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7fd6f9ab180e'
down_revision = 'd05851a05863'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('media',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('filename', sa.String(), nullable=True),
    sa.Column('source_url', sa.String(), nullable=True),
    sa.Column('format', sa.String(), nullable=True),
    sa.Column('public_id', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('media')
    # ### end Alembic commands ###
