"""Add remarque_note table

Revision ID: e0fb7ab079e0
Revises: 5a45d5b36426
Create Date: 2021-11-13 15:48:37.625904

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e0fb7ab079e0'
down_revision = '5a45d5b36426'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('note_patient_id_fkey', 'note', type_='foreignkey')
    op.drop_column('note', 'patient_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('note', sa.Column('patient_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('note_patient_id_fkey', 'note', 'user', ['patient_id'], ['id'])
    # ### end Alembic commands ###
