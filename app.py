from flask import Flask, request, render_template_string
import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret")

# MongoDB connection
mongo_url = os.getenv("MONGO_URL") or "mongodb://localhost:27017/"
client = MongoClient(mongo_url)
db = client["atlantisfreshrg"]
verifications = db["roblox_verifications"]

@app.route("/")
def index():
    return "Roblox Discord Verification - Railway redirect handler online!"

@app.route("/roblox/callback")
def roblox_callback():
    # Roblox OAuth will provide ?code=...&state=...
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")
    
    if error:
        return render_template_string("""
            <html>
            <head><title>Verification Error</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>Verification Error</h1>
                <p>An error occurred during verification: {{ error }}</p>
                <p>Please try again.</p>
            </body>
            </html>
        """, error=error), 400
    
    if not code:
        return render_template_string("""
            <html>
            <head><title>Verification Error</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>Verification Error</h1>
                <p>No authorization code provided by Roblox.</p>
                <p>Please try again.</p>
            </body>
            </html>
        """), 400

    # Log the verification attempt to MongoDB
    verification_data = {
        "code": code,
        "state": state,
        "ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent", ""),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        verifications.insert_one(verification_data)
    except Exception as e:
        print(f"Error inserting verification data: {e}")

    return render_template_string("""
        <html>
        <head>
            <title>Verification Complete</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 50px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0;
                }
                .container {
                    background: rgba(255, 255, 255, 0.1);
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                    backdrop-filter: blur(4px);
                }
                h1 {
                    margin-top: 0;
                    font-size: 2.5em;
                }
                p {
                    font-size: 1.2em;
                    line-height: 1.6;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✅ Verification Complete</h1>
                <p>Your account has been successfully verified with Roblox!</p>
                <p>You can now close this window and return to Discord.</p>
            </div>
        </body>
        </html>
    """)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
