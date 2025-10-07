import os
import motor.motor_asyncio
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Configuration
TARGET_USER_ID = 1109257320413798561  # The user ID to make admin
ADMIN_LEVEL = 100                    # The admin level to set
GUILD_ID = 1347138353820340224       # The guild ID where the admin level should be set

async def set_admin():
    # Connect to MongoDB
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
    db = client['atlantisfreshrg']
    admins = db['admins']
    
    # Prepare the query with GuildID
    query = {
        "UserID": TARGET_USER_ID,
        "GuildID": GUILD_ID
    }
    
    # Check if user already has an admin level
    existing = await admins.find_one(query)
    
    # Prepare the update data
    update_data = {
        "$set": {
            "UserID": TARGET_USER_ID,
            "GuildID": GUILD_ID,
            "AdminLevel": ADMIN_LEVEL
        }
    }
    
    # Update or insert the admin record
    result = await admins.update_one(
        query,
        update_data,
        upsert=True
    )
    
    if result.upserted_id:
        print(f"✅ Successfully set admin level {ADMIN_LEVEL} for user {TARGET_USER_ID} in guild {GUILD_ID}")
    elif result.modified_count > 0:
        print(f"✅ Successfully updated admin level to {ADMIN_LEVEL} for user {TARGET_USER_ID} in guild {GUILD_ID}")
    else:
        print("ℹ️ No changes were made. The user already has this admin level in this guild.")
    
    # Close the connection
    client.close()

if __name__ == "__main__":
    # Check if MONGODB_URI is set in .env
    if not os.getenv('MONGODB_URI'):
        print("❌ Error: MONGODB_URI not found in .env file")
    else:
        print(f"Setting admin level {ADMIN_LEVEL} for user {TARGET_USER_ID} in guild {GUILD_ID}...")
        asyncio.run(set_admin())
