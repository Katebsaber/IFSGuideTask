from sqlalchemy.orm import Session

from models import DBMessage
from schemas import SchemaMessage


def get_message(db: Session, message_id: str, user_id: str):
    return (
        db.query(DBMessage)
        .filter(DBMessage.id == message_id)
        .filter(DBMessage.user_id == user_id)
        .first()
    )


def get_user_dialogue_ids(db: Session, user_id: str, skip: int = 0, limit: int = 10):
    return (
        db.query(DBMessage.dialogue_id)
        .filter(DBMessage.user_id == user_id)
        .distinct(DBMessage.dialogue_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_all_dialogue_messages(db: Session, dialogue_id: str, user_id: str):
    return (
        db.query(DBMessage)
        .filter(DBMessage.dialogue_id == dialogue_id)
        .filter(DBMessage.user_id == user_id)
        .order_by(DBMessage.created_at)
        .all()
    )


def get_dialogue_messages(
    db: Session, dialogue_id: str, user_id: str, skip: int = 0, limit: int = 10
):
    return (
        db.query(DBMessage)
        .filter(DBMessage.dialogue_id == dialogue_id)
        .filter(DBMessage.user_id == user_id)
        .order_by(DBMessage.created_at)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_message(db: Session, message: SchemaMessage):
    db_message = DBMessage(
        id=message.id,
        user_id=message.user_id,
        dialogue_id=message.dialogue_id,
        created_at=message.created_at,
        content=message.content,
        message_type=message.message_type,
        in_response_to=message.in_response_to,
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)


if __name__ == "__main__":
    from datetime import datetime, timezone
    from schemas import SchemaMessageType

    msg = SchemaMessage(
        id="test_msg_id",
        user_id="test_user",
        dialogue_id="test_dilg_id",
        created_at=datetime.now(timezone.utc),
        content="hello",
        message_type=SchemaMessageType.human,
        in_response_to=None,
    )
    # print(msg)
    # print(msg.user_id)

    from models import Base
    from database import SessionLocal, engine

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # create_message(db=db, message=msg)

    print(
        get_dialogue_messages(
            db=db,
            dialogue_id="b69dfb2e-e1c9-48f0-879a-f1243c0d58ef",
            user_id="c85f5866-852e-40d8-a4f2-2dada07c7708",
            skip=0,
            limit=10,
        )
    )
