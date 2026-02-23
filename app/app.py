import os
from flask import Flask, session, request, Response
from bson.json_util import dumps

import config
from db import db, client
from auth import auth_bp

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-me")

app.register_blueprint(auth_bp)

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

@app.route("/me", methods=["GET"])
def me():
    if session.get("user_id") is None:
        return respond(401, "invalid credentials")
    return respond(data={"username": session.get("username")})

@app.route("/halls/list", methods=["GET"])  # US01
def get_halls():
    try:
        halls = db.halls.find({}, {"_id": 0, "id": 1, "name": 1})
        return respond(data=list(halls))
    except Exception as e:
        print(f"Encountered error in /halls/list: {e}")
        return respond(500)

@app.route("/halls/<hall_id>", methods=["GET"])  # US02
def get_hall_details(hall_id):
    try:
        hall = db.halls.find_one({"id": hall_id})
        if hall is None:
            return respond(404, "Unknown hall ID")
        return respond(data=hall)
    except Exception as e:
        print(f"Encountered error in /halls/{hall_id}: {e}")
        return respond(500)

@app.route("/foods/<food_item_id>", methods=["GET"])  # US03
def get_food_item_details(food_item_id):
    try:
        food_item = db.foods.find_one({"id": food_item_id})
        if food_item is None:
            return respond(404, "Unknown food item ID")
        return respond(data=food_item)
    except Exception as e:
        print(f"Encountered error in /foods/{food_item_id}: {e}")
        return respond(500)


@app.route("/foods/search", methods=["POST"])  # US04, US05, US06
def search_food_items():
    try:
        data = request.json
        foods = None
        if data.get("name", None) is not None:
            foods = db.foods.find(
                {"name": {"$regex": data.get("name", None), "$options": "i"}}
            )
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
        return respond(500)


@app.route("/config/tags", methods=["GET"])  # Dependencies of US06
def get_tags():
    try:
        tags = db.tags.find({})
        return respond(data=tags)
    except Exception as e:
        print(f"Encountered error in /config/tags: {e}")
        return respond(500)


@app.route("/mongo/ping/")
def mongo_ping():
    try:
        client.admin.command("ping")
        return "MongoDB is working!"
    except Exception as e:
        return f"MongoDB is not working: {e}"


if __name__ == '__main__':
    app.run(
        debug=True,
        host=config.FLASK_HOST or "0.0.0.0",
        port=int(config.FLASK_PORT or 5000)
    )