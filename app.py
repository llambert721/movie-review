from flask import Flask, request, jsonify, send_from_directory, session, redirect
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os
import re
import urllib.parse

# Load .env file if present
def load_env(filepath=".env"):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = val

load_env()

def get_mongo_uri():
    if "MONGO_URI" in os.environ and os.environ["MONGO_URI"].strip():
        return os.environ["MONGO_URI"].strip()
    user = os.environ.get("MONGO_USER", "").strip()
    pwd = os.environ.get("MONGO_PASSWORD", "").strip()
    if user and pwd:
        user_enc = urllib.parse.quote_plus(user)
        pwd_enc = urllib.parse.quote_plus(pwd)
        return f"mongodb+srv://{user_enc}:{pwd_enc}@cluster0.sdneqlg.mongodb.net/?appName=Cluster0"
    raise ValueError(
        "Missing MongoDB credentials! Please define MONGO_USER and MONGO_PASSWORD (or MONGO_URI) in your .env file."
    )

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "movie-review-secret-key-2026")

# Database connection
MONGO_URI = get_mongo_uri()
client = MongoClient(MONGO_URI)
db = client["MovieDB"]

users_collection = db["User"]
movies_collection = db["Movie"]
posts_collection = db["Post"]


# Helper: find user by ObjectId or username
def find_user_by_id_or_username(identifier):
    user = None
    if ObjectId.is_valid(identifier):
        try:
            user = users_collection.find_one({"_id": ObjectId(identifier)})
        except Exception:
            pass
    if not user:
        user = users_collection.find_one({
            "$or": [
                {"username": identifier},
                {"email": identifier.lower()}
            ]
        })
    return user


# Helper: format post with movie details
def format_post(post):
    movie_id = post.get("movie_id")
    movie = None
    if movie_id:
        if ObjectId.is_valid(str(movie_id)):
            try:
                movie = movies_collection.find_one({"_id": ObjectId(str(movie_id))})
            except Exception:
                pass
        if not movie:
            movie = movies_collection.find_one({"_id": movie_id})

    return {
        "id": str(post["_id"]),
        "user_id": str(post.get("user_id", "")),
        "movie_id": str(movie_id) if movie_id else "",
        "movie_title": movie.get("title") if movie else post.get("movie_title", "Unknown Movie"),
        "movie_genre": movie.get("genre", "") if movie else "",
        "movie_release_date": movie.get("release_date", "") if movie else "",
        "rating": post.get("rating", 0),
        "comment": post.get("comment", ""),
        "created_at": str(post.get("created_at", ""))
    }


# Helper: find post by id
def find_post_by_id(post_id):
    if not ObjectId.is_valid(post_id):
        return None
    try:
        return posts_collection.find_one({"_id": ObjectId(post_id)})
    except Exception:
        return None


# Helper: check if session user owns a post
def is_post_owner(post, user_id):
    post_user_id = post.get("user_id")
    if post_user_id is None or user_id is None:
        return False
    return str(post_user_id) == str(user_id)


# ==========================================
# PAGE ROUTES
# ==========================================

@app.get("/")
def index():
    return send_from_directory(".", "login.html")

@app.get("/login.html")
def login_page():
    return send_from_directory(".", "login.html")

@app.get("/adduser.html")
def adduser_page():
    return send_from_directory(".", "adduser.html")

@app.get("/addadmin.html")
def addadmin_page():
    if "user_id" not in session:
        return redirect("/login.html")
    if not session.get("is_admin"):
        return redirect("/myprofileuser.html")
    return send_from_directory(".", "addadmin.html")

@app.get("/myprofileadmin.html")
def myprofileadmin_page():
    if "user_id" not in session:
        return redirect("/login.html")
    if not session.get("is_admin"):
        return redirect("/myprofileuser.html")
    return send_from_directory(".", "myprofileadmin.html")

@app.get("/myprofileuser.html")
def myprofileuser_page():
    if "user_id" not in session:
        return redirect("/login.html")
    return send_from_directory(".", "myprofileuser.html")

