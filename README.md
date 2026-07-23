# Task API

## Project Title

Task API

## Short Project Description

Task API is a beginner-friendly FastAPI CRUD application for managing simple tasks in memory. It uses Pydantic for validation and FastAPI for automatic API documentation.

## Features

- In-memory task storage
- Create, read, update, and delete tasks
- Input validation with Pydantic
- JSON error responses
- Automatic Swagger UI documentation

## Tech Stack

- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic

## Project Structure

```text
.
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation Steps

### Virtual Environment Setup

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### Dependency Installation

Install the project dependencies:

```bash
pip install -r requirements.txt
```

## Run Command

```bash
uvicorn app:app --reload
```

## Swagger Documentation URL

Open the interactive API docs here:

```text
http://127.0.0.1:8000/docs
```

## Endpoint Table

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | / | Return API information |
| GET | /health | Return service health status |
| GET | /tasks | Return all tasks |
| GET | /tasks/{id} | Return one task by id |
| POST | /tasks | Create a new task |
| PUT | /tasks/{id} | Update an existing task |
| DELETE | /tasks/{id} | Delete a task |

## Example `curl -i` Output

Example request:

```bash
curl -i http://127.0.0.1:8000/health
```

Example response:

```text
HTTP/1.1 200 OK
content-type: application/json

{"status":"ok"}
```

## In-Memory Data Storage

This application stores all tasks only in memory using a Python list. That means all data is temporary. If the server restarts, the task list returns to the initial sample data.

## License

This project is released under the MIT License.
