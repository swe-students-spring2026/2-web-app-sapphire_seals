import os
from flask import Flask, session, request, render_template, redirect, Blueprint
from functools import wraps

import config
from db import db, client
from utils import require_auth # Authentication helper
from utils import respond # Response helper

import datetime


foods_bp = Blueprint('foods', __name__)

#### Page Routes ####

@foods_bp.route("/halls/<hall_id>")
def hall_detail_page(hall_id):
    hall = db.halls.find_one({"id": hall_id})
    if hall is None:
        return "Dining hall not found", 404
    foods = list(db.foods.find({"foodEdges.0": hall_id}))

    # Build meals list in the format hall_detail.html expects
    meals = []
    for food in foods:
        # Get first filter name as the category
        category = "Menu Item"
        if food.get("filters") and len(food["filters"]) > 0:
            category = food["filters"][0].get("name", "Menu Item")

        meals.append({
            "id": food.get("id"),
            "name": food.get("name", "Unknown"),
            "desc": food.get("desc", ""),
            "category": category,
            "calories": food.get("calories", ""),
            "averageScore": food.get("averageScore", 0),
        })

    # Collect all reviews from foods in this hall
    reviews = []
    for food in foods:
        for r in food.get("ratings", []):
            reviews.append({
                "user": r.get("user_id", "Anonymous"),
                "text": r.get("content", ""),
                "rating": int(r.get("score", 0)),
                "food_name": food.get("name", ""),
            })

    return render_template(
        "hall_detail.html",
        title=hall.get("name", "Dining Hall"),
        hall=hall,
        meals=meals,
        reviews=reviews,
        show_header=False,
    )


@foods_bp.route("/meal/<food_item_id>")
def meal_detail_page(food_item_id):
    food = db.foods.find_one({"id": food_item_id})
    if food is None:
        return respond(404, "Food item not found")

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


@foods_bp.route("/meal/<food_item_id>/review", methods=["GET", "POST", "DELETE"])
@require_auth
def meal_review_page(food_item_id, user_id):
    def meal_review_template(message=None):
        return render_template(
            "meal_review.html",
            title="Meal Review",
            food=food,
            message=message,
            show_header=False,
        )

    food = db.foods.find_one({"id": food_item_id})
    if food is None:
        return meal_review_template(message="Food item not found!")

    # GET — show the form
    if request.method == "GET":
        return meal_review_template()

    # DELETE — delete the review (TODO: NOT IMPLEMENTED)
    if request.method == "DELETE":
        result = db.foods.update_one({"id": food_item_id}, {"$pull": {"ratings": {"user_id": user_id}}})
        if result.modified_count == 0:
            return meal_review_template(message="You haven't rated this food item yet!")
        return redirect(f"/meal/{food_item_id}?message=Review+deleted+successfully!")

    # POST — process the review
    score_raw = request.form.get("score")
    content = request.form.get("content", "").strip()

    if score_raw is None:
        return meal_review_template(message="Please select a star rating.")

    try:
        score = float(score_raw)
    except ValueError:
        return meal_review_template(message="Invalid star rating.")

    if score < 1 or score > 5:
        return meal_review_template(message="Rating must be between 1 and 5.")
    if not content:
        return meal_review_template(message="Please write a review.")
    if len(content) > 1000:
        return meal_review_template(message="Review must be under 1000 characters.")

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


@foods_bp.route("/search")
def search_page():
    query = request.args.get("q", "").strip()
    results = []
    if query:
        results = list(db.foods.find(
            {"name": {"$regex": query, "$options": "i"}}
        ))
    return render_template("search.html", title="Search", query=query, results=results, show_header=False)


@foods_bp.route("/users/my_ratings", methods=["GET"])
@require_auth
def my_ratings(user_id):
    ratings = list(db.foods.find({"ratings.user_id": user_id}))
    return "NOT IMPLEMENTED"
    #return render_template("my_ratings.html", title="My Ratings", ratings=ratings, show_header=False)

@foods_bp.route("/users/all_ratings", methods=["POST"])
def all_ratings():
    data = request.json
    user_id = data.get("user_id")
    if user_id is None:
        return respond(400, "User ID is required")
    user = db.users.find_one({"_id": user_id}, {"_id": 0, "username": 1})
    if user is None:
        return respond(404, "User not found")
    ratings = list(db.foods.find({"ratings.user_id": user_id}))
    return "NOT_IMPLEMENTED"
    #return render_template("all_ratings.html", title="Ratings from {user}".format(user["username"]), ratings=ratings, show_header=False)
