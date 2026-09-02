"""Final TracePass hardening: remove e-commerce schema and normalize DPP compliance categories/evidence reviews."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "z9f0e1d2c3b4"
down_revision = ("aa11bb22cc33", "df9fa46b27bc")
branch_labels = None
depends_on = None


def _has_table(bind, name):
    return inspect(bind).has_table(name)


def _has_column(bind, table, column):
    return column in {c["name"] for c in inspect(bind).get_columns(table)}


def upgrade():
    bind = op.get_bind()

    # Remove obsolete online-store/cart tables if they exist from an earlier release.
    for table in ("order_items", "orders", "cart_items", "carts"):
        if _has_table(bind, table):
            op.drop_table(table)

    # Remove the storefront-only product price field. Keep image_url because a
    # product image is useful on the public Digital Product Passport.
    if _has_column(bind, "products", "price"):
        with op.batch_alter_table("products") as batch_op:
            batch_op.drop_column("price")

    # Compliance rules now reference the authoritative ProductCategory FK.
    if not _has_column(bind, "compliance_rules", "category_id"):
        with op.batch_alter_table("compliance_rules") as batch_op:
            batch_op.add_column(sa.Column("category_id", sa.Integer(), nullable=True))
            batch_op.create_index("ix_compliance_rules_category_id", ["category_id"], unique=False)
            batch_op.create_foreign_key("fk_compliance_rules_category_id", "product_categories", ["category_id"], ["id"])

    # Backfill legacy products so existing records participate in the new
    # category-driven compliance engine. New products should use category_id
    # directly; this migration preserves older products during the transition.
    if _has_column(bind, "products", "category") and _has_column(bind, "products", "category_id"):
        op.execute(text("""
            UPDATE products
               SET category_id = (
                   SELECT pc.id FROM product_categories pc
                    WHERE lower(pc.name) = lower(products.category)
                    LIMIT 1
               )
             WHERE category IS NOT NULL AND category_id IS NULL
        """))

    if _has_column(bind, "compliance_rules", "category"):
        # Preserve legacy rules by matching their old category name to the new master data.
        op.execute(text("""
            UPDATE compliance_rules
               SET category_id = (
                   SELECT pc.id FROM product_categories pc
                    WHERE lower(pc.name) = lower(compliance_rules.category)
                    LIMIT 1
               )
             WHERE category IS NOT NULL AND category_id IS NULL
        """))
        with op.batch_alter_table("compliance_rules") as batch_op:
            batch_op.drop_column("category")

    # Certificate evidence ownership/review metadata.
    additions = []
    if not _has_column(bind, "certificates", "uploaded_by_user_id"):
        additions.append(sa.Column("uploaded_by_user_id", sa.Integer(), nullable=True))
    if not _has_column(bind, "certificates", "review_status"):
        additions.append(sa.Column("review_status", sa.String(length=20), nullable=False, server_default="pending"))
    if not _has_column(bind, "certificates", "reviewed_by_user_id"):
        additions.append(sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True))
    if not _has_column(bind, "certificates", "reviewed_at"):
        additions.append(sa.Column("reviewed_at", sa.DateTime(), nullable=True))
    if not _has_column(bind, "certificates", "review_comments"):
        additions.append(sa.Column("review_comments", sa.Text(), nullable=True))
    if additions:
        with op.batch_alter_table("certificates") as batch_op:
            for col in additions:
                batch_op.add_column(col)
            if any(c.name == "uploaded_by_user_id" for c in additions):
                batch_op.create_foreign_key("fk_certificates_uploaded_by_user_id", "users", ["uploaded_by_user_id"], ["id"])
            if any(c.name == "reviewed_by_user_id" for c in additions):
                batch_op.create_foreign_key("fk_certificates_reviewed_by_user_id", "users", ["reviewed_by_user_id"], ["id"])

    # Existing certificate records from older releases are treated as pending so
    # they cannot silently satisfy a compliance rule without human review.
    if _has_column(bind, "certificates", "review_status"):
        op.execute(text("UPDATE certificates SET review_status = 'pending' WHERE review_status IS NULL OR review_status = ''"))


def downgrade():
    # Deliberately do not recreate the removed e-commerce tables. This release
    # permanently excludes the online store/cart scope.
    bind = op.get_bind()
    if _has_column(bind, "certificates", "review_comments"):
        with op.batch_alter_table("certificates") as batch_op:
            for name in ("review_comments", "reviewed_at", "reviewed_by_user_id", "review_status", "uploaded_by_user_id"):
                if _has_column(bind, "certificates", name):
                    batch_op.drop_column(name)
    if _has_column(bind, "compliance_rules", "category_id"):
        with op.batch_alter_table("compliance_rules") as batch_op:
            batch_op.drop_constraint("fk_compliance_rules_category_id", type_="foreignkey")
            batch_op.drop_index("ix_compliance_rules_category_id")
            batch_op.drop_column("category_id")
