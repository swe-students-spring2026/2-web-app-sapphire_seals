from flask import Flask
from pymongo import MongoClient
from dotenv import load_dotenv, dotenv_values
from flask import jsonify, request
import os

load_dotenv()

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "Hello, World!"

@app.route("/halls/list", methods=["GET"]) # US01
def get_halls():
    try:
        halls = db.halls.find({}, {"_id": 0, "id": 1, "name": 1})
        return jsonify({"ok": True, "data": halls}, status=200)
    except Exception as e:
        print("Encountered error in /halls/list: ",e.with_traceback())
        return jsonify({"ok": False}, status=500)

@app.route("/halls/<hall_id>", methods=["GET"]) # US02
def get_hall_details(hall_id):
    try:
        hall = db.halls.find_one({"id": hall_id})
        if hall is None:
            return jsonify({"ok": False, "message": "Unknown hall ID"}, status=404)
        return jsonify({"ok": True, "data": hall}, status=200)
    except Exception as e:
        print(f"Encountered error in /halls/{hall_id}: ",e.with_traceback())
        return jsonify({"ok": False}, status=500)

@app.route("/foods/<food_item_id>", methods=["GET"]) # US03
def get_food_item_details(food_item_id):
    try:
        food_item = db.foods.find_one({"id": food_item_id})
        if food_item is None:
            return jsonify({"ok": False, "message": "Unknown food item ID"}, status=404)
        return jsonify({"ok": True, "data": food_item}, status=200)
    except Exception as e:
        print(f"Encountered error in /foods/{food_item_id}: ",e.with_traceback())
        return jsonify({"ok": False}, status=500)

@app.route("/foods/search", methods=["POST"]) # US04, US05, US06
def search_food_items():
    '''
    POST /foods/search
    data: {
        "name": str,
        "hall_id": str,
        "tags": [tag_id, tag_id, ...]
    }
    '''
    data = request.json
    #return jsonify({"message": f"Searching for food items by name {data.get("name", None)}, hall ID {data.get("hall_id", None)}, tags {data.get("tags", None)}"})
    return jsonify({"message": "Not Implemented"}, status=501)

@app.route("/config/tags", methods=["GET"]) # Dependencies of US06
def get_tags():
    return jsonify({"message": "Not Implemented"}, status=501)

@app.route("/refresh", methods=["POST"])
def refresh():
    return jsonify({"message": "Not Implemented"}, status=501)

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