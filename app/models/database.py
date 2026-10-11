import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./content.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL, connect_args=connect_args
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)
    # Lightweight schema upgrade for SQLite
    with engine.connect() as conn:
        inspector = inspect(engine)
        if "contents" in inspector.get_table_names():
            columns = {col["name"] for col in inspector.get_columns("contents")}
            new_columns = {
                "content": "TEXT",
                "url": "VARCHAR",
                "published_at": "DATETIME",
                "created_at": "DATETIME",
                "content_hash": "VARCHAR",
            }
            for col_name, col_type in new_columns.items():
                if col_name not in columns:
                    try:
                        conn.execute(text(f"ALTER TABLE contents ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                    except Exception:
                        pass