@app.get("/userpage.html")
def userpage_page():
    return send_from_directory(".", "userpage.html")

# Backwards compatibility routes
@app.get("/user")
def legacy_user():
    if "user_id" not in session:
        return redirect("/login.html")
    return redirect("/myprofileuser.html")

@app.get("/admin")
def legacy_admin():
    if "user_id" not in session:
        return redirect("/login.html")
    if not session.get("is_admin"):
        return jsonify({"error": "Access denied"}), 403
    return redirect("/myprofileadmin.html")


# ==========================================
# AUTHENTICATION & USER API ENDPOINTS
# ==========================================

# POST /api/login
@app.post("/api/login")
def login():
    data = request.get_json() or {}
    username = (data.get("username") or data.get("email") or "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = users_collection.find_one({
        "$or": [
            {"username": username},
            {"email": username.lower()}
        ]
    })

    if not user:
        return jsonify({"error": "Invalid username or password"}), 401

    if not check_password_hash(user.get("password_hash", ""), password):
        return jsonify({"error": "Invalid username or password"}), 401

    is_admin = bool(user.get("is_admin", user.get("role") == "admin"))
    display_name = user.get("display_name") or user.get("name") or user.get("username", "")

    session["user_id"] = str(user["_id"])
    session["username"] = user.get("username", username)
    session["display_name"] = display_name
    session["is_admin"] = is_admin
    session["role"] = "admin" if is_admin else "user"

    return jsonify({
        "user_id": str(user["_id"]),
        "username": session["username"],
        "display_name": display_name,
        "is_admin": is_admin,
        "role": session["role"]
    })


# GET /api/me
@app.get("/api/me")
def get_me():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user = None
    if ObjectId.is_valid(session["user_id"]):
        try:
            user = users_collection.find_one({"_id": ObjectId(session["user_id"])})
        except Exception:
            pass

    if user:
        is_admin = bool(user.get("is_admin", user.get("role") == "admin"))
        display_name = user.get("display_name") or user.get("name") or user.get("username", "")
        return jsonify({
            "user_id": str(user["_id"]),
            "username": user.get("username", session.get("username", "")),
            "display_name": display_name,
            "is_admin": is_admin,
            "role": "admin" if is_admin else "user"
        })

    return jsonify({
        "user_id": session["user_id"],
        "username": session.get("username", ""),
        "display_name": session.get("display_name", ""),
        "is_admin": session.get("is_admin", False),
        "role": session.get("role", "user")
    })


# POST /api/logout
@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"})


