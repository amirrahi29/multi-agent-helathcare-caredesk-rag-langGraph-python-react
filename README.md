# Multi-Agent AI System (Python + React + LangChain + RAG)

## Youtube video
- youtube.com/watch?v=1DmdnY2Hvok&t=489s&pp=0gcJCd4KAYcqIYzv&pbjreload=102

<table>
  <tr>
    <td width="40%">
      <img src="https://github.com/user-attachments/assets/0f8fac92-5639-4da4-891a-735540ad9111" width="100%" alt="Screenshot 1" />
    </td>
    <td width="40%">
      <img src="https://github.com/user-attachments/assets/71302dc4-854b-4f23-ac19-c1817c663d14" width="100%" alt="Screenshot 2" />
    </td>
  </tr>
</table>

<table>
  <tr>
    <td width="40%">
      <img src="https://github.com/user-attachments/assets/2b5184db-6f47-4f58-a199-0cbe84c9391a" width="100%" alt="Screenshot 3" />
    </td>
    <td width="40%">
      <img src="https://github.com/user-attachments/assets/0de5b141-a62e-497a-9734-144081d97718" width="100%" alt="Screenshot 4" />
    </td>
  </tr>
</table>

End-to-end **multi-agent** demo: **FastAPI** + **LangGraph**-style workflow (`app/graph/pipeline.py`), **PostgreSQL + pgvector**, and a **React** chat client (**CareDesk**). Answers combine **RAG** (semantic retrieval) and **tool** paths (structured lookups); each turn returns a **pipeline trace** the UI can animate.

## Contents

