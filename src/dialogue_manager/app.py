import uvicorn
import requests
import pandas as pd
import ujson as json
from uuid import uuid4
from config import INITIAL_PROMPT, AUTH_URL, AGENT_URL
from fastapi.responses import RedirectResponse
from fastapi import FastAPI, status, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from crud import (
    get_message,
    get_user_dialogue_ids,
    get_dialogue_messages,
    get_all_dialogue_messages,
    create_message,
)
from datetime import datetime, timezone
from models import Base, DBMessage
from schemas import SchemaMessageType, SchemaAgentMessage, SchemaMessage
from database import SessionLocal, engine

Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()

@app.get("/", response_class=RedirectResponse, include_in_schema=False)
async def docs():
    return RedirectResponse(url="/docs")

def get_agent_reply(message: str) -> SchemaAgentMessage:
    bot_role = "\n CHATBOT : "
    response = requests.get(AGENT_URL, params={"prompt": f"{message} {bot_role}"})
    
    return SchemaAgentMessage(
        created_at=datetime.now(tz=timezone.utc),
        content=response.content,
        message_type=SchemaMessageType.ai,
    )

def create_dialogue_memory(messages: list) -> str:
    # construct the doubly linked list data structure for messages to ensure the order:
    #
    # to achieve precise message ordering, one could either sort messages 
    # based on created_at field or struct them in a linked list format.
    # as a result of variable datetime precision in different stores, datetime method 
    # can not be guaranteed to work all the time. 
    # so the the better approach would be to go with the linked list data structure.
    # to sort using a doubly linked list, we must first find the last message in the dialogue.
    # finding the last message is as easy as subtracting two unique sets: message_id and in_response_to.
    # 
    # i.e.
    # MESSAGE_IDS: {A, B, C}
    # IN_RSPNS_TO: {-, A, B}
    # MESSAGE_IDS - IN_RSPNS_TO = {C}
    
    response = {}

    messages = pd.DataFrame([x.__dict__ for x in messages])
    messages.drop(["_sa_instance_state"], axis=1, inplace=True)
    msg_ids = set(messages["id"])
    in_response_to_ids = set(messages["in_response_to"])
    last_msg_id = list(msg_ids - in_response_to_ids)[0]
    response["last_message_id"] = last_msg_id

    # Create the dialogue history
    ordered_messages = []
    counter = len(messages) -1
    while last_msg_id is not None:
        temp_msg_type = messages.loc[messages.id == last_msg_id]["message_type"].values[0]
        temp_content = messages.loc[messages.id == last_msg_id]["content"].values[0]
        ordered_messages.append(f"{temp_msg_type + " :" if counter > 0 else ""} {temp_content}")
        last_msg_id = messages.loc[messages.id == last_msg_id]["in_response_to"].values[0]
        counter -= 1
    ordered_messages = list(reversed(ordered_messages))
    
    dialogue_memory = " \n ".join(ordered_messages)
    response["memory"] = dialogue_memory.strip()

    return response


@app.post("/api/v1/dialogue")
async def dialogue(
    message: str = None, dialogue_id: str = None, auth: str = Header(None), db: Session = Depends(get_db)
):
    try:
        # Simple User Info Checker
        user_info = requests.get(AUTH_URL, headers={"Authorization": auth})
        if user_info.status_code != 200:
            raise HTTPException(user_info.status_code)

        user_info = json.loads(user_info.content)
        # Message can not be empty since in our design a dialogue is only happening after the first message
        if message is None or message == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Message is empty"
            )
        message_id = str(uuid4())

        # Check if this is a new dialogue
        if dialogue_id is None:
            # a new dialogue
            dialogue_id = str(uuid4())

            # create augmented message = prompt + message
            message = f"{INITIAL_PROMPT} \n\n HUMAN : {message}"

            # create a new message object for a new dialogue id
            msg = SchemaMessage(
                id=message_id,
                user_id=user_info["id"],
                dialogue_id=dialogue_id,
                created_at=datetime.now(timezone.utc),
                content=message,
                message_type=SchemaMessageType.human,
                in_response_to=None,
            )

            # generate a response based on the augmented message
            reply_content = get_agent_reply(message=message)

            # create a new message object for ai reply
            rply = SchemaMessage(
                id=str(uuid4()),
                user_id=user_info["id"],
                dialogue_id=dialogue_id,
                created_at=reply_content.created_at,
                content=reply_content.content,
                message_type=reply_content.message_type,
                in_response_to=message_id,
            )

            # store messages
            create_message(db=db, message=msg)
            create_message(db=db, message=rply)

            return {
                "memory":msg.content,
                "reply": rply
            }
        else:
            # continuation on a previous dialogue

            # get all dialogue messages
            msgs = get_all_dialogue_messages(db=db, dialogue_id=dialogue_id, user_id=user_info["id"])
            
            # check if there is such a chat or the user has the right permissions to read that
            if len(msgs) == 0:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dialogue not found or user is not permitted to read")

            # create the dialogue memory
            memory = create_dialogue_memory(msgs)
            last_message_id = memory["last_message_id"]
            dialogue_memory = memory["memory"]
            dialogue_memory += f" \n HUMAN : {message}"

            # create a new message object with memory
            msg = SchemaMessage(
                id=message_id,
                user_id=user_info["id"],
                dialogue_id=dialogue_id,
                created_at=datetime.now(timezone.utc),
                content=message,
                message_type=SchemaMessageType.human,
                in_response_to=last_message_id,
            )
            
            # generate a response based on the augmented message
            reply_content = get_agent_reply(message=dialogue_memory)

            # create a new message object for ai reply
            rply = SchemaMessage(
                id=str(uuid4()),
                user_id=user_info["id"],
                dialogue_id=dialogue_id,
                created_at=reply_content.created_at,
                content=reply_content.content,
                message_type=reply_content.message_type,
                in_response_to=message_id,
            )

            # store messages
            create_message(db=db, message=msg)
            create_message(db=db, message=rply)

            return({"memory":dialogue_memory, "reply":rply})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unknown error occured: {e}",
        )


@app.get("/api/v1/dialogues")
async def get_dialogues(skip:int = 0, limit:int=10, auth: str = Header(None), db: Session = Depends(get_db)):
    try:
        # Simple User Info Checker
        user_info = requests.get(AUTH_URL, headers={"Authorization": auth})
        if user_info.status_code != 200:
            raise HTTPException(user_info.status_code)

        user_info = json.loads(user_info.content)

        return {"dialogue_ids":[x[0] for x in get_user_dialogue_ids(db=db, user_id=user_info["id"], skip=skip, limit=limit)]}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unknown error occured: {e}",
        )   

@app.get("/api/v1/{dialogue_id}/messages")
async def get_messages(dialogue_id: str = None,skip:int = 0, limit:int=10, auth: str = Header(None), db: Session = Depends(get_db)):
    try:
        # Simple User Info Checker
        user_info = requests.get(AUTH_URL, headers={"Authorization": auth})
        if user_info.status_code != 200:
            raise HTTPException(user_info.status_code)

        user_info = json.loads(user_info.content)

        return get_dialogue_messages(
            db=db,
            dialogue_id=dialogue_id,
            user_id=user_info["id"],
            skip=skip,
            limit=limit,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unknown error occured: {e}",
        )  
