from fastapi import FastAPI, Request
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
# This is where Roblox will redirect back to after authentication
ROBLOX_REDIRECT_URI = "https://your-render-app-url.onrender.com/auth/roblox/callback"  # Update with your server URL
# This is where we'll redirect after verification is complete
GITHUB_PAGES_URL = "https://indiandripcat.github.io/fresh-royal-guard/"

app = FastAPI()

# Set up MongoDB
mongodb = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017'))
db = mongodb['atlantisfreshrg']

@app.get("/")
async def root():
    """Root endpoint - redirect to GitHub Pages"""
    return RedirectResponse(url=GITHUB_PAGES_URL, status_code=302)

@app.get("/auth/roblox")
async def start_auth(state: str):
    """Start the OAuth flow with Roblox"""
    params = {
        'client_id': ROBLOX_CLIENT_ID,
        'redirect_uri': ROBLOX_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid profile:read',
        'state': state
    }
    auth_url = f"https://authorize.roblox.com/?{urlencode(params)}"
    return RedirectResponse(auth_url)

@app.get("/auth/roblox/callback")
async def auth_callback(code: str, state: str):
    """Handle the OAuth callback from Roblox"""
    try:
        # Exchange the authorization code for an access token
        async with aiohttp.ClientSession() as session:
            # Exchange code for token
            token_url = "https://apis.roblox.com/oauth/v1/token"
            data = {
                'client_id': ROBLOX_CLIENT_ID,
                'client_secret': ROBLOX_CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': ROBLOX_REDIRECT_URI
            
            async with session.post(token_url, data=data) as response:
                if response.status != 200:
                    error = await response.text()
                    print(f"Token exchange failed: {error}")
                    return RedirectResponse(f"{GITHUB_PAGES_URL}?error=auth_failed&message={quote_plus('Failed to exchange code for token')}")
                
                token_data = await response.json()
                access_token = token_data.get('access_token')
                
                if not access_token:
                    return RedirectResponse(f"{GITHUB_PAGES_URL}?error=no_token&message={quote_plus('No access token received')}")
                
                # Get user info
                user_info_url = "https://apis.roblox.com/oauth/v1/userinfo"
                headers = {"Authorization": f"Bearer {access_token}"}
                
                async with session.get(user_info_url, headers=headers) as user_response:
                    if user_response.status != 200:
                        return RedirectResponse(f"{GITHUB_PAGES_URL}?error=user_info_failed&message={quote_plus('Failed to fetch user info')}")
                    
                    user_data = await user_response.json()
                    roblox_id = user_data.get('sub')
                    username = user_data.get('nickname')
                    
                    if not roblox_id or not username:
                        return RedirectResponse(f"{GITHUB_PAGES_URL}?error=invalid_user_data&message={quote_plus('Invalid user data received')}")
                    
                    # Store in MongoDB
                    await db.verified_users.update_one(
                        {"discord_id": state},
                        {"$set": {"roblox_id": roblox_id, "username": username, "verified_at": datetime.utcnow()}},
                        upsert=True
                    )
                    
                    # Redirect to GitHub Pages
                    return RedirectResponse(f"{GITHUB_PAGES_URL}?success=true&username={quote_plus(username)}")
    
    except Exception as e:
        print(f"Error during OAuth callback: {str(e)}")
        return RedirectResponse(f"{GITHUB_PAGES_URL}?error=server_error&message={quote_plus(str(e))}")
            # Replace the error div with our error message
            html_content = html_content.replace('<div id="error" style="display: none;">', 
                                             error_html + '<div id="error" style="display: none;">')
            
            return HTMLResponse(content=html_content, status_code=200)
        except Exception as e2:
            return HTMLResponse(content=f"<h1>Verification Error</h1><p>An error occurred during verification: {str(e2)}</p>", status_code=500)

if __name__ == "__main__":
    print("Starting auth server on http://localhost:5000")
    uvicorn.run(app, host="0.0.0.0", port=5000)
