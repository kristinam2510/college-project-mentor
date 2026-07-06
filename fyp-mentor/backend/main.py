"""
FastAPI backend for the AI Final-Year-Project Mentor.

This is a STRUCTURED PIPELINE API, not a chat API. The frontend wizard
calls these endpoints in sequence:

  POST /projects                  -> create project, get 5 ideas
  POST /projects/select-idea      -> lock in chosen idea, kicks off
                                      research -> gaps -> datasets ->
                                      architecture -> roadmap (creates tasks)
  GET  /projects/{id}             -> full project state
  GET  /projects/{id}/tasks       -> task list (for progress board)
  PATCH /tasks/{id}                -> update task status
  GET  /projects/{id}/risk        -> recompute risk/success
  GET  /projects/{id}/mentor      -> mentor status card
  POST /projects/{id}/replan      -> detect overdue tasks and redistribute
                                      them across remaining months
"""
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from db import init_db, get_db, to_json, from_json, Project, Task, new_id
from models.schemas import IntakeRequest, SelectIdeaRequest, TaskUpdateRequest

from agents.idea_agent import generate_ideas
from agents.research_agent import run_research
from agents.gap_agent import detect_gaps
from agents.dataset_agent import recommend_datasets
from agents.architecture_agent import generate_architecture
from agents.roadmap_agent import generate_roadmap, regenerate_roadmap
from agents.risk_agent import assess_risk_and_success
from agents.mentor_agent import mentor_check
from agents.replan_agent import replan_if_needed

