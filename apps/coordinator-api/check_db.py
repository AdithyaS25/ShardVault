import asyncio
from app.core.database import engine
from sqlalchemy import text

async def check():
    async with engine.connect() as conn:

        # Only public schema tables
        result = await conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        ))
        tables = result.fetchall()
        print("Tables in PUBLIC schema:")
        if not tables:
            print("  (no tables found — none created yet)")
        for t in tables:
            print(" -", t[0])

        # Check columns only if public.users exists
        if any(t[0] == "users" for t in tables):
            col_result = await conn.execute(text(
                "SELECT column_name, data_type "
                "FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = 'users' "
                "ORDER BY ordinal_position"
            ))
            cols = col_result.fetchall()
            print("\nColumns in public.users:")
            for c in cols:
                print(f"  - {c[0]} ({c[1]})")
        else:
            print("\npublic.users does not exist yet.")

asyncio.run(check())