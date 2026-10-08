import os
import urllib.parse
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

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

MONGO_URI = get_mongo_uri()
client = MongoClient(MONGO_URI)
db = client["MovieDB"]
users = db["User"]

users.delete_many({
    "username": {"$in": ["user", "admin"]}
})

users.insert_many([
    {
        "username": "user",
        "display_name": "User",
        "password_hash": generate_password_hash("User123!"),
        "is_admin": False
    },
    {
        "username": "admin",
        "display_name": "Admin User",
        "password_hash": generate_password_hash("Admin123!"),
        "is_admin": True
    }
])

print("Demo users created.")
print("Database: MovieDB")
print("Collection: User")
