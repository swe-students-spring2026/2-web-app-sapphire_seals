from flask import Flask, session
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from dotenv import load_dotenv, dotenv_values
from flask import jsonify, request, Response
from bson.json_util import dumps
import os

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-me")

client = MongoClient(os.getenv("MONGO_URL"))
db = client.get_database(os.getenv("MONGO_DBNAME"))


@app.route("/register", methods=["POST"])
def register():
    try:
        body = request.json or {}
        username = (body.get("username") or "").strip()
        password = body.get("password") or ""    

        if not username or not password:
            return respond(400, "username and password required")
        user = db.users.find_one({"username": username})
        if not user is None:
            return respond(400, "existed user")
        hashed_pwd =   

@app.route("/login", methods=['POST'])
def login():
    """
    POST /login
    JSON:{"username": "...", "password": "..."}
    """
    try:
        body = request.json or {}
        username = (body.get("username") or "").strip()
        password = body.get("password") or ""

        if not username or not password:
            return respond(400, "username and password required")
        user = db.users.find_one({"username": username})
        if user is None:
            return respond(401, "invalid credentials")
        if not check_password_hash(user.get("password_hash", ""),password):
            return respond(401, "invalid credentials")
        
        session["user_id"] = str(user["_id"])
        session["username"] = user["username"]
        return respond(data = {"username": user["username"]})
    except Exception as e:
        print(f"Error in /login: {e}", flush=True)
        return respond(500)
    
@app.route("/logout", methods=["POST"])
def logout():
    try:
        session.clear()
        return respond(data=True)
    except Exception as e:
        print(f"Error in /logout: {e}")
        return respond(500)
    
@app.route("/me", methods=["GET"])
def me():
    if session.get("user_id") is None:
        return respond(401, "invalid credentials")
    return respond(data={"username": session.get("username")})



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

@app.route("/foods/<food_item_id>", methods=["GET"]) # US03
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