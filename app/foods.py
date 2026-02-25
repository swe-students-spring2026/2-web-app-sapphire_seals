import os
from flask import Flask, session, request, render_template, redirect
from functools import wraps

import config
from db import db, client
from auth import auth_bp

import datetime

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-me")

app.register_blueprint(auth_bp)


#### Authentication Helper ####

def require_auth(view_fn):
    @wraps(view_fn)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return redirect("/login")
        if db.users.find_one({"_id": user_id}) is None:
            return redirect("/login")
        kwargs["user_id"] = user_id
        return view_fn(*args, **kwargs)
    return wrapper


#### Page Routes ####

@app.route("/")
def home():
    try:
        halls = list(db.halls.find())
        return render_template("home.html", title="Home", halls=halls, show_header=False)
    except Exception as e:
        print(f"Error on home page: {e}")
        return render_template("home.html", title="Home", halls=[], show_header=False)


@app.route("/halls/<hall_id>")
def hall_detail_page(hall_id):
    try:
        hall = db.halls.find_one({"id": hall_id})
        if hall is None:
            return "Dining hall not found", 404
        foods = list(db.foods.find({"foodEdges.0": hall_id}))
        return render_template("hall_detail.html", title=hall.get("name", "Dining Hall"), hall=hall, foods=foods, show_header=False)
    except Exception as e:
        print(f"Error on hall detail page: {e}")
        return "Something went wrong", 500


@app.route("/meal/<food_item_id>")
def meal_detail_page(food_item_id):
    food = db.foods.find_one({"id": food_item_id})
    if food is None:
        return "Food item not found", 404

    avg_score = food.get("averageScore", 0)
    message = request.args.get("message", None)

    return render_template(
        "meal_details.html",
        title="Meal Details",
        food=food,
        avg_score=avg_score,
        message=message,
        show_header=False,
    )


@app.route("/meal/<food_item_id>/review", methods=["GET", "POST"])
def meal_review_page(food_item_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    food = db.foods.find_one({"id": food_item_id})
    if food is None:
        return "Food item not found", 404

    # GET — show the form
    if request.method == "GET":
        return render_template(
            "meal_review.html",
            title="Meal Review",
            food=food,
            message=None,
            show_header=False,
        )

    # POST — process the review
    score_raw = request.form.get("score")
    content = request.form.get("content", "").strip()

    if score_raw is None:
        return render_template(
            "meal_review.html",
            title="Meal Review",
            food=food,
            message="Please select a star rating.",
            show_header=False,
        )

    score = float(score_raw)

    if score < 1 or score > 5:
        return render_template(
            "meal_review.html",
            title="Meal Review",
            food=food,
            message="Rating must be between 1 and 5.",
            show_header=False,
        )

    if not content:
        return render_template(
            "meal_review.html",
            title="Meal Review",
            food=food,
            message="Please write a review.",
            show_header=False,
        )

    if len(content) > 1000:
        return render_template(
            "meal_review.html",
            title="Meal Review",
            food=food,
            message="Review must be under 1000 characters.",
            show_header=False,
        )

    # Try to update existing rating by this user
    result = db.foods.update_one(
        {"id": food_item_id, "ratings.user_id": user_id},
        {
            "$set": {
                "ratings.$.score": score,
                "ratings.$.content": content,
                "ratings.$.updatedAt": datetime.datetime.now(),
            }
        },
    )

    # If no existing rating, push a new one
    if result.matched_count == 0:
        db.foods.update_one(
            {"id": food_item_id},
            {
                "$push": {
                    "ratings": {
                        "user_id": user_id,
                        "score": score,
                        "content": content,
                        "createdAt": datetime.datetime.now(),
                        "updatedAt": datetime.datetime.now(),
                    }
                }
            },
        )

    # Recalculate average score
    updated_food = db.foods.find_one({"id": food_item_id})
    ratings = updated_food.get("ratings", [])
    if len(ratings) > 0:
        avg = sum(r["score"] for r in ratings) / len(ratings)
    else:
        avg = 0
    db.foods.update_one({"id": food_item_id}, {"$set": {"averageScore": avg}})

    return redirect(f"/meal/{food_item_id}?message=Review+submitted+successfully!")


@app.route("/search")
def search_page():
    query = request.args.get("q", "").strip()
    results = []
    if query:
        results = list(db.foods.find(
            {"name": {"$regex": query, "$options": "i"}}
        ))
    return render_template("search.html", title="Search", query=query, results=results, show_header=False)


@app.route("/favorites")
@require_auth
def favorites_page(user_id):
    rated_foods = list(db.foods.find({"ratings.user_id": user_id}))
    return render_template("favorites.html", title="Favorites", foods=rated_foods, show_header=False)


@app.route("/account")
@require_auth
def account_page(user_id):
    user = db.users.find_one({"_id": user_id}, {"password_hash": 0})
    return render_template("account.html", title="Account", user=user, show_header=False)


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