# POST /api/register (Create regular user account)
@app.post("/api/register")
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    display_name = data.get("display_name", "").strip()
    password = data.get("password", "")

    if not username:
        return jsonify({"error": "Username is required"}), 400
    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters long"}), 400
    if not password:
        return jsonify({"error": "Password is required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400

    # Check if username is taken (case-insensitive)
    existing = users_collection.find_one({
        "username": {"$regex": f"^{re.escape(username)}$", "$options": "i"}
    })
    if existing:
        return jsonify({"error": "Username is already taken"}), 409

    new_user = {
        "username": username,
        "display_name": display_name or username,
        "password_hash": generate_password_hash(password),
        "is_admin": False
    }

    result = users_collection.insert_one(new_user)
    return jsonify({
        "message": "User registered successfully",
        "user_id": str(result.inserted_id)
    }), 201


# POST /api/admin/create-admin (Admin creates another admin account)
@app.post("/api/admin/create-admin")
def create_admin():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    if not session.get("is_admin"):
        return jsonify({"error": "Administrator privilege required"}), 403

    data = request.get_json() or {}
    username = data.get("username", "").strip()
    display_name = data.get("display_name", "").strip()
    password = data.get("password", "")

    if not username:
        return jsonify({"error": "Username is required"}), 400
    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters long"}), 400
    if not password:
        return jsonify({"error": "Password is required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400

    existing = users_collection.find_one({
        "username": {"$regex": f"^{re.escape(username)}$", "$options": "i"}
    })
    if existing:
        return jsonify({"error": "Username is already taken"}), 409

    new_admin = {
        "username": username,
        "display_name": display_name or username,
        "password_hash": generate_password_hash(password),
        "is_admin": True
    }

    result = users_collection.insert_one(new_admin)
    return jsonify({
        "message": "Administrator registered successfully",
        "user_id": str(result.inserted_id)
    }), 201


# ==========================================
# POSTS & USER PROFILE API ENDPOINTS
# ==========================================

# GET /api/my/posts
@app.get("/api/my/posts")
def get_my_posts():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]
    query = {"$or": [{"user_id": user_id}]}
    if ObjectId.is_valid(user_id):
        query["$or"].append({"user_id": ObjectId(user_id)})

    posts = list(posts_collection.find(query).sort("_id", -1))
    return jsonify([format_post(p) for p in posts])


# GET /api/users/<identifier> (Public profile by username or id)
@app.get("/api/users/<identifier>")
def get_user_profile(identifier):
    user = find_user_by_id_or_username(identifier)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "user_id": str(user["_id"]),
        "username": user.get("username", ""),
        "display_name": user.get("display_name") or user.get("username", ""),
        "is_admin": bool(user.get("is_admin", False))
    })


# GET /api/users/<identifier>/posts (List of specific user's posts)
@app.get("/api/users/<identifier>/posts")
def get_user_posts(identifier):
    user = find_user_by_id_or_username(identifier)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_id = str(user["_id"])
    query = {"$or": [{"user_id": user_id}, {"user_id": user["_id"]}]}

    posts = list(posts_collection.find(query).sort("_id", -1))
    return jsonify([format_post(p) for p in posts])


# PUT /api/posts/<post_id> (Owner edits own review)
@app.put("/api/posts/<post_id>")
def update_post(post_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    post = find_post_by_id(post_id)
    if not post:
        return jsonify({"error": "Review not found"}), 404

    if not is_post_owner(post, session["user_id"]):
        return jsonify({"error": "You can only edit your own reviews"}), 403

    data = request.get_json() or {}
    rating = data.get("rating")
    comment = data.get("comment")

    if rating is None:
        return jsonify({"error": "Rating is required"}), 400
    try:
        rating = float(rating)
    except (TypeError, ValueError):
        return jsonify({"error": "Rating must be a number"}), 400
    if rating < 1 or rating > 10:
        return jsonify({"error": "Rating must be between 1 and 10"}), 400

    if comment is None:
        return jsonify({"error": "Comment is required"}), 400
    if not isinstance(comment, str):
        return jsonify({"error": "Comment must be text"}), 400
    comment = comment.strip()
    if not comment:
        return jsonify({"error": "Comment cannot be empty"}), 400

    posts_collection.update_one(
        {"_id": post["_id"]},
        {"$set": {"rating": rating, "comment": comment}}
    )

    updated = find_post_by_id(post_id)
    return jsonify(format_post(updated))


# DELETE /api/posts/<post_id> (Owner or admin deletes a review)
@app.delete("/api/posts/<post_id>")
def delete_post(post_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    post = find_post_by_id(post_id)
    if not post:
        return jsonify({"error": "Review not found"}), 404

    is_owner = is_post_owner(post, session["user_id"])
    is_admin = bool(session.get("is_admin"))
    if not is_owner and not is_admin:
        return jsonify({"error": "You can only delete your own reviews"}), 403

    posts_collection.delete_one({"_id": post["_id"]})
    return jsonify({"message": "Review deleted successfully"})


# Static assets route
@app.get("/<path:filename>")
def serve_static(filename):
    if filename.endswith(".py") or filename.startswith("."):
        return "Access denied", 403
    if os.path.exists(filename):
        return send_from_directory(".", filename)
    return "Not found", 404


if __name__ == "__main__":
    print("Open: http://localhost:5000")
    app.run(debug=True)
