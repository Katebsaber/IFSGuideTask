from enum import Enum
from typing import List
from pydantic import BaseModel, AwareDatetime

class SchemaMessageType(str, Enum):
    human = "HUMAN"
    ai = "CHATBOT"

class SchemaMessage(BaseModel):
    id: str
    user_id: str
    dialogue_id: str
    created_at: AwareDatetime
    content: str
    message_type: SchemaMessageType
    in_response_to: str | None = None

    class Config:
        from_attributes = True

class SchemaAgentMessage(BaseModel):
    created_at: AwareDatetime
    content: str
    message_type: SchemaMessageType


if __name__=="__main__":
    print(SchemaMessageType.human)