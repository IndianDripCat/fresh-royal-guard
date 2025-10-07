from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
import uvicorn
import os
import aiohttp
from urllib.parse import urlencode, quote_plus
from datetime import datetime
import motor.motor_asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
ROBLOX_CLIENT_ID = os.getenv('ROBLOX_CLIENT_ID')
ROBLOX_CLIENT_SECRET = os.getenv('ROBLOX_CLIENT_SECRET')
GITHUB_PAGES_URL = "https://yourusername.github.io/verification.html"  # Update this to your GitHub Pages URL
REDIRECT_URI = "http://localhost:5000/auth/roblox/callback"

app = FastAPI()
mongodb = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017'))
db = mongodb['atlantisfreshrg']

@app.get("/auth/roblox")
async def start_auth(state: str):
    """Start the OAuth flow with Roblox"""
    params = {
        'client_id': ROBLOX_CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'profile openid',
        'state': state
    }
    auth_url = f"https://authorize.roblox.com/?{urlencode(params)}"
    return RedirectResponse(auth_url)

@app.get("/auth/roblox/callback")
async def auth_callback(code: str, state: str):
    """Handle the OAuth callback from Roblox"""
    if not code:
        return RedirectResponse(f"{GITHUB_PAGES_URL}?status=error&message=no_code")
    
    try:
        # Exchange code for access token
        token_url = "https://apis.roblox.com/oauth/v1/token"
        data = {
            'client_id': ROBLOX_CLIENT_ID,
            'client_secret': ROBLOX_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI
        }
        
        async with aiohttp.ClientSession() as session:
            # Get access token
            async with session.post(token_url, data=data) as response:
                token_data = await response.json()
                
                if 'access_token' not in token_data:
                    return RedirectResponse(f"{GITHUB_PAGES_URL}?status=error&message=token_failed")
                
                # Get user info
                headers = {"Authorization": f"Bearer {token_data['access_token']}"}
                async with session.get("https://apis.roblox.com/oauth/v1/userinfo", headers=headers) as user_response:
                    user_data = await user_response.json()
                    roblox_id = user_data.get('sub')
                    username = user_data.get('preferred_username')
                    
                    if not roblox_id:
                        return RedirectResponse(f"{GITHUB_PAGES_URL}?status=error&message=no_user_id")
                    
                    # Store in MongoDB
                    await db.verified_users.update_one(
                        {"discord_id": state},
                        {"$set": {
                            "roblox_id": roblox_id,
                            "username": username,
                            "verified_at": datetime.utcnow(),
                            "last_updated": datetime.utcnow()
                        }},
                        upsert=True
                    )
                    
                    # Redirect to success page with username in URL
                    safe_username = quote_plus(username)
                    return RedirectResponse(f"{GITHUB_PAGES_URL}?status=success&username={safe_username}")
    
    except Exception as e:
        print(f"Error during OAuth callback: {str(e)}")
        return RedirectResponse(f"{GITHUB_PAGES_URL}?status=error&message=server_error")

if __name__ == "__main__":
    print("Starting auth server on http://localhost:5000")
    uvicorn.run(app, host="0.0.0.0", port=5000)
