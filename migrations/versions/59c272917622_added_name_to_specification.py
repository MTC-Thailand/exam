"""added name to specification

Revision ID: 59c272917622
Revises: add5acbedeb5
Create Date: 2021-11-27 12:36:35.428484

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '59c272917622'
down_revision = 'add5acbedeb5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('specifications', sa.Column('name', sa.String(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('specifications', 'name')
    # ### end Alembic commands ###