app = FastAPI(title="AI Final-Year-Project Mentor")
print("DEBUG CORS_ORIGINS:", repr(os.environ.get("CORS_ORIGINS")))
print("DEBUG GROQ_API_KEY present:", bool(os.environ.get("GROQ_API_KEY")))
print("DEBUG GROQ_MODEL:", os.environ.get("GROQ_MODEL"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


def _project_to_dict(p: Project) -> dict:
    return {
        "id": p.id,
        "domain": p.domain,
        "sector": p.sector,
        "difficulty": p.difficulty,
        "duration_months": p.duration_months,
        "team_size": p.team_size,
        "title": p.title,
        "description": p.description,
        "ideas": from_json(p.ideas_json),
        "research": from_json(p.research_json),
        "gaps": from_json(p.gaps_json),
        "datasets": from_json(p.datasets_json),
        "architecture": from_json(p.architecture_json),
        "roadmap": from_json(p.roadmap_json),
        "approved": bool(p.approved),
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@app.post("/projects")
def create_project(req: IntakeRequest, db: Session = Depends(get_db)):
    """Step 1: intake form -> generates candidate ideas."""
    ideas = generate_ideas(req.domain, req.difficulty, req.duration_months, req.team_size, sector=req.sector)

    project = Project(
        id=new_id(),
        domain=req.domain,
        sector=req.sector,
        difficulty=req.difficulty,
        duration_months=req.duration_months,
        team_size=req.team_size,
        ideas_json=to_json(ideas),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return _project_to_dict(project)


@app.post("/projects/select-idea")
def select_idea(req: SelectIdeaRequest, db: Session = Depends(get_db)):
    """
    Step 2: student picks an idea -> runs the rest of the pipeline
    automatically (research -> gaps -> datasets -> architecture -> roadmap
    -> seeds tasks). This is the "agentic, runs on its own" part.
    """
    project = db.get(Project, req.project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    ideas = from_json(project.ideas_json)
    if req.idea_index < 0 or req.idea_index >= len(ideas):
        raise HTTPException(400, "Invalid idea_index")

    chosen = ideas[req.idea_index]
    project.title = chosen["title"]
    project.description = chosen["description"]

    research = run_research(project.id, chosen["title"], chosen["description"])
    project.research_json = to_json(research)

    gaps = detect_gaps(project.id, chosen["title"], chosen["description"], research["papers"])
    project.gaps_json = to_json(gaps)

    datasets = recommend_datasets(chosen["title"], chosen["description"], chosen.get("key_technologies", []))
    project.datasets_json = to_json(datasets)

    architecture = generate_architecture(chosen["title"], chosen["description"], chosen.get("key_technologies", []))
    project.architecture_json = to_json(architecture)

    roadmap = generate_roadmap(chosen["title"], chosen["description"], project.duration_months, project.team_size)
    project.roadmap_json = to_json(roadmap)

    db.commit()

    # Selecting an idea fully replaces the plan, so wipe any tasks left
    # over from a previous idea/roadmap before seeding the new ones --
    # otherwise re-selecting (or re-running select-idea on) a project
    # accumulates tasks from every idea ever chosen.
    db.query(Task).filter(Task.project_id == project.id).delete()

    # seed the task board from the generated roadmap
    for month_block in roadmap.get("months", []):
        if "month" not in month_block:
            for key, value in month_block.items():
                if str(key).isdigit():
                    month_block = {"month": int(key), **value}
                    break
        for task_title in month_block.get("tasks", []):
            db.add(Task(id=new_id(), project_id=project.id, month=month_block["month"], title=task_title))
    db.commit()

    db.refresh(project)
    return _project_to_dict(project)


@app.get("/projects/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return _project_to_dict(project)


@app.get("/projects/{project_id}/tasks")
def get_tasks(project_id: str, db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.project_id == project_id).order_by(Task.month).all()
    return [
        {
            "id": t.id, "month": t.month, "title": t.title, "status": t.status,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        }
        for t in tasks
    ]


@app.patch("/tasks/{task_id}")
def update_task(task_id: str, req: TaskUpdateRequest, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    task.status = req.status
    if req.status == "done":
        task.completed_at = datetime.datetime.utcnow()
    db.commit()
    return {"id": task.id, "status": task.status}


@app.get("/projects/{project_id}/risk")
def get_risk(project_id: str, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    task_dicts = [{"status": t.status, "month": t.month} for t in tasks]
    project_dict = {
        "duration_months": project.duration_months,
        "team_size": project.team_size,
        "difficulty": project.difficulty,
        "created_at": project.created_at,
    }
    return assess_risk_and_success(project_dict, task_dicts)


@app.get("/projects/{project_id}/mentor")
def get_mentor_update(project_id: str, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    task_dicts = [{"status": t.status, "month": t.month, "title": t.title} for t in tasks]

    project_dict = {
        "duration_months": project.duration_months,
        "team_size": project.team_size,
        "difficulty": project.difficulty,
        "created_at": project.created_at,
    }
    risk = assess_risk_and_success(project_dict, task_dicts)
    roadmap = from_json(project.roadmap_json) or {}
    return mentor_check(project.title, roadmap, task_dicts, risk, project=project_dict)


@app.post("/projects/{project_id}/replan")
def replan_project(project_id: str, db: Session = Depends(get_db)):
    """
    Checks for overdue tasks (still pending/in_progress in a month that's
    already passed) and, if any exist, redistributes them across the
    remaining months -- extending duration_months if needed so the new
    plan stays realistic. Then recomputes risk against the updated plan.
    """
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    task_dicts = [{"id": t.id, "month": t.month, "status": t.status} for t in tasks]

    project_dict = {
        "duration_months": project.duration_months,
        "created_at": project.created_at,
    }

    result = replan_if_needed(project_dict, task_dicts)

    if result["changed"]:
        # apply month moves back onto the real Task rows
        task_by_id = {t.id: t for t in tasks}
        for move in result["moves"]:
            task_by_id[move["task_id"]].month = move["new_month"]

        # extend duration if the plan needed more room
        project.duration_months = result["new_duration_months"]

        db.commit()

    # recompute risk against the (possibly updated) plan
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    task_dicts = [{"status": t.status, "month": t.month} for t in tasks]
    risk_project_dict = {
        "duration_months": project.duration_months,
        "team_size": project.team_size,
        "difficulty": project.difficulty,
        "created_at": project.created_at,
    }
    risk = assess_risk_and_success(risk_project_dict, task_dicts)

    return {
        "replanned": result["changed"],
        "current_month": result["current_month"],
        "duration_months": project.duration_months,
        "moves": result["moves"],
        "risk": risk,
    }

@app.post("/projects/{project_id}/roadmap/regenerate")
def regenerate_project_roadmap(project_id: str, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    task_dicts = [{"status": t.status, "month": t.month, "title": t.title} for t in tasks]

    project_dict = {
        "duration_months": project.duration_months,
        "team_size": project.team_size,
        "difficulty": project.difficulty,
        "created_at": project.created_at,
    }
    risk = assess_risk_and_success(project_dict, task_dicts)

    created_at = project.created_at
    if isinstance(created_at, str):
        created_at = datetime.datetime.fromisoformat(created_at)
    elapsed_months = max((datetime.datetime.utcnow() - created_at).days / 30.0, 0.01)
    current_month = min(max(int(elapsed_months) + 1, 1), project.duration_months)

    new_plan = regenerate_roadmap(
        project.title,
        project.description,
        project.duration_months,
        project.team_size,
        current_month,
        task_dicts,
        risk,
    )

    old_roadmap = from_json(project.roadmap_json) or {"months": []}
    kept_months = []
    for month_block in old_roadmap.get("months", []):
        if not isinstance(month_block, dict):
            continue
        if "month" in month_block:
            if month_block["month"] < current_month:
                kept_months.append(month_block)
            continue
        for key, value in month_block.items():
            if str(key).isdigit():
                normalized = {"month": int(key), **value}
                if normalized["month"] < current_month:
                    kept_months.append(normalized)
                break
    merged_months = kept_months + new_plan.get("months", [])
    merged = {"months": merged_months}
    project.roadmap_json = to_json(merged)

    db.query(Task).filter(
        Task.project_id == project_id,
        Task.month >= current_month,
        Task.status != "done",
    ).delete()
    for month_plan in new_plan.get("months", []):
        if "month" not in month_plan:
            for key, value in month_plan.items():
                if str(key).isdigit():
                    month_plan = {"month": int(key), **value}
                    break
        for t in month_plan.get("tasks", []):
            db.add(Task(
                id=new_id(),
                project_id=project_id,
                month=month_plan["month"],
                title=t,
                status="pending",
            ))
    db.commit()

    return {"roadmap": merged, "risk": risk, "replanned_from_month": current_month}
@app.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    """Return all projects for the My Projects home screen."""
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "approved": bool(p.approved),
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in projects
    ]


@app.delete("/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project and all its tasks."""
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    db.query(Task).filter(Task.project_id == project_id).delete()
    db.delete(project)
    db.commit()
    return {"deleted": True}


@app.post("/projects/{project_id}/approve")
def approve_project(project_id: str, db: Session = Depends(get_db)):
    """
    Student has reviewed Research, Gaps, Datasets, Architecture and Roadmap
    and is happy — mark the project as approved so the Progress tab unlocks.
    """
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    project.approved = True
    db.commit()
    return {"approved": True}


@app.get("/health")
def health():
    return {"status": "ok"}