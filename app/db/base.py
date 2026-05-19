# Import SQLModel for metadata/table creation
from sqlmodel import SQLModel  # noqa: F401

# Import models so they register with SQLModel.metadata
from app.models import *  # noqa: F403
