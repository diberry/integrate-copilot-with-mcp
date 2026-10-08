"""
High School Management System API

A FastAPI application that allows teachers to manage student registrations
for extracurricular activities at Mergington High School.
"""

import logging
import secrets
import time
import json
from pathlib import Path

from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from teacher_auth import hash_password, load_teacher_credentials, verify_password

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=current_dir / "static"), name="static")

teacher_credentials_path = current_dir / "teachers.json"
if teacher_credentials_path.exists():
    teacher_credentials = load_teacher_credentials(teacher_credentials_path)
else:
    logging.getLogger(__name__).warning(
        "No teacher credentials configured. Run create_teacher.py before teacher login."
    )
    teacher_credentials = {}

DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe())
teacher_sessions: dict[str, tuple[str, float]] = {}
SESSION_COOKIE = "teacher_session"
SESSION_TTL_SECONDS = 8 * 60 * 60


class TeacherLogin(BaseModel):
    username: str
    password: str


def require_teacher(
    teacher_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> str:
    if teacher_session is None:
        raise HTTPException(status_code=401, detail="Teacher login required")

    session = teacher_sessions.get(teacher_session)
    if session is None:
        raise HTTPException(status_code=401, detail="Teacher login required")

    username, expires_at = session
    if expires_at <= time.time():
        teacher_sessions.pop(teacher_session, None)
        raise HTTPException(status_code=401, detail="Teacher session expired")

    return username

# In-memory activity database
# Method to load data from json file in data directory 
def load_activities():
    try:
        activities_path = current_dir / "data" / "activities.json"

        with open(activities_path, "r") as file:
            data = json.load(file)
            return data
    except:
        print("Activities file not found!")

activities = load_activities()

@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.get("/auth/session")
def get_auth_session(
    teacher_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    if teacher_session is None:
        return {"authenticated": False}

    session = teacher_sessions.get(teacher_session)
    if session is None:
        return {"authenticated": False}

    username, expires_at = session
    if expires_at <= time.time():
        teacher_sessions.pop(teacher_session, None)
        return {"authenticated": False}

    return {"authenticated": True, "username": username}


@app.post("/auth/login")
def login(credentials: TeacherLogin, request: Request):
    stored_password = teacher_credentials.get(
        credentials.username, DUMMY_PASSWORD_HASH
    )
    if not verify_password(credentials.password, stored_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    now = time.time()
    expired_tokens = [
        token for token, (_, expires_at) in teacher_sessions.items()
        if expires_at <= now
    ]
    for token in expired_tokens:
        teacher_sessions.pop(token, None)

    session_token = secrets.token_urlsafe(32)
    teacher_sessions[session_token] = (
        credentials.username,
        now + SESSION_TTL_SECONDS,
    )
    response = JSONResponse(
        {"message": "Login successful", "username": credentials.username}
    )
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="strict",
        secure=request.url.scheme == "https",
    )
    return response


@app.post("/auth/logout")
def logout(
    response: Response,
    teacher_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    if teacher_session is not None:
        teacher_sessions.pop(teacher_session, None)
    response.delete_cookie(SESSION_COOKIE)
    return {"message": "Logout successful"}


@app.post(
    "/activities/{activity_name}/signup",
    dependencies=[Depends(require_teacher)],
)
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete(
    "/activities/{activity_name}/unregister",
    dependencies=[Depends(require_teacher)],
)
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
