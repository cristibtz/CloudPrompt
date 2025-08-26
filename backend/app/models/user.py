from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, nullable=False)
    keycloak_id = Column(String(100), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    credits = Column(Integer, default=0, nullable=False)
    
    # Relationship to Prompts
    prompts = relationship("Prompt", back_populates="user")
    credentials = relationship("Credential", back_populates="user")