from typing import Generator

from sqlalchemy.orm import sessionmaker

from ktem.app import BaseApp
from ktem.db.engine import engine
from ktem.index import IndexManager
from ktem.llms.manager import llms as llm_manager
from ktem.embeddings.manager import embedding_models_manager as embedding_manager
from ktem.rerankings.manager import reranking_models_manager as reranking_manager

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class App(BaseApp):
    def ui(self):
        pass

def get_application() -> App:
    return App()

def get_index_manager() -> IndexManager:
    return IndexManager(get_application())

def get_llm_manager():
    return llm_manager

def get_embedding_manager():
    return embedding_manager

def get_reranking_manager():
    return reranking_manager

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
