import os
from flask import Flask, request, render_template, session
from bson.json_util import dumps
from bson.objectid import ObjectId

import config
from db import db, client
from utils import require_auth, respond

from auth import auth_bp
from foods import foods_bp
from api import api_bp

import datetime

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-me")

app.register_blueprint(auth_bp)
app.register_blueprint(foods_bp)
app.register_blueprint(api_bp)

#### Pages ####

@app.route("/")
@app.route("/home")
def home():
    halls = list(db.halls.find())
    return render_template("home.html", title="Home", halls=halls, show_header=False)

@app.route("/halls")
def halls_list():
    halls = list(db.halls.find())
    return render_template("halls.html", title="Dining Halls", halls=halls, show_header=False)

#### Authenticated ####

@app.route("/account")
@require_auth
def account_page(user_id):
    user = db.users.find_one({"_id": ObjectId(user_id)}, {"_id": 0, "username": 1, "email": 1, "netid": 1})
    if user is None:
        return respond(404, "User not found")
    return "NOT_IMPLEMENTED"
    #return render_template("account.html", title="Account", user=user, show_header=False)

#### Status ####

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
