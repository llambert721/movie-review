"""Adds a few sample movies to MovieDB.Movie (skips titles that already exist)."""
import os
import urllib.parse
from pymongo import MongoClient


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
    if os.environ.get("MONGO_URI", "").strip():
        return os.environ["MONGO_URI"].strip()
    user = os.environ.get("MONGO_USER", "").strip()
    pwd = os.environ.get("MONGO_PASSWORD", "").strip()
    if user and pwd:
        return (f"mongodb+srv://{urllib.parse.quote_plus(user)}:{urllib.parse.quote_plus(pwd)}"
                "@cluster0.sdneqlg.mongodb.net/?appName=Cluster0")
    raise ValueError("Missing MongoDB credentials! Define MONGO_USER and MONGO_PASSWORD (or MONGO_URI) in .env.")


movies = MongoClient(get_mongo_uri())["MovieDB"]["Movie"]

SAMPLE_MOVIES = [
    {"title": "The Shawshank Redemption", "release_date": "1994-09-23", "genre": "Drama",
     "description": "Two imprisoned men bond over several years, finding solace and eventual redemption through acts of common decency."},
    {"title": "The Dark Knight", "release_date": "2008-07-18", "genre": "Action",
     "description": "Batman faces the Joker, a criminal mastermind who pushes Gotham City into chaos."},
    {"title": "Inception", "release_date": "2010-07-16", "genre": "Sci-Fi",
     "description": "A thief who steals secrets through dream-sharing technology is given the task of planting an idea in a target's mind."},
    {"title": "Spirited Away", "release_date": "2001-07-20", "genre": "Animation",
     "description": "A young girl wanders into a world of spirits and must work in a bathhouse to free her parents."},
    {"title": "Superbad", "release_date": "2007-08-17", "genre": "Comedy",
     "description": "Two high school friends try to make the most of their last days before graduation."},
]

added = 0
for movie in SAMPLE_MOVIES:
    if not movies.find_one({"title": movie["title"]}):
        movies.insert_one(movie)
        added += 1

print(f"Added {added} sample movie(s).")
