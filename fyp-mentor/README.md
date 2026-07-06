# AI Final-Year-Project Mentor

A structured, wizard-style tool (not a chatbot) that takes a student from
project idea selection to a tracked, mentored implementation plan.

```
Intake form → 5 generated ideas → pick one → pipeline runs automatically
(research → gap detection → datasets → architecture → roadmap) → dashboard
(progress board, risk/success score, mentor status card)
```

## Why this shape, not a chatbot

The original brief suggested Open WebUI + CrewAI as a conversational agent
stack. In practice, this workflow is a **fixed sequential pipeline**, not an
open-ended conversation: research always happens before gap detection,
which always happens before architecture. A chat interface adds UI
complexity (intent detection, conversation state) without adding capability.
This build instead uses:

- A plain **React wizard UI** (not Open WebUI's chat widget) — four short
  steps, each with a clear "done" state.
- **Direct, focused LLM calls per agent** instead of CrewAI's
  task-delegation framework. CrewAI earns its complexity when agents need
  to *decide* what to do next or call each other dynamically; here the
  call order is fixed, so a Python function per agent is simpler to build,
  test, and explain in a viva than an agent framework wrapping the same
  fixed sequence. See `backend/agents/` — each file *is* one agent's
  responsibility, callable independently or wired into a pipeline.
- **ChromaDB** kept as specified — used to cache retrieved paper abstracts
  per project so the Gap Detection agent doesn't re-hit the research APIs.
- **arXiv + Semantic Scholar APIs** used directly, no key required for arXiv,
  optional key for Semantic Scholar to raise rate limits.

## What's reused vs. custom-built

| Component | Status |
|---|---|
| LLM calls (ideas, research summary, gaps, architecture, roadmap, mentor) | Custom prompts, but reuse the Anthropic SDK — no need to write inference code |
| arXiv / Semantic Scholar clients | Thin custom wrappers (~30 lines each) around public REST APIs |
| ChromaDB | Reused as-is via its Python client; only collection naming is custom |
| Risk/Success prediction | Custom, deliberately rule-based (see `backend/agents/risk_agent.py` docstring for why — no FYP cohort dataset exists to train a real model on, so a transparent heuristic is more honest than a fabricated one) |
| Database layer | SQLAlchemy + SQLite, standard ORM patterns |
| Frontend | Custom React app — no Open WebUI chat widget, since the UI is a wizard, not a conversation |

This keeps custom code concentrated in: agent prompts, the gap-detection
method (frequency analysis + LLM reasoning over it), and the risk heuristic
— the actual novel contributions — while everything else (HTTP plumbing,
vector storage, ORM) is off-the-shelf.

## Project structure

```
fyp-mentor/
├── backend/
│   ├── agents/              # one file per agent (idea, research, gap, dataset,
│   │                         architecture, roadmap, risk, mentor)
│   ├── services/             # llm_client, arxiv_client, semantic_scholar_client, chroma_client
│   ├── models/schemas.py     # pydantic request/response models
│   ├── db.py                 # SQLAlchemy models (Project, Task)
│   ├── main.py                # FastAPI app — pipeline endpoints
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/Intake.jsx     # step 1: domain/difficulty/duration/team form
│   │   ├── pages/Ideas.jsx      # step 2: pick an idea, triggers pipeline
│   │   ├── pages/Dashboard.jsx  # step 3: tabs for research/gaps/datasets/
│   │   │                          architecture/roadmap/progress/mentor
│   │   ├── components/PipelineRail.jsx
│   │   └── lib/api.js
│   └── package.json
└── docker-compose.yml
```

## Running locally

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your ANTHROPIC_API_KEY
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173`.

### Or with Docker
```bash
cp backend/.env.example backend/.env   # add your key first
docker compose up --build
```

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/projects` | Intake form → generates 5 ideas |
| POST | `/projects/select-idea` | Locks idea, runs research → gaps → datasets → architecture → roadmap, seeds tasks |
| GET | `/projects/{id}` | Full project state |
| GET | `/projects/{id}/tasks` | Task board |
| PATCH | `/tasks/{id}` | Update task status |
| GET | `/projects/{id}/risk` | Recomputed risk/success score |
| GET | `/projects/{id}/mentor` | Mentor status card |

## Notes for the project report

- **Novelty section**: lean on `gap_agent.py`'s method — it separates the
  *auditable* part (frequency counting done in plain Python) from the
  *reasoning* part (LLM proposing directions from that table). That
  separation is defensible in a viva ("here's exactly how '80% of papers
  use CNNs' was computed — it's not an LLM guess").
- **Risk/success model**: explicitly a weighted heuristic, not trained ML —
  documented in code with the reasoning. If you want to claim a "trained
  model" for the report, you'd need real usage data across multiple
  students/cohorts first; until then, presenting an honest heuristic is
  stronger than presenting a fake training pipeline.
- **Swap to Postgres** for the database section of your report by changing
  `DATABASE_URL` in `.env` — no code changes needed since SQLAlchemy
  abstracts the dialect.
