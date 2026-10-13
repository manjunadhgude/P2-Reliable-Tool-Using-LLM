"""Persist per-turn model and tool budget consumption."""
from alembic import op
import sqlalchemy as sa

revision = "0002_turn_budgets"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    # The initial revision uses current ORM metadata to create tables. On a fresh
    # database it may therefore already include these columns; older databases
    # created before the budget fields were added still need this revision to add them.
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("turns")}
    if "model_steps" not in columns:
        op.add_column("turns", sa.Column("model_steps", sa.Integer(), server_default="0", nullable=False))
    if "tool_calls" not in columns:
        op.add_column("turns", sa.Column("tool_calls", sa.Integer(), server_default="0", nullable=False))


def downgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("turns")}
    if "tool_calls" in columns:
        op.drop_column("turns", "tool_calls")
    if "model_steps" in columns:
        op.drop_column("turns", "model_steps")
