"""
SQLite via SQLAlchemy. SQLite is used so the project runs with zero setup
(`docker-compose up` or even just `uvicorn main:app`). To use Postgres for
a more "production" deployment story in your report, just change DATABASE_URL
in .env to a postgres:// URL — the SQLAlchemy models below don't change.
"""
import os
import json
import uuid
import datetime
from sqlalchemy import create_engine, Column, String, Float, Integer, Text, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./fyp_mentor.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def new_id() -> str:
    return str(uuid.uuid4())


class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=new_id)
    domain = Column(String)
    sector = Column(String, nullable=True)
    difficulty = Column(String)
    duration_months = Column(Integer)
    team_size = Column(Integer)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    ideas_json = Column(Text, nullable=True)       # candidate ideas, before selection
    research_json = Column(Text, nullable=True)    # papers + survey
    gaps_json = Column(Text, nullable=True)
    architecture_json = Column(Text, nullable=True)
    roadmap_json = Column(Text, nullable=True)
    datasets_json = Column(Text, nullable=True)
    approved = Column(Boolean, default=False)      # True once student reviews and approves
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True, default=new_id)
    project_id = Column(String, index=True)
    month = Column(Integer)
    title = Column(String)
    status = Column(String, default="pending")  # pending | in_progress | done
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def to_json(obj) -> str:
    return json.dumps(obj)


def from_json(s: str | None):
    return json.loads(s) if s else None