- [Architecture overview](#architecture-overview)
- [Agents](#agents)
- [Tech stack](#tech-stack)
- [Repository layout](#repository-layout)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Demo data & sign-in](#demo-data--sign-in)
- [API](#api)
- [Frontend (CareDesk)](#frontend-caredesk)
- [Features](#features)
- [Limitations](#limitations)
- [Future improvements](#future-improvements)
- [Author](#author)

---

## Architecture overview

High-level flow (see `app/graph/pipeline.py` for the exact graph: prepare → classify → **tool | RAG** → respond):

```
User Query
   ↓
Prepare / follow-up merge
   ↓
Query Agent (intent + structured vs RAG)
   ↓
Decision Agent (route)
   ↓
 ├── Tool Agent (structured DB queries)
 └── RAG Agent (semantic search via pgvector)
   ↓
Response Agent (final answer)
```

---

## Agents

| Agent | Role |
|--------|------|
| **Query** | Intent detection and query type (structured vs RAG). |
| **Decision** | Chooses execution path from classification. |
| **Tool** | Structured queries over demo data (orders, payments, etc.). |
| **RAG** | Embedding search and context from pgvector. |
| **Response** | Final user-facing answer. |

---

## Tech stack

| Layer | Details |
|--------|---------|
| **Backend** | Python 3.11+, FastAPI, Uvicorn, LangGraph (`langgraph`), OpenAI (chat + embeddings) |
| **Data store** | PostgreSQL with **pgvector** |
| **Frontend** | React 19 (Create React App), UI modules under `frontend/src/chat/` |
| **Demo assets** | CSVs in `data/`; optional regeneration via `scripts/generate_demo_csvs.py` |

---

## Repository layout

```
app/
├── agents/       # Query, decision, RAG, tool, response
├── core/         # Embeddings & LLM config
├── services/     # DB, patients, vector helpers
├── graph/        # LangGraph pipeline + trace shaping
└── api/          # FastAPI (`/verify-patient`, `/query`)

frontend/         # CareDesk (`npm start` → http://localhost:3000)
scripts/          # ingest_data, generate_demo_csvs, etc.
data/             # patients, orders, … (CSV)
```

---

## Prerequisites

- **Python** 3.11+ and `pip`
- **Node.js** 18+ and `npm` (for the frontend)
- **PostgreSQL** with **pgvector** extension, database reachable with the credentials in your `.env`
- **OpenAI API key** for LLM and embedding calls used in ingestion and chat

---

## Quick start

### 1. Python virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment variables

Create a `.env` file in the **repository root**:

```env
OPENAI_API_KEY=your_api_key

DB_NAME=your_db
USER_NAME=your_user
PASSWORD=your_password
HOST_NAME=localhost
PORT=5432
```

### 3. Ingest data into Postgres + vectors

From the repo root (after DB is up and extensions are installed):

```bash
python -m scripts.ingest_data
```

**Optional — larger synthetic CSVs** (then run ingest again):

```bash
python scripts/generate_demo_csvs.py
python -m scripts.ingest_data
```

### 4. Run the API

```bash
uvicorn app.api.main:app --reload
```

- API: **http://127.0.0.1:8000**
- Swagger: **http://127.0.0.1:8000/docs**

### 5. Run CareDesk (frontend)

```bash
cd frontend
npm install
npm start
```

Opens **http://localhost:3000** by default.

**Point the UI at another API origin** (optional):

```bash
# frontend/.env.local
REACT_APP_API_URL=http://127.0.0.1:8000
```

The backend allows CORS from `http://localhost:3000` and `http://127.0.0.1:3000`. If the UI shows network errors, confirm the API is running and `REACT_APP_API_URL` has no trailing slash.

---

## Demo data & sign-in

Patient emails come from **`data/patients.csv`** (column `email`). Examples that ship with the default dataset:

- `riya@example.com` (Riya Singh)
- `amit@example.com`
- `arjun@example.com`

Use one of these on the **CareDesk** intro screen. Unknown addresses return **404** from `/verify-patient`.

---

## API

### `POST /verify-patient`

Validates `email` against loaded patient records (used by the intro flow).

**Request**

```json
{ "email": "riya@example.com" }
```

**Response (200)**

```json
{
  "patient_id": 2,
  "name": "Riya Singh",
  "email": "riya@example.com",
  "city": "Mumbai"
}
```

**404** — email not in the dataset.

### `POST /query`

Runs the graph for the signed-in **`patient_email`**. Conversation turns are kept **in memory** per **`session_id`** (per API process, last 40 messages).

**Request**

```json
{
  "query": "Order 5102 ka status kya hai?",
  "patient_email": "riya@example.com",
  "last_query": null,
  "session_id": "uuid-or-string-from-client"
}
```

**Response**

```json
{
  "response": "…",
  "route": "tool",
  "session_id": "uuid-or-string-from-client",
  "pipeline_trace": []
}
```

**403** — `patient_email` not authorized.

---

## Frontend (CareDesk)

- **Sign-in** with a demo email from `data/patients.csv`.
- **Toolbar:** flow legend, signed-in identity, **New chat** (new session id), **Sign out**.
- **Chat:** pipeline steps per assistant turn, then a **final answer** card and route/source pill.
- **Voice input** where the browser supports Web Speech API (see in-app hints).
- **Copy / branding:** `frontend/src/chat/constants.js` (`BRAND_NAME`, API base), `frontend/src/chat/uiCopy.js`.

```bash
cd frontend
npm test          # Jest + Testing Library
npm run build     # production bundle
```

---

## Features

- LangGraph-style branching (tool vs RAG) with **pipeline trace** for the UI  
- Patient-gated **`patient_email`** on `/query`  
- Server-side session history keyed by **`session_id`** (in-process)  
- React client with optional speech-to-text  

## Limitations

- **`SESSION_HISTORY` is lost** when the API process restarts.  
- **Not** a production auth or EMR system — demo CSVs and ingestion only.  
- **Browser storage** holds session id and patient profile locally for convenience.  

---

## Future improvements

- Durable session / chat store (database or Redis)  
- Hardened auth and observability for real deployments  
- Docker Compose for API + Postgres + optional frontend build  

---

## Summary

Ingest **`data/`**, run **`uvicorn app.api.main:app --reload`**, start **`frontend`** with **`npm start`**, sign in with a **`patients.csv`** email, and inspect each answer’s **pipeline** in the chat UI.

---

## Author

Amir Rahi
