import os
from sqlalchemy import URL

INITIAL_PROMPT = "As a helpful IFS therapist chatbot, your role is to guide users through a simulated IFS session in a safe and supportive manner with a few changes to the exact steps of the IFS model."
AUTH_URL = os.getenv("AUTH_URL", "http://127.0.0.1:8080/api/v1/me")
SQL_ALCHEMY_DATABASE_URL = URL.create(
    drivername="postgresql",
    username=os.getenv("PG_USERNAME", "postgres"),
    password=os.getenv("PG_PASSWORD", "admin"),
    host=os.getenv("PG_HOST", "127.0.0.1"),
    port=os.getenv("PG_PORT", 5432),
    database=os.getenv("PG_DATABASE", "postgres"),
)
