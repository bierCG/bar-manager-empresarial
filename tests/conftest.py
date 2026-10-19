import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv()

URL_TESTE = os.getenv("TEST_DATABASE_URL")

'''
if not URL_TESTE or not URL_TESTE.endswith("_test"):
    raise RuntimeError("TEST_DATABASE_URL ausente ou não termina com '_test'")
'''

os.environ["DATABASE_URL"] = URL_TESTE

from fastapi.testclient import TestClient          
from alembic import command                        
from alembic.config import Config                  
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session                

from app.main import app                           
from app.core.database.connection import get_db         

SEEDS_SQL = Path(__file__).parent / "seed.sql"     


@pytest.fixture(scope="session")
def migracoes_banco():
    engine = create_engine(URL_TESTE)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    engine.dispose()

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", URL_TESTE.replace("%", "%%"))
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(scope="session")
def engine(migracoes_banco):
    engine = create_engine(URL_TESTE)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine):
    conn = engine.connect()
    trans = conn.begin()
    conn.exec_driver_sql(SEEDS_SQL.read_text(encoding="utf-8"))
    session = Session(bind=conn, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        conn.close()


@pytest.fixture
def client(session):
    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)