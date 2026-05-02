# Multi-Agent AI System (Python + React + LangChain + RAG)

<table>
  <tr>
    <td width="40%">
      <img src="https://github.com/user-attachments/assets/6b6253fa-af64-41cb-bcdf-f0a59428efcd" width="100%" alt="Screenshot 1" />
    </td>
    <td width="40%">
      <img src="https://github.com/user-attachments/assets/78552cd9-7901-4213-802e-2a9f31f2f146" width="100%" alt="Screenshot 2" />
    </td>
  </tr>
</table>

<table>
  <tr>
    <td width="40%">
      <img src="https://github.com/user-attachments/assets/cfa9bdd1-4272-476f-820f-1b86a0630f6f" width="100%" alt="Screenshot 3" />
    </td>
    <td width="40%">
      <img src="https://github.com/user-attachments/assets/f3f8d341-af74-46db-801b-5011ba64e9d0" width="100%" alt="Screenshot 4" />
    </td>
  </tr>
</table>

A production-style multi-agent stack: **FastAPI** backend with LangChain / LangGraph-style orchestration, **PostgreSQL + pgvector**, and a **React** chat UI (**CareDesk**) for signed-in demo patients.

The backend combines retrieval-augmented generation (RAG), tool-style structured lookup, routing, and a linear **pipeline trace** the UI can render step by step.

---

## Architecture overview

```
User Query
   ↓
Query Agent (intent detection)
   ↓
Decision Agent (routing)
   ↓
 ├── Tool Agent (structured DB queries)
 └── RAG Agent (semantic search via pgvector)
   ↓
Response Agent (LLM output generation)
```

---

## Agents

| Agent | Role |
|--------|------|
| **Query** | Detects intent and classifies structured vs RAG. |
| **Decision** | Routes to tool or RAG. |
| **Tool** | Runs structured queries on demo data (orders, payments, etc.). |
| **RAG** | Semantic search over embedded documents (pgvector). |
| **Response** | Produces the final natural-language answer. |

---

## Tech stack

- **Backend:** Python 3.11, FastAPI, Uvicorn, LangChain-oriented graph in `app/graph`, OpenAI (LLM + embeddings), PostgreSQL + pgvector  
- **Frontend:** React 19 (Create React App), chat UI under `frontend/src/chat/`  
- **Data:** CSV files under `data/`; ingestion via `scripts.ingest_data`

---

## Repository layout

```
app/
├── agents/       # Query, decision, RAG, tool, response
├── core/         # Embeddings & LLM config
├── services/     # DB, patients, vector store
├── graph/        # Multi-agent pipeline
└── api/          # FastAPI app (verify-patient, query)

frontend/         # CareDesk React app (npm start)
scripts/          # e.g. ingest_data, demo CSV helpers
data/             # Demo CSV datasets
```

---

## Quick start

### 1. Python environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment variables

Create a `.env` in the project root (values match your Postgres and OpenAI setup):

```env
OPENAI_API_KEY=your_api_key

DB_NAME=your_db
USER_NAME=your_user
PASSWORD=your_password
HOST_NAME=localhost
PORT=5432
```

### 3. Ingest demo data (vectors / DB)

```bash
python -m scripts.ingest_data
```

### 4. Run the API

```bash
uvicorn app.api.main:app --reload
```

Default: **http://127.0.0.1:8000** — Open **http://127.0.0.1:8000/docs** for Swagger.

### 5. Run the CareDesk frontend

In another terminal:

```bash
cd frontend
npm install
npm start
```

The app expects the API at **http://localhost:8000** unless you set:

```bash
# frontend/.env.local (optional)
REACT_APP_API_URL=http://localhost:8000
```

CORS is configured for `http://localhost:3000` and `http://127.0.0.1:3000`.

---

## API

### `POST /verify-patient`

Checks the email against demo patients (CSV-backed). Used by the intro sign-in screen.

**Request**

```json
{ "email": "patient@example.com" }
```

**Response (200)**

```json
{
  "patient_id": 1,
  "name": "Riya Singh",
  "email": "patient@example.com",
  "city": "…"
}
```

Returns **404** if the email is not in the demo dataset.

### `POST /query`

Runs the multi-agent graph for a **verified** `patient_email`. Maintains a lightweight **in-memory** conversation per `session_id` (per server process, trimmed to the last 40 messages).

**Request**

```json
{
  "query": "Order 5102 ka status kya hai?",
  "patient_email": "patient@example.com",
  "last_query": null,
  "session_id": "optional-uuid-from-client"
}
```

**Response**

```json
{
  "response": "…natural language answer…",
  "route": "tool",
  "session_id": "optional-uuid-from-client",
  "pipeline_trace": [ /* stepped trace for the UI */ ]
}
```

Returns **403** if `patient_email` is not authorized.

---

## Frontend (CareDesk)

- Sign-in with a **demo patient email** from your data, then chat in **English or Hindi** (voice works in supported browsers; see UI copy).  
- Toolbar shows session status, **New chat** (new `session_id`), and **Sign out** (clears stored profile on the device).  
- Assistant turns show **pipeline steps**, then a **final answer** card with source route (e.g. tool vs RAG).  
- Product name and API base URL are centralized in `frontend/src/chat/constants.js`.

```bash
cd frontend
npm test          # unit tests
npm run build     # production build
```

---

## Features

- Multi-agent pipeline with explicit trace for the UI  
- RAG + tool hybrid routing  
- Patient-gated queries (`patient_email`)  
- Session history on the server (per `session_id`, in-memory)  
- React chat client with speech-to-text (where supported)  

---

## Limitations

- **Server memory** resets when the API process restarts (`SESSION_HISTORY` is in-process).  
- **Browser chat** is local to the device (not a full account system).  
- Demo scope: CSV / ingestion–defined patients and records, not a production EMR.  

---

## Future improvements

- Persistent conversation store (Redis / DB)  
- Stronger observability and auth for real deployments  
- Containerized deploy (Docker) and managed vector DB  

---

## Summary

This repo is an end-to-end **multi-agent + RAG demo**: ingest data, run **FastAPI**, open **CareDesk** on port 3000, sign in with a demo email, and watch the pipeline explain how each answer was produced.

---

## Author

Amir Rahi
