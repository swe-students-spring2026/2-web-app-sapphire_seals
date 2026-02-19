from flask import Flask
from pymongo import MongoClient
from dotenv import load_dotenv, dotenv_values
import os

load_dotenv()

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "Hello, World!"

@app.route("/mongo/ping/")
def mongo_ping():
    try:
        client.admin.command("ping")
        return "MongoDB is working!"
    except Exception as e:
        return f"MongoDB is not working: {e}"

if __name__ == '__main__':
    client = MongoClient(os.getenv("MONGO_URL"))
    db = client.get_database(os.getenv("MONGO_DBNAME"))
    app.run(
        debug=True,
        host=os.getenv("FLASK_HOST"),
        port=os.getenv("FLASK_PORT", 5000)
    )