from flask import Flask, render_template
from pymongo import MongoClient
from dotenv import load_dotenv, dotenv_values
from flask import jsonify, request, Response
from bson.json_util import dumps
import os

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
    """
    POST /foods/search
    data: {
        "name": str,
        "hall_id": str,
        "tags": [tag_id, tag_id, ...]
    }
    """
    try:
        data = request.json
        foods = None
        print(f"Data: {data}")
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
        print(f"Data: {request.json}")
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


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return render_template(
            "login.html", title="Login", show_header=False, message="Error Message"
        )
    else:
        return render_template("login.html", title="Login", show_header=False)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        return render_template(
            "register.html",
            title="Register",
            show_header=False,
            message="Error Message",
        )
    else:
        return render_template("register.html", title="Register", show_header=False)


if __name__ == "__main__":
    client = MongoClient(os.getenv("MONGO_URL"))
    db = client.get_database(os.getenv("MONGO_DBNAME"))
    app.run(
        debug=True, host=os.getenv("FLASK_HOST"), port=os.getenv("FLASK_PORT", 5000)
    )
