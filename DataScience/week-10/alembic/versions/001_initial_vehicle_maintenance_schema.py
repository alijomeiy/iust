"""Initial schema: Vehicle, GPSLog, MaintenanceEvent.

Revision ID: 001_initial
Revises:
Create Date: 2025-02-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("owner_id", sa.String(length=255), nullable=False),
        sa.Column("total_distance_km", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_service_distance_km", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_calculated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vehicles_id"), "vehicles", ["id"], unique=False)
    op.create_index(op.f("ix_vehicles_owner_id"), "vehicles", ["owner_id"], unique=False)

    op.create_table(
        "gps_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_gps_logs_id"), "gps_logs", ["id"], unique=False)
    op.create_index(op.f("ix_gps_logs_vehicle_id"), "gps_logs", ["vehicle_id"], unique=False)
    op.create_index(op.f("ix_gps_logs_timestamp"), "gps_logs", ["timestamp"], unique=False)
    op.create_index(
        "ix_gps_logs_vehicle_id_timestamp",
        "gps_logs",
        ["vehicle_id", "timestamp"],
        unique=False,
    )

    op.create_table(
        "maintenance_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_maintenance_events_id"), "maintenance_events", ["id"], unique=False)
    op.create_index(op.f("ix_maintenance_events_vehicle_id"), "maintenance_events", ["vehicle_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_maintenance_events_vehicle_id"), table_name="maintenance_events")
    op.drop_index(op.f("ix_maintenance_events_id"), table_name="maintenance_events")
    op.drop_table("maintenance_events")

    op.drop_index("ix_gps_logs_vehicle_id_timestamp", table_name="gps_logs")
    op.drop_index(op.f("ix_gps_logs_timestamp"), table_name="gps_logs")
    op.drop_index(op.f("ix_gps_logs_vehicle_id"), table_name="gps_logs")
    op.drop_index(op.f("ix_gps_logs_id"), table_name="gps_logs")
    op.drop_table("gps_logs")

    op.drop_index(op.f("ix_vehicles_owner_id"), table_name="vehicles")
    op.drop_index(op.f("ix_vehicles_id"), table_name="vehicles")
    op.drop_table("vehicles")
