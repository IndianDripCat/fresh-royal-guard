import os
from pymongo import MongoClient

# You may want to load .env if MONGO_URL is in there
from dotenv import load_dotenv
load_dotenv()

MONGO_URL = os.getenv("MONGO_URL") or "mongodb://localhost:27017/"
ADMIN_USER_ID = 1109257320413798561  # user id to promote
GUILD_ID = 1347138353820340224      # target guild
ADMIN_LEVEL = 100

client = MongoClient(MONGO_URL)
db = client["atlantisfreshrg"]
admins_collection = db["admins"]

existing = admins_collection.find_one({"guild_id": GUILD_ID, "user_or_role_id": ADMIN_USER_ID})

if existing:
    print(f"User {ADMIN_USER_ID} already has admin level {existing['AdminLevel']} in guild {GUILD_ID}.")
else:
    admins_collection.insert_one({
        "guild_id": GUILD_ID,
        "user_or_role_id": ADMIN_USER_ID,
        "user_or_role_name": f"<@{ADMIN_USER_ID}>",
        "AdminLevel": ADMIN_LEVEL
    })
    print(f"Set user {ADMIN_USER_ID} to admin level {ADMIN_LEVEL} in guild {GUILD_ID}.")
