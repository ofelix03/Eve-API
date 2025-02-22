"""empty message

Revision ID: 8a17cfc7f057
Revises: 5d4f1d63e410
Create Date: 2020-05-27 21:19:37.576274

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a17cfc7f057'
down_revision = '5d4f1d63e410'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('brand_founders',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('brand_id', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_brand_founders_name'), 'brand_founders', ['name'], unique=False)
    op.drop_column('brands', 'founder')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('brands', sa.Column('founder', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_index(op.f('ix_brand_founders_name'), table_name='brand_founders')
    op.drop_table('brand_founders')
    # ### end Alembic commands ###
