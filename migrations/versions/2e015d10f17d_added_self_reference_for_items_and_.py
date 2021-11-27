"""added self reference for items and choices

Revision ID: 2e015d10f17d
Revises: 73a48deee1f3
Create Date: 2021-10-10 15:09:53.909807

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e015d10f17d'
down_revision = '73a48deee1f3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('choices', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'choices', 'choices', ['parent_id'], ['id'])
    op.add_column('items', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'items', 'items', ['parent_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'items', type_='foreignkey')
    op.drop_column('items', 'parent_id')
    op.drop_constraint(None, 'choices', type_='foreignkey')
    op.drop_column('choices', 'parent_id')
    # ### end Alembic commands ###