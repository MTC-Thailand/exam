"""added assoc table for items and groups

Revision ID: 98749ee7b72c
Revises: 7574a100cef3
Create Date: 2021-11-27 13:55:40.057841

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '98749ee7b72c'
down_revision = '7574a100cef3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('assoc_group_items',
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.Column('item_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['item_groups.id'], ),
    sa.ForeignKeyConstraint(['item_id'], ['items.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('assoc_group_items')
    # ### end Alembic commands ###