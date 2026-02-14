from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base


Base = declarative_base()

# -------------------------
# WORKER MODEL
# -------------------------
# This model represents a worker in the database. It includes fields for
# name, email, skill, experience years, and salary. The email field is unique   
class WorkerDB(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    skill = Column(String, nullable=False)
    experience_years = Column(Integer, nullable=False)
    salary = Column(Integer, nullable=False)


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./workers.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)