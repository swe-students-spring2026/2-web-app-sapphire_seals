from flask import Blueprint, request, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import db 

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return render_template("login.html", title="Login", show_header=False, message="Username and password required")
        
        user = db.users.find_one({"username": username})
        if user is None or not check_password_hash(user.get("password_hash", ""), password):
            return render_template("login.html", title="Login", show_header=False, message="Invalid credentials")
        
        session["user_id"] = str(user["_id"])
        session["username"] = user["username"]
        
        return redirect(url_for('me')) 
    
    return render_template("login.html", title="Login", show_header=False)

@auth_bp.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return render_template("register.html", title="Register", show_header=False, message="Username and password required")

        existing_user = db.users.find_one({"username": username})
        if existing_user:
            return render_template("register.html", title="Register", show_header=False, message="Username already exists")

        hashed_pwd = generate_password_hash(password)
        result = db.users.insert_one({"username": username, "password_hash": hashed_pwd})
        
        session["user_id"] = str(result.inserted_id)
        session["username"] = username
        
        return redirect(url_for('me'))

    return render_template("register.html", title="Register", show_header=False)

@auth_bp.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    return redirect(url_for('auth.login'))