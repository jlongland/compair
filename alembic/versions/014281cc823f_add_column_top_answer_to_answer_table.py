"""Add column notable to answer table

Revision ID: 014281cc823f
Revises: ad3d3931f78b
Create Date: 2016-10-05 21:13:52.232095

"""

# revision identifiers, used by Alembic.
revision = '014281cc823f'
down_revision = 'ad3d3931f78b'

from alembic import op
import sqlalchemy as sa

from compair.models import convention

def upgrade():
    op.add_column('answer', sa.Column('top_answer', sa.Boolean(name='top_answer'),
        default='0', server_default='0', nullable=False, index=True))

def downgrade():
    with op.batch_alter_table('answer', naming_convention=convention) as batch_op:
        batch_op.drop_index('ix_answer_top_answer')
        batch_op.drop_column('top_answer')
