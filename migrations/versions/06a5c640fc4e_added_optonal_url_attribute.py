"""Added optonal URL attribute

Revision ID: 06a5c640fc4e
Revises: 2f5a4e907518
Create Date: 2024-06-03 15:32:14.972650

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '06a5c640fc4e'
down_revision = '2f5a4e907518'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('entry', schema=None) as batch_op:
        batch_op.add_column(sa.Column('url', sa.String(length=1000), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('entry', schema=None) as batch_op:
        batch_op.drop_column('url')

    # ### end Alembic commands ###
