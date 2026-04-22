from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import text

from app.database import engine
from app.routers import activity_logs, auth, exercises, users, workout_logs, workouts
from app.routers.workouts import sets_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(title="PA Backend", lifespan=lifespan)


@app.middleware("http")
async def strip_trailing_slash(request: Request, call_next):
    if request.url.path != "/" and request.url.path.endswith("/"):
        url = request.url.replace(path=request.url.path.rstrip("/"))
        return RedirectResponse(url=str(url), status_code=307)
    return await call_next(request)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(exercises.router)
app.include_router(workouts.router)
app.include_router(sets_router)
app.include_router(workout_logs.router)
app.include_router(activity_logs.router)


@app.get("/health")
async def health():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok"}
