from pathlib import Path
from app.database import engine, is_sqlite

if not is_sqlite():
    raise SystemExit("This script is for SQLite local development. Use database_schema.sql for Supabase/PostgreSQL.")

sql = Path(__file__).resolve().parents[1] / "local_schema.sql"
with engine.begin() as conn:
    for statement in sql.read_text(encoding="utf-8").split(";"):
        statement=statement.strip()
        if statement:
            conn.exec_driver_sql(statement)
print("Local SQLite database initialized: oism_local.db")
