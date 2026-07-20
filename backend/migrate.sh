#!/bin/sh
# migrate.sh — Wait for the database, ensure schema, sync Alembic state.
# Runs as the Railway start command prefix. A schema step failing must not
# permanently kill the deployment: the API can still serve /health, so we
# log loudly and continue rather than exit non-zero.

echo "=== Preparing database ==="
python - <<'EOF'
import sys, time
import sqlalchemy as sa

from app.core.config import settings

url = settings.DATABASE_URL_SYNC

# 1. Wait for the database to accept connections (Neon cold start / boot races)
engine = None
for attempt in range(30):
    try:
        engine = sa.create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
        with engine.connect():
            pass
        print(f"Database reachable (attempt {attempt + 1})")
        break
    except Exception as e:
        print(f"Database not ready (attempt {attempt + 1}/30): {e}")
        time.sleep(2)
else:
    print("WARNING: database never became reachable; starting server anyway")
    sys.exit(0)

try:
    # 2. pgvector must exist before models with Vector columns are created
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector;"))
    print("pgvector extension ready")

    # 3. Create any missing tables/indexes from the models (idempotent).
    #    The initial Alembic revision is empty, so create_all is the source
    #    of truth for schema; Alembic is then stamped to head for the future.
    from app.database.session import Base
    import app.models  # noqa: F401
    Base.metadata.create_all(engine, checkfirst=True)
    print("Schema ensured from models")

    # 4. create_all skips existing tables, so add any columns the models
    #    gained since the table was created (idempotent, additive only).
    insp = sa.inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if not insp.has_table(table.name):
                continue
            db_cols = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name in db_cols:
                    continue
                ddl = f'ALTER TABLE {table.name} ADD COLUMN IF NOT EXISTS {col.name} {col.type.compile(engine.dialect)}'
                conn.execute(sa.text(ddl))
                print(f"Added column {table.name}.{col.name}")
except Exception as e:
    print(f"WARNING: schema preparation failed: {e}")
EOF

echo "=== Syncing Alembic version ==="
if alembic stamp head; then
    echo "=== Alembic stamped to head ==="
else
    echo "WARNING: alembic stamp failed — starting the server anyway"
fi
