from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.graph.pipeline import run_multi_agent_graph
from app.services.patients import fetch_patient_by_email

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# In-memory conversation store (per process)
# -----------------------------
MAX_HISTORY_MESSAGES = 40

SESSION_HISTORY: dict[str, list[dict]] = {}


def _trim_history(messages: list[dict]) -> list[dict]:
    if len(messages) <= MAX_HISTORY_MESSAGES:
        return messages
    return messages[-MAX_HISTORY_MESSAGES:]


# -----------------------------
# Request Schema
# -----------------------------
class VerifyPatientRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=320)


class QueryRequest(BaseModel):
    query: str
    patient_email: str = Field(..., min_length=3, max_length=320)
    last_query: str | None = None
    session_id: str | None = None


# -----------------------------
# Patient gate
# -----------------------------
@app.post("/verify-patient")
def verify_patient(req: VerifyPatientRequest):
    row = fetch_patient_by_email(str(req.email))
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="This email is not registered for patient access. Use the address on file with your organization.",
        )
    return {
        "patient_id": row["patient_id"],
        "name": row["name"],
        "email": row["email"],
        "city": row["city"],
    }


# -----------------------------
# MAIN API
# -----------------------------
@app.post("/query")
def handle_query(req: QueryRequest):
    patient = fetch_patient_by_email(str(req.patient_email))
    if patient is None:
        raise HTTPException(
            status_code=403,
            detail="The signed-in address is not authorized for patient access. End the session and sign in with a valid account.",
        )

    session_id = (req.session_id or "default").strip() or "default"
    prior = [dict(m) for m in SESSION_HISTORY.get(session_id, [])]

    final_state = run_multi_agent_graph(
        {
            "query": req.query,
            "last_query": req.last_query,
            "history": prior,
            "patient_id": patient["patient_id"],
            "patient_name": patient["name"],
            "patient_email": patient["email"],
        }
    )

    assistant_text = final_state.get("response", "")
    route = final_state.get("route", "rag")
    pipeline_trace = final_state.get("pipeline_trace") or []

    turns = list(SESSION_HISTORY.get(session_id, []))
    turns.append({"role": "user", "content": req.query.strip()})
    turns.append({"role": "assistant", "content": assistant_text})
    SESSION_HISTORY[session_id] = _trim_history(turns)

    return {
        "response": assistant_text,
        "route": route,
        "session_id": session_id,
        "pipeline_trace": pipeline_trace,
    }
