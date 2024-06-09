from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import select, text
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision = '304d6ba3c795'
down_revision = '1908d77a0412'
branch_labels = None
depends_on = None

def column_exists(table, column):
    """ Check if a column exists in the table using SQLite's PRAGMA table_info. """
    conn = op.get_bind()
    res = conn.execute(text(f"PRAGMA table_info({table})"))
    columns = [row[1] for row in res.fetchall()]
    return column in columns

metadata = sa.MetaData()

# Define tables using metadata for clearer reference
category_table = sa.Table(
    'category', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('name', sa.String(100), nullable=False),
    sa.Column('symbol', sa.String(10)),
    sa.Column('color_hex', sa.String(10)),
    sa.Column('repeat_annually', sa.Boolean),
    sa.Column('display_celebration', sa.Boolean),
    sa.Column('is_protected', sa.Boolean),
)

entry_table = sa.Table(
    'entry', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('category', sa.String(100)),
    sa.Column('category_id', sa.Integer)  # New category ID foreign key
)

def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    # Create Category table if not exists
    if not bind.dialect.has_table(bind, 'category'):
        op.create_table(
            'category',
            sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('symbol', sa.String(length=10), nullable=False),
            sa.Column('color_hex', sa.String(length=10), nullable=False),
            sa.Column('repeat_annually', sa.Boolean(), nullable=False),
            sa.Column('display_celebration', sa.Boolean(), nullable=False),
            sa.Column('is_protected', sa.Boolean(), nullable=False),
            sa.UniqueConstraint('name')
        )

        # Default and additional categories
        categories = [
            {'name': "Cake", 'symbol': "🍰", 'color_hex': "#FF8A65", 'repeat_annually': False, 'display_celebration': False, 'is_protected': False},
            {'name': "Birthday", 'symbol': "🥳", 'color_hex': "#AED581", 'repeat_annually': True, 'display_celebration': True, 'is_protected': True},
            {'name': "Release", 'symbol': "🚀", 'color_hex': "#42A5F5", 'repeat_annually': False, 'display_celebration': False, 'is_protected': False},
            {'name': "Custom", 'symbol': "✨", 'color_hex': "#4DD0E1", 'repeat_annually': False, 'display_celebration': False, 'is_protected': False},
        ]
        op.bulk_insert(category_table, categories)

    session.commit()

    # Map existing categories to ensure a match is found, otherwise use "Custom"
    categories = session.execute(
        select(category_table.c.id, category_table.c.name)
    ).fetchall()
    category_map = {name.lower(): id for id, name in categories}
    custom_category_id = category_map['custom']  # Ensure there is a category named 'Custom'

    # Add category_id column to Entry table if not exists
    with op.batch_alter_table('entry', schema=None) as batch_op:
        if not column_exists('entry', 'category_id'):
            batch_op.add_column(sa.Column('category_id', sa.Integer, nullable=True))
            batch_op.create_foreign_key('fk_entry_category', 'category', ['category_id'], ['id'])

    # Assign category_id based on existing category names or use "Custom"
    entries = session.execute(select(entry_table.c.id, entry_table.c.category)).fetchall()
    for entry_id, category_name in entries:
        category_id = category_map.get(category_name.lower(), custom_category_id)
        update_stmt = entry_table.update().where(entry_table.c.id == entry_id).values(category_id=category_id)
        session.execute(update_stmt)

    session.commit()

    # Change category_id to NOT NULL now that all entries have been updated
    with op.batch_alter_table('entry', schema=None) as batch_op:
        batch_op.alter_column('category_id', nullable=False)

    # Remove redundant category column if it exists
    with op.batch_alter_table('entry', schema=None) as batch_op:
        if column_exists('entry', 'category'):
            batch_op.drop_column('category')

    session.commit()

def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    # Re-add the category column with a temporary default value
    with op.batch_alter_table('entry', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category', sa.String(length=100), nullable=False, server_default="temporary"))

    # Fetch the category names mapped by category_id to update the category column
    categories = session.execute(
        select(category_table.c.id, category_table.c.name)
    ).fetchall()
    category_map = {id: name for id, name in categories}

    # Update the category column with actual category names from category_map
    entries = session.execute(select(entry_table.c.id, entry_table.c.category_id)).fetchall()
    for entry_id, category_id in entries:
        category_name = category_map.get(category_id, "").lower()  # Default to empty string if not found
        session.execute(
            entry_table.update().where(entry_table.c.id == entry_id).values(category=category_name)
        )

    session.commit()

    # Remove temporary default and make the column NOT NULL explicitly if needed
    with op.batch_alter_table('entry', schema=None) as batch_op:
        batch_op.alter_column('category', nullable=False, server_default=None)

    # Use batch mode to remove the column with foreign key in SQLite
    with op.batch_alter_table('entry', schema=None) as batch_op:
        if column_exists('entry', 'category_id'):
            batch_op.drop_constraint('fk_entry_category', type_='foreignkey')
            batch_op.drop_column('category_id')

    # Drop the category table if it was created during the upgrade
    if bind.dialect.has_table(bind, 'category'):
        op.drop_table('category')

    session.commit()

