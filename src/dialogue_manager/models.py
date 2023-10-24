from sqlalchemy import Column, String, Integer, DateTime, Text
from database import Base

class DBMessage(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    dialogue_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    content = Column(Text) 
    message_type = Column(String, nullable=False)
    in_response_to = Column(String, nullable=True, index=True)
