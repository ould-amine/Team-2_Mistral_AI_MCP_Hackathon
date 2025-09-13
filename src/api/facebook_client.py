"""
Facebook Graph API client
"""
import requests
from typing import Dict, Any, List
from ..config.settings import FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, FACEBOOK_REDIRECT_URI, LE_CHAT_USER_ID
from ..utils.data_manager import load_user_data, save_user_data


class FacebookClient:
    """Facebook Graph API client"""
    
    def __init__(self):
        self.app_id = FACEBOOK_APP_ID
        self.app_secret = FACEBOOK_APP_SECRET
        self.redirect_uri = FACEBOOK_REDIRECT_URI
        self.user_id = LE_CHAT_USER_ID
    
    def get_auth_url(self) -> str:
        """Generate Facebook OAuth URL for page connection"""
        import urllib.parse
        
        params = {
            'client_id': self.app_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'email,public_profile,business_management,pages_manage_posts,pages_read_engagement,pages_show_list,pages_read_user_content,read_insights',
            'response_type': 'code',
            'state': self.user_id
        }
        base_url = "https://www.facebook.com/dialog/oauth"
        auth_url = f"{base_url}?{urllib.parse.urlencode(params)}"
        return f"🔗 Visit this URL to connect your Facebook page:\n{auth_url}\n\n📌 User ID: {self.user_id}"
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        token_url = "https://graph.facebook.com/oauth/access_token"
        token_params = {
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            'redirect_uri': self.redirect_uri,
            'code': code
        }
        
        response = requests.get(token_url, params=token_params)
        return response.json()
    
    def get_user_pages(self, access_token: str) -> Dict[str, Any]:
        """Get user's Facebook pages"""
        pages_url = "https://graph.facebook.com/me/accounts"
        pages_params = {'access_token': access_token}
        
        response = requests.get(pages_url, params=pages_params)
        return response.json()
    
    def save_user_connection(self, access_token: str, pages: List[Dict[str, Any]]) -> None:
        """Save user connection data"""
        user_data = load_user_data()
        user_data[self.user_id] = {
            'access_token': access_token,
            'pages': pages
        }
        save_user_data(user_data)
    
    def get_user_data(self) -> Dict[str, Any]:
        """Get user data"""
        return load_user_data()
    
    def is_connected(self) -> bool:
        """Check if user is connected"""
        user_data = self.get_user_data()
        return self.user_id in user_data and 'pages' in user_data[self.user_id]
    
    def get_first_page(self) -> Dict[str, Any]:
        """Get first available page"""
        user_data = self.get_user_data()
        if self.user_id in user_data:
            pages = user_data[self.user_id].get('pages', [])
            if pages:
                return pages[0]
        return None
