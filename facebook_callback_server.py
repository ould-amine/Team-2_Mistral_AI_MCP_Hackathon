#!/usr/bin/env python3
"""
Simple FastAPI server to handle Facebook OAuth callbacks
Run this alongside your MCP server to handle Facebook redirects
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
import json
import os
import requests
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI(title="Facebook OAuth Callback Server")

# Facebook App Configuration
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
FACEBOOK_REDIRECT_URI = os.getenv("FACEBOOK_REDIRECT_URI") or "http://localhost:8000/facebook/callback"
LE_CHAT_USER_ID = os.getenv("LE_CHAT_USER_ID")

# File to store user tokens (same as MCP server)
USER_DATA_FILE = "facebook_users.json"

def load_user_data():
    """Load user data from JSON file"""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user_data(data):
    """Save user data to JSON file"""
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Facebook OAuth Callback Server", "status": "running"}

@app.get("/facebook/callback")
async def facebook_callback(request: Request):
    """Handle Facebook OAuth callback"""
    try:
        # Extract parameters from the request
        code = request.query_params.get("code")
        error = request.query_params.get("error")
        
        
        if error:
            return HTMLResponse(f"""
            <html>
                <head>
                    <title>Authorization Failed</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
                        .error {{ color: #d32f2f; }}
                        .container {{ background-color: #ffebee; padding: 20px; border-radius: 8px; }}
                        button {{ padding: 12px 24px; background-color: #d32f2f; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; margin-top: 15px; }}
                        .countdown {{ font-size: 18px; font-weight: bold; color: #d32f2f; }}
                    </style>
                    <script>
                        let countdown = 10;
                        function updateCountdown() {{
                            document.getElementById('countdown').textContent = countdown;
                            countdown--;
                            if (countdown < 0) {{
                                closeWindow();
                            }}
                        }}
                        
                        function closeWindow() {{
                            try {{
                                window.close();
                            }} catch(e) {{
                                alert('Please close this window manually (Ctrl+W or Cmd+W)');
                            }}
                        }}
                        
                        window.onload = function() {{
                            setInterval(updateCountdown, 1000);
                        }}
                    </script>
                </head>
                <body>
                    <div class="container">
                        <h1 class="error">❌ Authorization Failed</h1>
                        <p><strong>Error:</strong> {error}</p>
                        <p class="countdown">This window will close automatically in <span id="countdown">10</span> seconds</p>
                        <button onclick="closeWindow()">❌ Close Window</button>
                        <p style="font-size: 12px; color: #666; margin-top: 10px;">
                            Or close manually with Ctrl+W (Windows) or Cmd+W (Mac)
                        </p>
                    </div>
                </body>
            </html>
            """)
        
        if not code:
            return HTMLResponse("""
            <html>
                <head>
                    <title>Authorization Failed</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
                        .error {{ color: #d32f2f; }}
                        .container {{ background-color: #ffebee; padding: 20px; border-radius: 8px; }}
                        button {{ padding: 12px 24px; background-color: #d32f2f; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; margin-top: 15px; }}
                        .countdown {{ font-size: 18px; font-weight: bold; color: #d32f2f; }}
                    </style>
                    <script>
                        let countdown = 10;
                        function updateCountdown() {{
                            document.getElementById('countdown').textContent = countdown;
                            countdown--;
                            if (countdown < 0) {{
                                closeWindow();
                            }}
                        }}
                        
                        function closeWindow() {{
                            try {{
                                window.close();
                            }} catch(e) {{
                                alert('Please close this window manually (Ctrl+W or Cmd+W)');
                            }}
                        }}
                        
                        window.onload = function() {{
                            setInterval(updateCountdown, 1000);
                        }}
                    </script>
                </head>
                <body>
                    <div class="container">
                        <h1 class="error">❌ Authorization Failed</h1>
                        <p>Missing authorization code</p>
                        <p class="countdown">This window will close automatically in <span id="countdown">10</span> seconds</p>
                        <button onclick="closeWindow()">❌ Close Window</button>
                        <p style="font-size: 12px; color: #666; margin-top: 10px;">
                            Or close manually with Ctrl+W (Windows) or Cmd+W (Mac)
                        </p>
                    </div>
                </body>
            </html>
            """)
        
        # Exchange code for access token
        print(f"🔄 Exchanging authorization code for access token...")
        token_url = "https://graph.facebook.com/oauth/access_token"
        token_params = {
            'client_id': FACEBOOK_APP_ID,
            'client_secret': FACEBOOK_APP_SECRET,
            'redirect_uri': FACEBOOK_REDIRECT_URI,
            'code': code
        }
        
        response = requests.get(token_url, params=token_params)
        token_data = response.json()
        
        if 'access_token' not in token_data:
            error_msg = token_data.get('error', {}).get('message', 'Unknown error')
            return HTMLResponse(f"""
            <html>
                <head>
                    <title>Token Exchange Failed</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
                        .error {{ color: #d32f2f; }}
                        .container {{ background-color: #ffebee; padding: 20px; border-radius: 8px; }}
                        button {{ padding: 12px 24px; background-color: #d32f2f; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; margin-top: 15px; }}
                        .countdown {{ font-size: 18px; font-weight: bold; color: #d32f2f; }}
                    </style>
                    <script>
                        let countdown = 10;
                        function updateCountdown() {{
                            document.getElementById('countdown').textContent = countdown;
                            countdown--;
                            if (countdown < 0) {{
                                closeWindow();
                            }}
                        }}
                        
                        function closeWindow() {{
                            try {{
                                window.close();
                            }} catch(e) {{
                                alert('Please close this window manually (Ctrl+W or Cmd+W)');
                            }}
                        }}
                        
                        window.onload = function() {{
                            setInterval(updateCountdown, 1000);
                        }}
                    </script>
                </head>
                <body>
                    <div class="container">
                        <h1 class="error">❌ Token Exchange Failed</h1>
                        <p><strong>Error:</strong> {error_msg}</p>
                        <p class="countdown">This window will close automatically in <span id="countdown">10</span> seconds</p>
                        <button onclick="closeWindow()">❌ Close Window</button>
                        <p style="font-size: 12px; color: #666; margin-top: 10px;">
                            Or close manually with Ctrl+W (Windows) or Cmd+W (Mac)
                        </p>
                    </div>
                </body>
            </html>
            """)
        
        access_token = token_data['access_token']
        
        # Get user's pages
        pages_url = f"https://graph.facebook.com/me/accounts?access_token={access_token}"
        pages_response = requests.get(pages_url)
        pages_data = pages_response.json()
        
        if 'data' not in pages_data:
            error_msg = pages_data.get('error', {}).get('message', 'Unknown error')
            return HTMLResponse(f"""
            <html>
                <head>
                    <title>Pages Access Failed</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
                        .error {{ color: #d32f2f; }}
                        .container {{ background-color: #ffebee; padding: 20px; border-radius: 8px; }}
                        button {{ padding: 12px 24px; background-color: #d32f2f; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; margin-top: 15px; }}
                        .countdown {{ font-size: 18px; font-weight: bold; color: #d32f2f; }}
                    </style>
                    <script>
                        let countdown = 10;
                        function updateCountdown() {{
                            document.getElementById('countdown').textContent = countdown;
                            countdown--;
                            if (countdown < 0) {{
                                closeWindow();
                            }}
                        }}
                        
                        function closeWindow() {{
                            try {{
                                window.close();
                            }} catch(e) {{
                                alert('Please close this window manually (Ctrl+W or Cmd+W)');
                            }}
                        }}
                        
                        window.onload = function() {{
                            setInterval(updateCountdown, 1000);
                        }}
                    </script>
                </head>
                <body>
                    <div class="container">
                        <h1 class="error">❌ Failed to Access Pages</h1>
                        <p><strong>Error:</strong> {error_msg}</p>
                        <p class="countdown">This window will close automatically in <span id="countdown">10</span> seconds</p>
                        <button onclick="closeWindow()">❌ Close Window</button>
                        <p style="font-size: 12px; color: #666; margin-top: 10px;">
                            Or close manually with Ctrl+W (Windows) or Cmd+W (Mac)
                        </p>
                    </div>
                </body>
            </html>
            """)
        
        # Save user data
        user_data = load_user_data()
        facebook_user_id = LE_CHAT_USER_ID
        user_data[facebook_user_id] = {
            'facebook_user_id': facebook_user_id,
            'access_token': access_token,
            'pages': pages_data['data']
        }
        save_user_data(user_data)
        
        # Create pages list for display
        pages_list = ""
        for page in pages_data['data']:
            pages_list += f"<li><strong>{page['name']}</strong> (ID: {page['id']})</li>"
        
        return HTMLResponse(f"""
        <html>
            <head>
                <title>Facebook Authorization Complete</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                    .success {{ color: #4CAF50; }}
                    .container {{ text-align: center; }}
                    ul {{ text-align: left; }}
                    .countdown {{ font-size: 18px; font-weight: bold; color: #FF6B35; }}
                </style>
                <script>
                    let countdown = 10;
                    function updateCountdown() {{
                        document.getElementById('countdown').textContent = countdown;
                        countdown--;
                        if (countdown < 0) {{
                            closeWindow();
                        }}
                    }}
                    
                    function closeWindow() {{
                        try {{
                            window.close();
                        }} catch(e) {{
                            alert('Please close this window manually (Ctrl+W or Cmd+W)');
                        }}
                    }}
                    
                    window.onload = function() {{
                        setInterval(updateCountdown, 1000);
                    }}
                </script>
            </head>
            <body>
                <div class="container">
                    <h1 class="success">✅ Facebook Authorization Complete!</h1>
                    <p>Successfully connected your Facebook account!</p>
                    <h3>Available Pages:</h3>
                    <ul>{pages_list}</ul>
                    <p><strong>User ID:</strong> {facebook_user_id}</p>
                    
                    <div style="margin-top: 30px; padding: 20px; background-color: #f0f8ff; border-radius: 8px;">
                        <p style="font-size: 16px; color: #333; margin-bottom: 15px;">
                            ✅ <strong>Authorization Complete!</strong><br>
                            You can now use the Facebook posting tools in your MCP client!
                        </p>
                        <p class="countdown">This window will close automatically in <span id="countdown">10</span> seconds</p>
                        <button onclick="closeWindow()" style="padding: 12px 24px; background-color: #4CAF50; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold;">
                            ✅ Close Window
                        </button>
                        <p style="font-size: 12px; color: #666; margin-top: 10px;">
                            Or close manually with Ctrl+W (Windows) or Cmd+W (Mac)
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
        <html>
            <head>
                <title>Error</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
                    .error {{ color: #d32f2f; }}
                    .container {{ background-color: #ffebee; padding: 20px; border-radius: 8px; }}
                    button {{ padding: 12px 24px; background-color: #d32f2f; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; margin-top: 15px; }}
                    .countdown {{ font-size: 18px; font-weight: bold; color: #d32f2f; }}
                </style>
                <script>
                    let countdown = 10;
                    function updateCountdown() {{
                        document.getElementById('countdown').textContent = countdown;
                        countdown--;
                        if (countdown < 0) {{
                            closeWindow();
                        }}
                    }}
                    
                    function closeWindow() {{
                        try {{
                            window.close();
                        }} catch(e) {{
                            alert('Please close this window manually (Ctrl+W or Cmd+W)');
                        }}
                    }}
                    
                    window.onload = function() {{
                        setInterval(updateCountdown, 1000);
                    }}
                </script>
            </head>
            <body>
                <div class="container">
                    <h1 class="error">❌ Error</h1>
                    <p><strong>Error:</strong> {str(e)}</p>
                    <p class="countdown">This window will close automatically in <span id="countdown">10</span> seconds</p>
                    <button onclick="closeWindow()">❌ Close Window</button>
                    <p style="font-size: 12px; color: #666; margin-top: 10px;">
                        Or close manually with Ctrl+W (Windows) or Cmd+W (Mac)
                    </p>
                </div>
            </body>
        </html>
        """)

if __name__ == "__main__":
    port = int(os.getenv("CALLBACK_PORT", "8000"))
    print(f"🚀 Starting Facebook OAuth Callback Server on port {port}")
    print(f"📍 Callback URL: http://localhost:{port}/facebook/callback")
    print(f"📊 Health check: http://localhost:{port}/")
    print("🛑 Press Ctrl+C to stop")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
