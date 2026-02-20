import os
from pathlib import Path
from dotenv import load_dotenv

from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# -------------------------
# BASE MODEL
# -------------------------

Base = declarative_base()

# -------------------------
# WORKER MODEL
# -------------------------

class WorkerDB(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)

    # Identity Fields
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    skill = Column(String(100), nullable=False)

    # Profile Fields
    experience_years = Column(Integer, nullable=False)
    salary = Column(Integer, nullable=False)

    # Performance Fields (NEW)
    rating = Column(Float, default=0)
    on_time = Column(Float, default=0)
    completion = Column(Float, default=0)
    complaints = Column(Integer, default=0)
    jobs_completed = Column(Integer, default=0)


# -------------------------
# DATABASE CONFIG
# -------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)