from ktem.main import App
from ktem.db.engine import engine
from sqlmodel import Session

# Create a global App instance to be shared across the application
# This is a simplified approach. In a production environment, you might want
# to manage the lifecycle of this instance more carefully.
app_instance = App()
index_manager = app_instance.index_manager

def get_application():
    """Dependency to get the main application instance."""
    return app_instance

def get_index_manager():
    """Dependency to get the index manager."""
    return index_manager

def get_db():
    """Dependency to get a database session."""
    with Session(engine) as session:
        yield session
