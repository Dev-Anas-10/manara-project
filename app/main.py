import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from db import Task, get_db, init_db
from s3_logger import setup_logging

s3_handler = setup_logging()
log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    log.info("Application started, DB initialized")
    yield
    log.info("Application shutting down")
    if s3_handler:
        s3_handler.close()


app = FastAPI(title="Tasks API", lifespan=lifespan)


class TaskIn(BaseModel):
    title: str


@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    if request.url.path != "/health":
        log.info("%s %s -> %s", request.method, request.url.path, response.status_code)
    return response


@app.get("/")
def root():
    return {"message": "Hello from ECS Fargate + RDS + S3", "version": "2.0.0"}


@app.get("/health")
def health():
    # Liveness only: does NOT touch the DB, so a DB blip won't kill the task
    return {"status": "healthy"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "db ok"}


@app.get("/tasks")
def list_tasks(db: Session = Depends(get_db)):
    return [{"id": t.id, "title": t.title, "done": t.done} for t in db.query(Task).order_by(Task.id).all()]


@app.post("/tasks", status_code=201)
def create_task(payload: TaskIn, db: Session = Depends(get_db)):
    task = Task(title=payload.title)
    db.add(task)
    db.commit()
    db.refresh(task)
    log.info("Task created id=%s", task.id)
    return {"id": task.id, "title": task.title, "done": task.done}


@app.put("/tasks/{task_id}/done")
def complete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        log.warning("Task not found id=%s", task_id)
        raise HTTPException(status_code=404, detail="Task not found")
    task.done = True
    db.commit()
    return {"id": task.id, "title": task.title, "done": task.done}
