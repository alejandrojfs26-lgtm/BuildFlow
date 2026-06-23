"""create materials and project_materials

Revision ID: f6159f60e980
Revises: 5e0b25a97393
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f6159f60e980"
down_revision: str = "5e0b25a97393"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "materials",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "unit",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'unit'"),
        ),
        sa.Column("unit_price", sa.Float(), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("stock", sa.Float(), nullable=True, server_default=sa.text("0")),
        sa.Column("min_stock", sa.Float(), nullable=True, server_default=sa.text("0")),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_materials")),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name=op.f("fk_materials_tenant_id_tenants"),
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        op.f("ix_materials_tenant_id"), "materials", ["tenant_id"]
    )

    op.create_table(
        "project_materials",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("material_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("total_price", sa.Float(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_materials")),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            name=op.f("fk_project_materials_tenant_id_tenants"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_project_materials_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["material_id"],
            ["materials.id"],
            name=op.f("fk_project_materials_material_id_materials"),
            ondelete="RESTRICT",
        ),
    )
    op.create_index(
        op.f("ix_project_materials_tenant_id"),
        "project_materials",
        ["tenant_id"],
    )
    op.create_index(
        op.f("ix_project_materials_project_id"),
        "project_materials",
        ["project_id"],
    )
    op.create_index(
        op.f("ix_project_materials_material_id"),
        "project_materials",
        ["material_id"],
    )


def downgrade() -> None:
    op.drop_table("project_materials")
    op.drop_table("materials")
