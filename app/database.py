from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./liveshow.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def run_migrations() -> None:
    """Apply any schema migrations needed for existing databases.

    SQLAlchemy's ``create_all`` only creates missing tables; it does not add
    columns to tables that already exist.  This function handles such
    incremental column additions so that users upgrading from an older version
    do not hit runtime errors.
    """
    with engine.connect() as conn:
        # Only migrate if the scripts table already exists
        tables = {
            row[0]
            for row in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
        }
        if "scripts" not in tables:
            return

        # Retrieve existing columns for the scripts table
        existing = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(scripts)")).fetchall()
        }
        if "font_face" not in existing:
            conn.execute(text("ALTER TABLE scripts ADD COLUMN font_face VARCHAR(256)"))
        if "font_size" not in existing:
            conn.execute(text("ALTER TABLE scripts ADD COLUMN font_size VARCHAR(64)"))
        conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
