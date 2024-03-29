"""added choices order field

Revision ID: 86535560a83f
Revises: ad60b3290e70
Create Date: 2022-08-27 14:03:43.650240

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '86535560a83f'
down_revision = 'ad60b3290e70'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('random_item_sets', sa.Column('choices_order', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('random_item_sets', 'choices_order')
    # ### end Alembic commands ###
