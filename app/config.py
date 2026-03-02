import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
MONGO_DBNAME = os.getenv("MONGO_DBNAME")
FLASK_HOST = os.getenv("FLASK_HOST")
FLASK_PORT = os.getenv("FLASK_PORT", 5000)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")