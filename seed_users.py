from pymongo import MongoClient
from werkzeug.security import generate_password_hash

client = MongoClient("mongodb://localhost:27017/")
db = client["coffee_auth"]
users = db["users"]

users.delete_many({
    "email": {"$in": ["user@coffee.local", "admin@coffee.local"]}
})

users.insert_many([
    {
        "name": "Student User",
        "email": "user@coffee.local",
        "password_hash": generate_password_hash("User123!"),
        "role": "user",
        "active": True
    },
    {
        "name": "Coffee Administrator",
        "email": "admin@coffee.local",
        "password_hash": generate_password_hash("Admin123!"),
        "role": "admin",
        "active": True
    }
])

print("Demo users created.")
print("Database: coffee_auth")
print("Collection: users")
