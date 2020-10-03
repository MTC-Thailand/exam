"""added answer field to the choice model

Revision ID: 1d52b9c397bf
Revises: 4ffa30b0de5e
Create Date: 2020-10-03 14:44:25.485300

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1d52b9c397bf'
down_revision = '4ffa30b0de5e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('choices', sa.Column('answer', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('choices', 'answer')
    # ### end Alembic commands ###
