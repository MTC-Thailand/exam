"""added status field to the item model

Revision ID: cc412f397c31
Revises: 80da16460956
Create Date: 2020-10-03 11:17:31.213051

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc412f397c31'
down_revision = '80da16460956'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('items', sa.Column('status', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('items', 'status')
    # ### end Alembic commands ###
