from flask import Flask
from pymongo import MongoClient
from dotenv import load_dotenv, dotenv_values
from flask import jsonify, request, Response
from bson.json_util import dumps
import os
from datetime import datetime

load_dotenv()

app = Flask(__name__)

def respond(status_code=200, data=None):
    if status_code == 200:
        return Response(
            dumps({"ok": True, "data": data}),
            mimetype="application/json",
        ), status_code
    else:
        return Response(
            dumps({"ok": False, "message": data}),
            mimetype="application/json",
        ), status_code

@app.route("/halls/list", methods=["GET"]) # US01
def get_halls():
    try:
        halls = db.halls.find({}, {"_id": 0, "id": 1, "name": 1})
        return respond(data=list(halls))
    except Exception as e:
        print(f"Encountered error in /halls/list: {e}")
        return respond(500)

@app.route("/halls/<hall_id>", methods=["GET"]) # US02
def get_hall_details(hall_id):
    try:
        hall = db.halls.find_one({"id": hall_id})
        if hall is None:
            return respond(404, "Unknown hall ID")
        return respond(data=hall)
    except Exception as e:
        print(f"Encountered error in /halls/{hall_id}: {e}")
        return respond(500)

@app.route("/foods/<food_item_id>", methods=["GET"]) # US03, US13
def get_food_item_details(food_item_id):
    try:
        food_item = db.foods.find_one({"id": food_item_id})
        if food_item is None:
            return respond(404, "Unknown food item ID")
        return respond(data=food_item)
    except Exception as e:
        print(f"Encountered error in /foods/{food_item_id}: {e}")
        return respond(500)

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
    try:
        data = request.json
        foods = None
        print(f"Data: {data}")
        if data.get("name", None) is not None:
            foods = db.foods.find({"name": {"$regex": data.get("name", None), "$options": "i"}})
        elif data.get("hall_id", None) is not None:
            foods = db.foods.find({"foodEdges.0": data.get("hall_id", None)})
        elif data.get("tags", None) is not None:
            foods = db.foods.find({"filters.id": {"$in": data.get("tags", None)}})
        else:
            return respond(400, "No search criteria provided")
        if foods is None:
            return respond(404, "No foods found")
        return respond(data=foods)
    except Exception as e:
        print(f"Encountered error in /foods/search: {e}")
        print(f"Data: {request.json}")
        return respond(500)

@app.route("/config/tags", methods=["GET"]) # Dependencies of US06
def get_tags():
    try:
        tags = db.tags.find({})
        return respond(data=tags)
    except Exception as e:
        print(f"Encountered error in /config/tags: {e}")
        return respond(500)

@app.route("/foods/<food_item_id>/rate", methods=["POST"]) # US09, US10, US11
def rate_food_item(food_item_id):
    try:
        data = request.json
        user_id = data.get("user_id")
        score = data.get("score")
        content = data.get("content")
        if user_id is None or score is None or content is None:
            return respond(400, "User ID, score, and content are required")
        if db.users.find_one({"id": user_id}) is None:
            return respond(400, "User not found")
        if score != 0.0 and (score < 1 or score > 5):
            return respond(400, "Score must be between 1 and 5")
        if type(score) != float and score % 0.5 != 0:
            return respond(400, "Score must be a float and a multiple of 0.5")
        if type(content) != str:
            return respond(400, "Content must be a string")
        if len(content) > 1000:
            return respond(400, "Content must be less than 1000 characters")
        if score == 0.0: # DEL
            db.foods.update_one({"id": food_item_id}, {"$pull": {"ratings": {"user_id": user_id}}})
        else:
            result = db.foods.update_one( # Try Update
                {"id": food_item_id, "ratings.user_id": user_id},
                {"$set": {
                    "ratings.$.score": score,
                    "ratings.$.content": content,
                    "ratings.$.updatedAt": datetime.now()
                }}
            )
            if result.matched_count == 0: # Not exist, append
                db.foods.update_one(
                    {"id": food_item_id},
                    {"$push": {"ratings": {
                        "user_id": user_id,
                        "score": score,
                        "content": content,
                        "createdAt": datetime.now(),
                        "updatedAt": datetime.now()
                    }}}
                )
        ratings = db.foods.find_one({"id": food_item_id})["ratings"]
        averageScore = 0 # Avoid div 0
        if len(ratings) > 0:
            averageScore = sum([rating["score"] for rating in ratings]) / len(ratings)
        db.foods.update_one({"id": food_item_id}, {"$set": {"averageScore": averageScore}})
        return respond(200)
    except Exception as e:
        print(f"Encountered error in /foods/{food_item_id}/rate: {e}")
        return respond(500)

@app.route("/users/all_ratings", methods=["GET"]) # US12
def get_all_ratings():
    try:
        data = request.json
        user_id = data.get("user_id")
        if user_id is None:
            return respond(400, "User ID is required")
        if db.users.find_one({"id": user_id}) is None:
            return respond(400, "User not found")
        ratings = db.foods.find({"ratings.user_id": user_id})
        return respond(data=ratings)
    except Exception as e:
        print(f"Encountered error in /users/all_ratings: {e}")
        return respond(500)

@app.route("/users/account", methods=["GET"])
def get_user_account():
    try:
        data = request.json
        user_id = data.get("user_id")
        if user_id is None:
            return respond(400, "User ID is required")
        if db.users.find_one({"id": user_id}) is None:
            return respond(400, "User not found")
        return respond(data=db.users.find_one({"id": user_id}))
    except Exception as e:
        print(f"Encountered error in /users/account: {e}")
        return respond(500)

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