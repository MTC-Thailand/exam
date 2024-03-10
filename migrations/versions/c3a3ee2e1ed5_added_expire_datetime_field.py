"""added expire datetime field

Revision ID: c3a3ee2e1ed5
Revises: effc31584857
Create Date: 2024-01-06 14:05:59.738043

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3a3ee2e1ed5'
down_revision = 'effc31584857'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('items', sa.Column('expired_at', sa.DateTime(timezone=True), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('items', 'expired_at')
    # ### end Alembic commands ###