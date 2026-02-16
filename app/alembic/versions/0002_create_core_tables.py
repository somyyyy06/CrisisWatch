"""create incidents and subscriptions tables

Revision ID: 0002_create_core_tables
Revises: 0001_create_users_table
Create Date: 2026-02-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry


# revision identifiers, used by Alembic.
revision: str = '0002_create_core_tables'
down_revision: Union[str, Sequence[str], None] = '0001_create_users_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable PostGIS extension for geometry types
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    
    # Create incidents table
    op.create_table('incidents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('incident_type', sa.String(), nullable=True),
        sa.Column('location_text', sa.String(), nullable=True),
        sa.Column('lon', sa.Float(), nullable=True),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('geom', Geometry('POINT', srid=4326), nullable=True),
        sa.Column('severity', sa.String(), nullable=True),
        sa.Column('reported_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['reported_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_incidents_id'), 'incidents', ['id'], unique=False)
    op.create_index('idx_incidents_geom', 'incidents', ['geom'], unique=False, postgresql_using='gist')
    
    # Create subscriptions table
    op.create_table('subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('location_text', sa.String(), nullable=False),
        sa.Column('radius_km', sa.Float(), nullable=False, server_default='10.0'),
        sa.Column('lon', sa.Float(), nullable=True),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('geom', Geometry('POINT', srid=4326), nullable=True),
        sa.Column('incident_types', sa.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subscriptions_id'), 'subscriptions', ['id'], unique=False)
    op.create_index('idx_subscriptions_geom', 'subscriptions', ['geom'], unique=False, postgresql_using='gist')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_subscriptions_geom', table_name='subscriptions')
    op.drop_index(op.f('ix_subscriptions_id'), table_name='subscriptions')
    op.drop_table('subscriptions')
    
    op.drop_index('idx_incidents_geom', table_name='incidents')
    op.drop_index(op.f('ix_incidents_id'), table_name='incidents')
    op.drop_table('incidents')
    
    # Note: Not dropping postgis extension in case other tables use it
