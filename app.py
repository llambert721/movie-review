from flask import Flask, request, jsonify, send_from_directory, session, redirect
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os
import re
import urllib.parse
from datetime import datetime, timezone

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

    author = None
    author_id = post.get("user_id")
    if author_id is not None and ObjectId.is_valid(str(author_id)):
        try:
            author = users_collection.find_one({"_id": ObjectId(str(author_id))})
        except Exception:
            pass

    return {
        "id": str(post["_id"]),
        "user_id": str(post.get("user_id", "")),
        "username": author.get("username", "") if author else "",
        "display_name": (author.get("display_name") or author.get("username", "")) if author else "Unknown User",
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


# Helper: find movie by id
def find_movie_by_id(movie_id):
    if not movie_id or not ObjectId.is_valid(movie_id):
        return None
    try:
        return movies_collection.find_one({"_id": ObjectId(movie_id)})
    except Exception:
        return None


# Helper: query matching posts for a movie (movie_id may be stored as str or ObjectId)
def movie_posts_query(movie_id):
    clauses = [{"movie_id": str(movie_id)}]
    if ObjectId.is_valid(str(movie_id)):
        clauses.append({"movie_id": ObjectId(str(movie_id))})
    return {"$or": clauses}


# Helper: average rating and review count for every movie -> {movie_id: (avg, count)}
def get_rating_stats():
    totals = {}
    for p in posts_collection.find({}, {"movie_id": 1, "rating": 1}):
        mid = str(p.get("movie_id", ""))
        try:
            rating = float(p.get("rating", 0))
        except (TypeError, ValueError):
            continue
        total, count = totals.get(mid, (0.0, 0))
        totals[mid] = (total + rating, count + 1)
    return {mid: (round(t / c, 1), c) for mid, (t, c) in totals.items()}


def format_movie(movie, stats):
    mid = str(movie["_id"])
    avg, count = stats.get(mid, (None, 0))
    return {
        "id": mid,
        "title": movie.get("title", ""),
        "release_date": movie.get("release_date", ""),
        "genre": movie.get("genre", ""),
        "description": movie.get("description", ""),
        "avg_rating": avg,
        "review_count": count
    }


# Helper: validate movie payload -> (clean_dict, error_message)
def validate_movie_payload(data):
    title = (data.get("title") or "").strip()
    genre = (data.get("genre") or "").strip()
    description = (data.get("description") or "").strip()
    release_date = (data.get("release_date") or "").strip()

    if not title:
        return None, "Title is required"
    if not release_date:
        return None, "Release date is required"
    try:
        datetime.strptime(release_date, "%Y-%m-%d")
    except ValueError:
        return None, "Release date must be in YYYY-MM-DD format"
    if not genre:
        return None, "Genre is required"
    if not description:
        return None, "Description is required"

    return {
        "title": title,
        "release_date": release_date,
        "genre": genre,
        "description": description
    }, None


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


# ==========================================
# MOVIE API ENDPOINTS
# ==========================================

# GET /api/movies?sort=date|rating|genre|title&order=asc|desc&genre=Drama
@app.get("/api/movies")
def list_movies():
    sort_key = request.args.get("sort", "date")
    order = request.args.get("order", "desc")
    genre_filter = request.args.get("genre", "").strip()

    query = {}
    if genre_filter:
        query["genre"] = {"$regex": f"^{re.escape(genre_filter)}$", "$options": "i"}

    stats = get_rating_stats()
    movies = [format_movie(m, stats) for m in movies_collection.find(query)]

    reverse = order != "asc"
    if sort_key == "rating":
        movies.sort(key=lambda m: (m["avg_rating"] if m["avg_rating"] is not None else -1,
                                   m["title"].lower()), reverse=reverse)
    elif sort_key == "genre":
        movies.sort(key=lambda m: (m["genre"].lower(), m["title"].lower()), reverse=reverse)
    elif sort_key == "title":
        movies.sort(key=lambda m: m["title"].lower(), reverse=reverse)
    else:
        movies.sort(key=lambda m: (m["release_date"], m["title"].lower()), reverse=reverse)

    return jsonify(movies)


# GET /api/genres
@app.get("/api/genres")
def list_genres():
    genres = {g.strip() for g in movies_collection.distinct("genre") if g and g.strip()}
    return jsonify(sorted(genres, key=str.lower))


# GET /api/movies/<id>
@app.get("/api/movies/<movie_id>")
def get_movie(movie_id):
    movie = find_movie_by_id(movie_id)
    if not movie:
        return jsonify({"error": "Movie not found"}), 404
    return jsonify(format_movie(movie, get_rating_stats()))


# GET /api/movies/<id>/posts
@app.get("/api/movies/<movie_id>/posts")
def get_movie_posts(movie_id):
    movie = find_movie_by_id(movie_id)
    if not movie:
        return jsonify({"error": "Movie not found"}), 404
    posts = posts_collection.find(movie_posts_query(movie_id)).sort("_id", -1)
    return jsonify([format_post(p) for p in posts])


# POST /api/movies (admin adds a movie)
@app.post("/api/movies")
def create_movie():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    if not session.get("is_admin"):
        return jsonify({"error": "Administrator privilege required"}), 403

    clean, error = validate_movie_payload(request.get_json() or {})
    if error:
        return jsonify({"error": error}), 400

    result = movies_collection.insert_one(clean)
    movie = movies_collection.find_one({"_id": result.inserted_id})
    return jsonify(format_movie(movie, {})), 201


# PUT /api/movies/<id> (admin edits a movie)
@app.put("/api/movies/<movie_id>")
def update_movie(movie_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    if not session.get("is_admin"):
        return jsonify({"error": "Administrator privilege required"}), 403

    movie = find_movie_by_id(movie_id)
    if not movie:
        return jsonify({"error": "Movie not found"}), 404

    clean, error = validate_movie_payload(request.get_json() or {})
    if error:
        return jsonify({"error": error}), 400

    movies_collection.update_one({"_id": movie["_id"]}, {"$set": clean})
    updated = movies_collection.find_one({"_id": movie["_id"]})
    return jsonify(format_movie(updated, get_rating_stats()))


# DELETE /api/movies/<id> (admin deletes a movie and its reviews)
@app.delete("/api/movies/<movie_id>")
def delete_movie(movie_id):
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    if not session.get("is_admin"):
        return jsonify({"error": "Administrator privilege required"}), 403

    movie = find_movie_by_id(movie_id)
    if not movie:
        return jsonify({"error": "Movie not found"}), 404

    posts_collection.delete_many(movie_posts_query(movie_id))
    movies_collection.delete_one({"_id": movie["_id"]})
    return jsonify({"message": "Movie deleted successfully"})


# ==========================================
# FEED & CREATE POST API ENDPOINTS
# ==========================================

# GET /api/posts (community feed, newest first)
@app.get("/api/posts")
def get_feed():
    try:
        limit = min(max(int(request.args.get("limit", 100)), 1), 200)
    except ValueError:
        limit = 100
    posts = posts_collection.find({}).sort("_id", -1).limit(limit)
    return jsonify([format_post(p) for p in posts])


# POST /api/posts (logged-in user reviews a movie)
@app.post("/api/posts")
def create_post():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json() or {}
    movie = find_movie_by_id(str(data.get("movie_id", "")))
    if not movie:
        return jsonify({"error": "Please choose a valid movie"}), 400

    rating = data.get("rating")
    if rating is None or rating == "":
        return jsonify({"error": "Rating is required"}), 400
    try:
        rating = float(rating)
    except (TypeError, ValueError):
        return jsonify({"error": "Rating must be a number"}), 400
    if rating < 1 or rating > 10:
        return jsonify({"error": "Rating must be between 1 and 10"}), 400

    comment = data.get("comment")
    if not isinstance(comment, str) or not comment.strip():
        return jsonify({"error": "Comment cannot be empty"}), 400

    new_post = {
        "user_id": session["user_id"],
        "movie_id": str(movie["_id"]),
        "movie_title": movie.get("title", ""),
        "rating": rating,
        "comment": comment.strip(),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    }
    result = posts_collection.insert_one(new_post)
    created = posts_collection.find_one({"_id": result.inserted_id})
    return jsonify(format_post(created)), 201


# Static assets route (only front-end file types are served)
ALLOWED_STATIC_EXTENSIONS = {".html", ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp"}

@app.get("/<path:filename>")
def serve_static(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_STATIC_EXTENSIONS:
        return "Not found", 404
    if os.path.isfile(filename):
        return send_from_directory(".", filename)
    return "Not found", 404


if __name__ == "__main__":
    print("Open: http://localhost:5000")
    app.run(debug=True)
