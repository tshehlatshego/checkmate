from sqlmodel import SQLModel, create_engine, Session, select
from contextlib import contextmanager

# Use SQLite (local file factchecker.db)
DATABASE_URL = "sqlite:///factchecker.db"
engine = create_engine(DATABASE_URL, echo=True)

# Initialize the database and create tables
def init_db():
    SQLModel.metadata.create_all(engine)

@contextmanager
def get_db_session():
    """
    Provides a database session context manager.
    Usage:
    with get_db_session() as session:
        result = session.exec(select(MyModel)).all()
    """
    with Session(engine) as session:
        yield session

# Example models (you can expand later)
from sqlmodel import Field

class FactCheck(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    claim: str
    status: str | None = None
    result: str | None = None
    source_url: str | None = None
    analysis: str | None = None
    credibility: str | None = None

# Example CRUD functions
def get_fact_check_by_id(check_id: int):
    with get_db_session() as session:
        return session.get(FactCheck, check_id)

def create_fact_check(claim_text: str):
    with get_db_session() as session:
        fact_check = FactCheck(claim=claim_text, status="pending")
        session.add(fact_check)
        session.commit()
        session.refresh(fact_check)
        return fact_check.id

def update_fact_check(claim_id: int, verdict_label: str, analysis: str, credibility: str, sources: str):
    with get_db_session() as session:
        fact_check = session.get(FactCheck, claim_id)
        if fact_check:
            fact_check.result = verdict_label
            fact_check.analysis = analysis
            fact_check.credibility = credibility
            fact_check.source_url = sources
            fact_check.status = "completed"
            session.add(fact_check)
            session.commit()
