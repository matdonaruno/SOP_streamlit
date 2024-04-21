"""Add EditDepartmentalSOP

Revision ID: aae5f0fb41e5
Revises: 
Create Date: 2024-04-10 22:58:36.035279

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aae5f0fb41e5'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('uncertainty_factor_diagrams',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sop_id', sa.Integer(), nullable=False),
    sa.Column('diagram_name', sa.String(), nullable=False),
    sa.Column('diagram_data', sa.LargeBinary(), nullable=False),
    sa.Column('registered_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['sop_id'], ['sop_details.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('uncertainty_factor_diagrams')
    # ### end Alembic commands ###