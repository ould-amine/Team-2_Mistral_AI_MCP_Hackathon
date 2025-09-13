"""
Application settings and configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Facebook App Configuration
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
FACEBOOK_REDIRECT_URI = os.getenv("FACEBOOK_REDIRECT_URI") or "http://localhost:8000/facebook/callback"
LE_CHAT_USER_ID = os.getenv("LE_CHAT_USER_ID")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# File paths
USER_DATA_FILE = "facebook_users.json"

# Validation
if not FACEBOOK_APP_ID or not FACEBOOK_APP_SECRET:
    raise ValueError("FACEBOOK_APP_ID, FACEBOOK_APP_SECRET must be set")
