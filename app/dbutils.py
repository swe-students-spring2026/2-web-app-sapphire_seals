from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

client = MongoClient(os.getenv("MONGO_URL"))
db = client.get_database(os.getenv("MONGO_DBNAME"))

def push_halls(data):
    # https://apiv4.dineoncampus.com/sites/5cab70a48e45bf099f4a9970/locations-public?for_map=true
    data = data["standaloneLocations"]
    for i in range(len(data)):
        data[i]["_id"] = data[i]["id"]
    db.halls.insert_many(data)

def push_hall_details(data):
    return