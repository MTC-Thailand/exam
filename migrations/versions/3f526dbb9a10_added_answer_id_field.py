"""added answer ID field

Revision ID: 3f526dbb9a10
Revises: 13d82fa75d11
Create Date: 2020-10-02 14:25:59.782197

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3f526dbb9a10'
down_revision = '13d82fa75d11'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('items', sa.Column('answer_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'items', 'choices', ['answer_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'items', type_='foreignkey')
    op.drop_column('items', 'answer_id')
    # ### end Alembic commands ###