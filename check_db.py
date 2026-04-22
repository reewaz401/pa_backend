import asyncio
from sqlalchemy import text
from app.database import engine

async def main():
    async with engine.connect() as conn:
        for table in ["users", "exercises", "workouts", "workout_exercises", "sets"]:
            count = (await conn.execute(text(f"SELECT count(*) FROM {table}"))).scalar()
            print(f"{table}: {count}")

        print("\n--- Workouts ---")
        rows = (await conn.execute(text("SELECT id, workout_date, title FROM workouts ORDER BY workout_date DESC"))).fetchall()
        if rows:
            for r in rows:
                print(f"  {r[1]} | {r[2]} | {r[0]}")
        else:
            print("  (empty)")

    await engine.dispose()

asyncio.run(main())
