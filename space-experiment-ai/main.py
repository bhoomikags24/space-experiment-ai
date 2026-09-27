from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime
import asyncio
import sqlite3
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

steps = [
    "PICK OBJECT",
    "SHOW OBJECT",
    "PLACE OBJECT",
    "CLOSE CONTAINER",
    "RAISE HAND"
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
DATABASE_PATH = os.path.join(DATABASE_DIR, "experiment.db")

os.makedirs(DATABASE_DIR, exist_ok=True)


def create_database():
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id TEXT,
            participant_id TEXT,
            time TEXT,
            step INTEGER,
            activity TEXT,
            status TEXT,
            confidence REAL
        )
    """)

    connection.commit()
    connection.close()


create_database()


experiment_state = {
    "experiment_id": "EXP001",
    "participant_id": "P001",
    "current_activity": "PICK OBJECT",
    "current_step": 1,
    "total_steps": 5,
    "status": "WAITING",
    "confidence": 0.0,
    "expected_activity": "PICK OBJECT"
}

latest_frame = None


@app.get("/")
def home():
    return {
        "message": "Space Experiment AI Backend is running"
    }


@app.get("/status")
def status():
    return {
        "status": "Backend connected successfully"
    }


@app.get("/experiment")
def experiment():
    return experiment_state


class ExperimentSetup(BaseModel):
    experiment_id: str
    participant_id: str


@app.post("/setup")
def setup_experiment(data: ExperimentSetup):

    experiment_state["experiment_id"] = data.experiment_id
    experiment_state["participant_id"] = data.participant_id
    experiment_state["current_activity"] = "PICK OBJECT"
    experiment_state["current_step"] = 1
    experiment_state["total_steps"] = len(steps)
    experiment_state["status"] = "WAITING"
    experiment_state["confidence"] = 0.0
    experiment_state["expected_activity"] = "PICK OBJECT"

    return {
        "message": "Experiment setup completed",
        "experiment": experiment_state
    }


class ActivityUpdate(BaseModel):
    activity: str
    step: int
    status: str = "WAITING"
    confidence: float = 0.0


@app.post("/update")
def update_activity(data: ActivityUpdate):

    experiment_state["current_activity"] = data.activity
    experiment_state["current_step"] = data.step
    experiment_state["status"] = data.status
    experiment_state["confidence"] = data.confidence

    if data.step <= len(steps):
        experiment_state["expected_activity"] = steps[data.step - 1]
    else:
        experiment_state["expected_activity"] = "COMPLETED"

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM activity_logs
        WHERE experiment_id = ?
        AND participant_id = ?
        AND step = ?
        AND activity = ?
        AND status = ?
        ORDER BY id DESC
        LIMIT 1
    """, (
        experiment_state["experiment_id"],
        experiment_state["participant_id"],
        data.step,
        data.activity,
        data.status
    ))

    existing = cursor.fetchone()

    if existing is None:
        cursor.execute("""
            INSERT INTO activity_logs
            (
                experiment_id,
                participant_id,
                time,
                step,
                activity,
                status,
                confidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            experiment_state["experiment_id"],
            experiment_state["participant_id"],
            datetime.now().strftime("%H:%M:%S"),
            data.step,
            data.activity,
            data.status,
            data.confidence
        ))

        connection.commit()

    connection.close()

    return {
        "message": "Activity updated successfully"
    }


@app.get("/logs")
def get_logs():

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            time,
            step,
            activity,
            status,
            confidence
        FROM activity_logs
        WHERE experiment_id = ?
        AND participant_id = ?
        ORDER BY id ASC
    """, (
        experiment_state["experiment_id"],
        experiment_state["participant_id"]
    ))

    rows = cursor.fetchall()
    connection.close()

    logs = [dict(row) for row in rows]

    return {
        "logs": logs
    }


@app.get("/report")
def get_report():

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            time,
            step,
            activity,
            status,
            confidence
        FROM activity_logs
        WHERE experiment_id = ?
        AND participant_id = ?
        ORDER BY id ASC
    """, (
        experiment_state["experiment_id"],
        experiment_state["participant_id"]
    ))

    rows = cursor.fetchall()
    connection.close()

    logs = [dict(row) for row in rows]

    correct_count = sum(
        1 for log in logs
        if log["status"] == "CORRECT"
    )

    wrong_count = sum(
        1 for log in logs
        if log["status"] == "WRONG"
    )

    if logs:
        average_confidence = sum(
            log["confidence"] for log in logs
        ) / len(logs)
    else:
        average_confidence = 0

    completion_status = (
        "COMPLETED"
        if experiment_state["current_step"] >= len(steps)
        else "IN PROGRESS"
    )

    return {
        "experiment_id": experiment_state["experiment_id"],
        "participant_id": experiment_state["participant_id"],
        "total_steps": len(steps),
        "current_step": experiment_state["current_step"],
        "completion_status": completion_status,
        "total_logs": len(logs),
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "average_confidence": round(average_confidence, 2),
        "logs": logs
    }


@app.post("/frame")
async def receive_frame(request: Request):

    global latest_frame

    latest_frame = await request.body()

    return {
        "message": "Frame received"
    }


async def camera_stream():

    global latest_frame

    while True:

        if latest_frame is not None:

            frame = latest_frame

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + frame
                + b"\r\n"
            )

        await asyncio.sleep(0.03)


@app.get("/camera")
async def camera():

    return StreamingResponse(
        camera_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )