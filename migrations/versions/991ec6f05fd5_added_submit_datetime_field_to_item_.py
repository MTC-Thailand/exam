"""added submit datetime field to item model

Revision ID: 991ec6f05fd5
Revises: cda53d5d1e84
Create Date: 2020-11-14 16:40:13.599612

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '991ec6f05fd5'
down_revision = 'cda53d5d1e84'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('items', sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('items', 'submitted_at')
    # ### end Alembic commands ###
