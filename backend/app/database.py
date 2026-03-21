"""Database configuration and session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.models import Base
import logging

logger = logging.getLogger(__name__)

# Create engine
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    connect_args=connect_args
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)

    # Lightweight migration: add 'color' column to pins if it was created before this feature.
    # Only runs on PostgreSQL (information_schema is not available in SQLite).
    if not settings.database_url.startswith("sqlite"):
        from sqlalchemy import text
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            try:
                check_sql = text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='pins' AND column_name='color';"
                )
                result = conn.execute(check_sql).fetchone()
                if not result:
                    conn.execute(text("ALTER TABLE pins ADD COLUMN color VARCHAR(10) NOT NULL DEFAULT 'blue';"))
                    logger.info("Migration: Added 'color' column to 'pins' table.")
            except Exception as e:
                logger.warning(f"Migration warning (color column): {e}")

            # Add 'value' column to votes table (default 1 = like)
            try:
                check_sql = text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='votes' AND column_name='value';"
                )
                result = conn.execute(check_sql).fetchone()
                if not result:
                    conn.execute(text("ALTER TABLE votes ADD COLUMN value INTEGER NOT NULL DEFAULT 1;"))
                    conn.execute(text("ALTER TABLE votes ADD CONSTRAINT check_vote_value CHECK (value IN (1, -1));"))
                    logger.info("Migration: Added 'value' column to 'votes' table.")
            except Exception as e:
                logger.warning(f"Migration warning (vote value column): {e}")

            # Migrate comments table from pin_id to target_type/target_id
            try:
                # Add target_type
                check_sql = text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='comments' AND column_name='target_type';"
                )
                if not conn.execute(check_sql).fetchone():
                    conn.execute(text("ALTER TABLE comments ADD COLUMN target_type VARCHAR(10) NOT NULL DEFAULT 'pin';"))

                # Add target_id
                check_sql2 = text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='comments' AND column_name='target_id';"
                )
                if not conn.execute(check_sql2).fetchone():
                    # Add column allowing NULLs initially to avoid NotNullViolation 
                    conn.execute(text("ALTER TABLE comments ADD COLUMN target_id INTEGER;"))
                    
                    # Migrate existing pin_id data before setting not null
                    check_pin = text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name='comments' AND column_name='pin_id';"
                    )
                    if conn.execute(check_pin).fetchone():
                        # We use 0 as a default fallback for orphaned comments just in case
                        conn.execute(text("UPDATE comments SET target_id = COALESCE(pin_id, 0);"))
                    else:
                        conn.execute(text("UPDATE comments SET target_id = 0 WHERE target_id IS NULL;"))
                        
                    # Now that all rows have a value, enforce NOT NULL
                    conn.execute(text("ALTER TABLE comments ALTER COLUMN target_id SET NOT NULL;"))
                    
                    logger.info("Migration: Added 'target_type'/'target_id' columns to 'comments' table.")

                # Add constraint
                check_constraint = text(
                    "SELECT constraint_name FROM information_schema.table_constraints "
                    "WHERE table_name='comments' AND constraint_name='check_comment_target_type';"
                )
                if not conn.execute(check_constraint).fetchone():
                    conn.execute(text("ALTER TABLE comments ADD CONSTRAINT check_comment_target_type CHECK (target_type IN ('pin', 'area'));"))
            except Exception as e:
                logger.warning(f"Migration warning (comments target columns): {e}")

            # Migrate target_id from INTEGER to BIGINT (pin/area IDs can exceed 32-bit range)
            try:
                check_type = text(
                    "SELECT data_type FROM information_schema.columns "
                    "WHERE table_name='comments' AND column_name='target_id';"
                )
                result = conn.execute(check_type).fetchone()
                if result and result[0] == 'integer':
                    conn.execute(text("ALTER TABLE comments ALTER COLUMN target_id TYPE BIGINT;"))
                    logger.info("Migration: Changed 'target_id' column to BIGINT in 'comments' table.")
            except Exception as e:
                logger.warning(f"Migration warning (comments target_id bigint): {e}")


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
