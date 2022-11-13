"""increased the size of the secret hash

Revision ID: f48a79498618
Revises: 74b4a4a2f4c7
Create Date: 2022-08-28 14:34:55.766565

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f48a79498618'
down_revision = '74b4a4a2f4c7'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('api_clients', column_name='secret_hash', type_=sa.String(255))


def downgrade():
    op.alter_column('api_clients', column_name='secret_hash', type_=sa.String(32))
