"""create workers and project_workers (assignments)

Revision ID: 8ea6286d1acc
Revises: f7fa9f9b5f96
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "8ea6286d1acc"
down_revision: str = "f7fa9f9b5f96"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("dni", sa.String(20), nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("position", sa.String(100), nullable=True),
        sa.Column("specialty", sa.String(100), nullable=True),
        sa.Column("hire_date", sa.Date(), nullable=True),
        sa.Column("hourly_rate", sa.Float(), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_workers")),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name=op.f("fk_workers_tenant_id_tenants"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_workers_user_id_users"),
            ondelete="SET NULL",
        ),
    )
    op.create_index(op.f("ix_workers_tenant_id"), "workers", ["tenant_id"])

    op.create_table(
        "project_workers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("worker_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(100), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("hourly_rate", sa.Float(), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_workers")),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name=op.f("fk_project_workers_tenant_id_tenants"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_project_workers_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["worker_id"],
            ["workers.id"],
            name=op.f("fk_project_workers_worker_id_workers"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "project_id",
            "worker_id",
            name=op.f("uq_project_workers_tenant_project_worker"),
        ),
    )
    op.create_index(
        op.f("ix_project_workers_tenant_id"), "project_workers", ["tenant_id"]
    )
    op.create_index(
        op.f("ix_project_workers_project_id"), "project_workers", ["project_id"]
    )
    op.create_index(
        op.f("ix_project_workers_worker_id"), "project_workers", ["worker_id"]
    )


def downgrade() -> None:
    op.drop_table("project_workers")
    op.drop_table("workers")
