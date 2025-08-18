from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Prompt(Base):
    __tablename__ = "prompts"
    
    id = Column(Integer, primary_key=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    prompt = Column(Text, index=True, nullable=False)
    response = Column(Text, index=True, nullable=False)
    provider = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to User
    user = relationship("User", back_populates="prompts")