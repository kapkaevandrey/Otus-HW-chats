"""1_init

Revision ID: 0d8fee3fd7bb
Revises:
Create Date: 2026-02-28 21:19:43.885136

"""

from alembic import op


revision = "0d8fee3fd7bb"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    CREATE TABLE users (
        id UUID PRIMARY KEY,
        first_name VARCHAR(255) NOT NULL,
        second_name VARCHAR(255) NOT NULL,
        birthdate DATE NOT NULL,
        biography TEXT,
        city VARCHAR(255)
    );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS users;")
