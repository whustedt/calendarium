"""Initial setup

Revision ID: 61fac01b7ce5
Revises: 
Create Date: 2024-06-03 15:28:32.677801

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '61fac01b7ce5'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Connect to the current target database
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    # Check if the 'entry' table already exists
    if 'entry' not in inspector.get_table_names():
        op.create_table('entry',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('date', sa.String(length=100), nullable=False),
            sa.Column('category', sa.String(length=100), nullable=False),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('description', sa.String(length=1000), nullable=True),
            sa.Column('image_filename', sa.String(length=100), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    else:
        pass  # If the table exists, do nothing

def downgrade():
    # Connect to the current target database
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    # Check if the 'entry' table exists before dropping it
    if 'entry' in inspector.get_table_names():
        op.drop_table('entry')
    else:
        pass  # If the table doesn't exist, do nothing