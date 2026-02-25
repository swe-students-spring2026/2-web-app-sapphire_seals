from functools import wraps
from functools import wraps
from flask import session
from db import db
from flask import Response
from bson.json_util import dumps
from bson.objectid import ObjectId

def require_auth(view_fn):
    @wraps(view_fn)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return respond(401, "invalid credentials")
        if db.users.find_one({"_id": ObjectId(user_id)}) is None:
            return respond(404, "User not found")
        kwargs["user_id"] = user_id
        return view_fn(*args, **kwargs)
    return wrapper

def respond(status_code=200, data=None):
    if status_code == 200:
        return Response(
            dumps({"ok": True, "data": data}),
            mimetype="application/json",
        ), status_code
    else:
        if True:
            raise Exception(f"Invalid status code: {status_code}")
        return Response(
            dumps({"ok": False, "message": data}),
            mimetype="application/json",
        ), status_code