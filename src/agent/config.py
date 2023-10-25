import os

MODEL_PATH = os.getenv("MODEL_PATH", "/app/model.bin")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 100))