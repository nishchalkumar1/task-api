from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, ConfigDict, model_validator

app = FastAPI(
    title="Task API",
    description="A beginner-friendly SQLite-backed CRUD API for managing tasks.",
    version="1.0",
)

DATABASE_PATH = Path(__file__).with_name("tasks.db")


def get_database_connection() -> sqlite3.Connection:
    """Create a SQLite connection configured for row-based access."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    """Create the database table and seed rows the first time the app starts."""
    with get_database_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL
            )
            """
        )
        connection.commit()

        cursor = connection.execute("SELECT COUNT(*) FROM tasks")
        row_count = cursor.fetchone()[0]
        if row_count == 0:
            connection.executemany(
                "INSERT INTO tasks(title, done) VALUES(?, ?)",
                [
                    ("Learn FastAPI", 0),
                    ("Build CRUD API", 0),
                    ("Submit Internship Assignment", 0),
                ],
            )
            connection.commit()


def row_to_task(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a SQLite row into the API's task response format."""
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
    }


def get_task_row(task_id: int) -> dict[str, Any] | None:
    """Fetch a single task row by id."""
    with get_database_connection() as connection:
        cursor = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return row_to_task(row)


@app.on_event("startup")
def on_startup() -> None:
    initialize_database()


class TaskBase(BaseModel):
    title: str = Field(..., description="Task title")

    @model_validator(mode="after")
    def validate_title(self) -> TaskBase:
        if not self.title.strip():
            raise ValueError("title cannot be empty")
        self.title = self.title.strip()
        return self


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, description="Task title")
    done: bool | None = Field(default=None, description="Task completion status")

    @model_validator(mode="after")
    def validate_update(self) -> TaskUpdate:
        if self.title is not None and not self.title.strip():
            raise ValueError("title cannot be empty")
        if self.title is not None:
            self.title = self.title.strip()
        if self.title is None and self.done is None:
            raise ValueError("At least one field must be provided")
        return self


class Task(TaskBase):
    id: int
    done: bool


class ApiHomeResponse(BaseModel):
    name: str
    version: str
    endpoints: list[str]


class HealthResponse(BaseModel):
    status: str


class ErrorResponse(BaseModel):
    error: str


@app.get(
    "/",
    response_model=ApiHomeResponse,
    summary="API home",
    description="Return basic API information and the available task endpoint.",
)
def read_root() -> ApiHomeResponse:
    return ApiHomeResponse(name="Task API", version="1.0", endpoints=["/tasks"])


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Return a simple status payload to confirm the service is running.",
)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get(
    "/favicon.ico",
    include_in_schema=False,
    summary="Favicon",
    description="Return an empty response for the browser favicon request.",
)
def favicon() -> Response:
    return Response(status_code=204)


@app.get(
    "/tasks",
    response_model=list[Task],
    summary="List tasks",
    description="Return all tasks currently stored in memory.",
)
def get_tasks() -> list[dict[str, Any]]:
    with get_database_connection() as connection:
        cursor = connection.execute("SELECT * FROM tasks")
        rows = cursor.fetchall()
    return [row_to_task(row) for row in rows]


@app.get(
    "/tasks/{task_id}",
    response_model=Task,
    responses={404: {"model": ErrorResponse}},
    summary="Get one task",
    description="Return a single task by its id. Return 404 when the task does not exist.",
)
def get_task(task_id: int) -> dict[str, Any] | JSONResponse:
    task = get_task_row(task_id)
    if task is None:
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
    return task


@app.post(
    "/tasks",
    response_model=Task,
    status_code=201,
    responses={400: {"model": ErrorResponse}},
    summary="Create task",
    description="Create a new task with an auto-generated id and done set to false.",
)
def create_task(task_in: TaskCreate) -> dict[str, Any]:
    with get_database_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO tasks(title, done) VALUES(?, ?)",
            (task_in.title, 0),
        )
        connection.commit()

        task_id = cursor.lastrowid
        row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return row_to_task(row)


@app.put(
    "/tasks/{task_id}",
    response_model=Task,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
    summary="Update task",
    description="Update the title and/or done status for an existing task.",
)
def update_task(task_id: int, task_in: TaskUpdate) -> dict[str, Any] | JSONResponse:
    task = get_task_row(task_id)
    if task is None:
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

    updated_title = task_in.title if task_in.title is not None else task["title"]
    updated_done = task_in.done if task_in.done is not None else task["done"]

    with get_database_connection() as connection:
        connection.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (updated_title, int(updated_done), task_id),
        )
        connection.commit()

    task["title"] = updated_title
    task["done"] = updated_done

    return task


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    responses={404: {"model": ErrorResponse}},
    summary="Delete task",
    description="Delete a task by id. Return 204 with an empty body when successful.",
)
def delete_task(task_id: int) -> JSONResponse:
    with get_database_connection() as connection:
        cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        connection.commit()

    if cursor.rowcount == 0:
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

    return Response(status_code=204)


@app.exception_handler(ValueError)
def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(RequestValidationError)
def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    error_detail = exc.errors()[0]["msg"] if exc.errors() else "Invalid request body"
    return JSONResponse(status_code=400, content={"error": error_detail})


@app.exception_handler(Exception)
def unexpected_error_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
