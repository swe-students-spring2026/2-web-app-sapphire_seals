from pymongo import MongoClient
from config import MONGO_DBNAME, MONGO_URL

client = MongoClient(MONGO_URL)
db = client.get_database(MONGO_DBNAME)
