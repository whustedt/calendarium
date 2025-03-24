"""Added quote functionality

Revision ID: 1a8bbf732309
Revises: 25858de709e5
Create Date: 2025-03-02 13:18:54.481040

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '1a8bbf732309'
down_revision = '25858de709e5'
branch_labels = None
depends_on = None

def upgrade():
    # Connect to the current target database
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    # Check if the 'entry' table already exists
    if 'quote' not in inspector.get_table_names():
        op.create_table('quote',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('text', sa.String(length=1000), nullable=False),
            sa.Column('author', sa.String(length=200), nullable=False),
            sa.Column('category', sa.String(length=100), nullable=True),
            sa.Column('url', sa.String(length=1000), nullable=True),
            sa.Column('last_updated_by', sa.String(length=130), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    else:
        pass  # If the table exists, do nothing

def downgrade():
    # Connect to the current target database
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    # Check if the 'entry' table exists before dropping it
    if 'quote' in inspector.get_table_names():
        op.drop_table('quote')
    else:
        pass  # If the table doesn't exist, do nothing