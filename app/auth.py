from flask import Blueprint, request, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import db 
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/")
@auth_bp.route("/login", methods=['GET', 'POST'])
def login():
    if session.get("user_id"):
        return redirect(url_for('home'))
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if not username or not password:
            return render_template("login.html", title="Login", show_header=False, message="Username and password required")
        
        username = username.strip()
        user = db.users.find_one({"username": username})
        if user is None or not check_password_hash(user.get("password_hash", ""), password):
            return render_template("login.html", title="Login", show_header=False, message="Invalid credentials")
        
        session["user_id"] = str(user["_id"])
        session["username"] = user["username"]
        
        return redirect(url_for('home')) # TODO: Redirect to home page
    
    return render_template("login.html", title="Login", show_header=False)

@auth_bp.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        netid = request.form.get("netid", "")
        email = request.form.get("email", "")
        re_enter_password = request.form.get("re-enter-password", "")

        if not username or not password or not netid or not email or not re_enter_password:
            return render_template("register.html", title="Register", show_header=False, message="Username and password required")

        username = username.strip()
        netid = netid.strip()
        email = email.strip()

        if password != re_enter_password:
            return render_template("register.html", title="Register", show_header=False, message="Passwords do not match")

        existing_user = db.users.find_one({"username": username})
        if existing_user:
            return render_template("register.html", title="Register", show_header=False, message="Username already exists")

        hashed_pwd = generate_password_hash(password)
        result = db.users.insert_one({
            "username": username, 
            "password_hash": hashed_pwd,
            "netid": netid.lower(),
            "email": email.lower(),
            "createdAt": datetime.now(),
            "updatedAt": datetime.now()
        })
        
        session["user_id"] = str(result.inserted_id)
        session["username"] = username
        
        return redirect(url_for('home')) # TODO: Redirect to home page

    return render_template("register.html", title="Register", show_header=False)

@auth_bp.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    return redirect(url_for('auth.login'))