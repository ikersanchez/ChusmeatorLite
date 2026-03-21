"""Database configuration and session management."""
from sqlalchemy import create_engine, inspect
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
    """Initialize database tables. Drop and recreate for schema migration."""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # Check if we need to migrate: if 'pins' table exists but doesn't have 'category' column
    needs_migration = False
    if "pins" in existing_tables:
        columns = [col["name"] for col in inspector.get_columns("pins")]
        if "category" not in columns:
            needs_migration = True
    
    if needs_migration:
        logger.info("Schema migration needed: dropping all tables and recreating...")
        from sqlalchemy import text
        try:
            with engine.begin() as conn:
                if engine.name == "postgresql":
                    for table in ["comments", "votes", "pins", "areas", "users"]:
                        conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
        except Exception as e:
            logger.warning(f"Error dropping tables manually: {e}")

        Base.metadata.drop_all(bind=engine)
    
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized.")


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
