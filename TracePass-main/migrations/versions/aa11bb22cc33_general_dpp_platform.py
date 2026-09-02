"""General industry/template support for TracePass DPP platform.

Merges the two legacy Phase-6 migration heads and introduces configurable
industries, product templates and category-specific passport attributes.
"""
from alembic import op
import sqlalchemy as sa

revision = "aa11bb22cc33"
down_revision = "c3d7e9f2a114"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "industries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "product_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("industry_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["industry_id"], ["industries.id"]),
    )
    op.create_table(
        "template_fields",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(80), nullable=False),
        sa.Column("label", sa.String(150), nullable=False),
        sa.Column("field_type", sa.String(20), nullable=False, server_default="text"),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("help_text", sa.String(255), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["template_id"], ["product_templates.id"]),
        sa.UniqueConstraint("template_id", "key", name="uq_template_field_key"),
    )
    with op.batch_alter_table("product_categories", schema=None) as batch_op:
        batch_op.add_column(sa.Column("industry_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("template_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_product_categories_industry_id", ["industry_id"], unique=False)
        batch_op.create_index("ix_product_categories_template_id", ["template_id"], unique=False)
        batch_op.create_foreign_key("fk_product_categories_industry", "industries", ["industry_id"], ["id"])
        batch_op.create_foreign_key("fk_product_categories_template", "product_templates", ["template_id"], ["id"])
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.add_column(sa.Column("attribute_values", sa.Text(), nullable=True))

def downgrade():
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.drop_column("attribute_values")
    with op.batch_alter_table("product_categories", schema=None) as batch_op:
        batch_op.drop_constraint("fk_product_categories_template", type_="foreignkey")
        batch_op.drop_constraint("fk_product_categories_industry", type_="foreignkey")
        batch_op.drop_index("ix_product_categories_template_id")
        batch_op.drop_index("ix_product_categories_industry_id")
        batch_op.drop_column("template_id")
        batch_op.drop_column("industry_id")
    op.drop_table("template_fields")
    op.drop_table("product_templates")
    op.drop_table("industries")
