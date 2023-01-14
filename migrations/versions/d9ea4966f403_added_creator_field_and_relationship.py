"""added creator field and relationship

Revision ID: d9ea4966f403
Revises: cf019cabe493
Create Date: 2023-01-14 10:05:05.577262

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd9ea4966f403'
down_revision = 'cf019cabe493'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('random_sets_testdrive', schema=None) as batch_op:
        batch_op.add_column(sa.Column('creator_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'users', ['creator_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('random_sets_testdrive', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('creator_id')

    # ### end Alembic commands ###
