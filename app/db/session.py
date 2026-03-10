from sqlmodel import SQLModel, Session, create_engine
from dotenv import load_dotenv

import os

load_dotenv()

mysql_url = os.getenv("MYSQL_URL", "sqlite:///auth_db.db")

engine = create_engine(mysql_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session