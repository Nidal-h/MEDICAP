"""Add remarque_note table

Revision ID: 87d04a5983b3
Revises: e0fb7ab079e0
Create Date: 2021-11-13 15:53:56.179579

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '87d04a5983b3'
down_revision = 'e0fb7ab079e0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('remarquenote',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('remarque', sa.String(), nullable=True),
    sa.Column('seen', sa.Boolean(), nullable=True),
    sa.Column('note_id', sa.Integer(), nullable=True),
    sa.Column('creator_id', sa.Integer(), nullable=False),
    sa.Column('date_creation', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['creator_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['note_id'], ['note.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_remarquenote_id'), 'remarquenote', ['id'], unique=False)
    op.create_index(op.f('ix_remarquenote_remarque'), 'remarquenote', ['remarque'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_remarquenote_remarque'), table_name='remarquenote')
    op.drop_index(op.f('ix_remarquenote_id'), table_name='remarquenote')
    op.drop_table('remarquenote')
    # ### end Alembic commands ###
