"""Add column profile_bs64 to User model

Revision ID: 7aebbb6abc9b
Revises: 597d9bdbba1e
Create Date: 2021-12-11 13:34:08.651817

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7aebbb6abc9b'
down_revision = '597d9bdbba1e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('profile_bs64', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'profile_bs64')
    # ### end Alembic commands ###
