"""
MCP Server Template with Facebook Integration
"""

from mcp.server.fastmcp import FastMCP
from pydantic import Field
import json
import os
import urllib.parse
import requests
from typing import Dict, Any
from dotenv import load_dotenv
import mcp.types as types


load_dotenv()
mcp = FastMCP("Facebook MCP Server", port=3000, stateless_http=True, debug=True)

# Facebook App Configuration
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
FACEBOOK_REDIRECT_URI = os.getenv("FACEBOOK_REDIRECT_URI") or "http://localhost:8000/facebook/callback"
LE_CHAT_USER_ID=os.getenv("LE_CHAT_USER_ID")

# make sure to add the app id and secret to the .env file and check the .env file
if not FACEBOOK_APP_ID or not FACEBOOK_APP_SECRET:
    raise ValueError("FACEBOOK_APP_ID, FACEBOOK_APP_SECRET must be set")

# File to store user tokens
USER_DATA_FILE = "facebook_users.json"

def load_user_data() -> Dict[str, Any]:
    """Load user data from JSON file"""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user_data(data: Dict[str, Any]):
    """Save user data to JSON file"""
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


@mcp.tool(
    title="Facebook Auth URL",
    description="Generate Facebook OAuth URL for page connection",
)
def get_facebook_auth_url() -> str:
    """Generate Facebook OAuth URL for connecting pages"""
    # Use hardcoded user ID
    facebook_user_id = LE_CHAT_USER_ID
    
    params = {
        'client_id': FACEBOOK_APP_ID,
        'redirect_uri': FACEBOOK_REDIRECT_URI,
        'scope': 'pages_manage_posts,pages_read_engagement,pages_show_list',
        'response_type': 'code',
        'state': facebook_user_id  # Use hardcoded user_id as state parameter
    }
    
    base_url = "https://www.facebook.com/dialog/oauth"
    auth_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    return f"🔗 Visit this URL to connect your Facebook page:\n{auth_url}\n\n📌 User ID: {facebook_user_id}"


@mcp.tool(
    title="Check Facebook Connection",
    description="Check if Facebook page is connected and ready for posting",
)
def check_facebook_connection() -> str:
    """Check if Facebook account is connected and ready for posting"""
    try:
        # Use hardcoded user ID
        facebook_user_id = LE_CHAT_USER_ID
        
        # Load user data
        user_data = load_user_data()
        
        if facebook_user_id not in user_data:
            return "❌ Facebook not connected. Use 'get_facebook_auth_url()' to get the authorization URL."
        
        # Get user's pages
        pages = user_data[facebook_user_id].get('pages', [])
        
        if not pages:
            return "❌ No Facebook pages found. Use 'get_facebook_auth_url()' to connect your page."
        
        # Get first page info
        first_page = pages[0]
        page_name = first_page['name']
        
        return f"✅ Facebook connected! Ready to post to '{page_name}'"
        
    except Exception as e:
        return f"❌ Error checking connection: {str(e)}"


@mcp.tool(
    title="Post to Facebook Page",
    description="Post text content and/or image to Facebook page (uses first available page)",
)
def post_to_facebook_page(
    post_text: str = Field(description="Message content to post to Facebook page"),
    image_url: str = Field(description="URL of the image to post (optional)", default="")
) -> str:
    """Post text and/or image to Facebook page using hardcoded user"""
    try:
        print(f"🔄 Posting to Facebook page: {post_text} {image_url}")
        # Use hardcoded user ID
        facebook_user_id = LE_CHAT_USER_ID
        
        # Load user data
        user_data = load_user_data()
        
        if facebook_user_id not in user_data:
            return "❌ Facebook account not connected. Please visit the auth URL first to connect your Facebook page."
        
        # Get user's pages
        pages = user_data[facebook_user_id].get('pages', [])
        
        if not pages:
            return "❌ No Facebook pages found. Make sure you have admin access to at least one Facebook page."
        
        # Use the first available page
        first_page = pages[0]
        page_token = first_page['access_token']
        page_name = first_page['name']
        page_id = first_page['id']
        
        print(f"📝 Posting to Facebook page: {page_name} (ID: {page_id})")
        if image_url:
            print(f"🖼️ Image URL: {image_url}")
        
        # Prepare post data
        post_url = f"https://graph.facebook.com/{page_id}/photos" if image_url else f"https://graph.facebook.com/{page_id}/feed"
        post_data = {
            'access_token': page_token
        }
        
        # Add message if provided
        if post_text:
            post_data['message'] = post_text
        
        # Add image if provided
        if image_url:
            post_data['url'] = image_url  # Facebook will fetch the image from URL
            post_type = "photo with text" if post_text else "photo"
        else:
            post_type = "text post"
        
        response = requests.post(post_url, data=post_data)
        result = response.json()
        
        if 'id' in result:
            post_id = result['id']
            # Create direct link to the Facebook post
            facebook_post_url = f"https://www.facebook.com/{post_id}"
            
            success_msg = f"✅ Successfully posted {post_type} to '{page_name}'!\n"
            success_msg += f"🔗 View post: {facebook_post_url}\n"
            success_msg += f"📱 Post ID: {post_id}"
            
            if post_text:
                success_msg += f"\n📝 Message: {post_text}"
            if image_url:
                success_msg += f"\n🖼️ Image: {image_url}"
                
            return success_msg
        else:
            error_msg = result.get('error', {}).get('message', 'Unknown error')
            return f"❌ Error posting to Facebook: {error_msg}"
            
    except Exception as e:
        return f"❌ Error posting to Facebook: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
