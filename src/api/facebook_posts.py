"""
Facebook posts management
"""
import requests
from typing import Dict, Any, List
from .facebook_client import FacebookClient


class FacebookPosts:
    """Facebook posts management"""
    
    def __init__(self, client: FacebookClient):
        self.client = client
    
    def post_text(self, post_text: str, page_token: str, page_id: str) -> Dict[str, Any]:
        """Post text content to Facebook page"""
        post_data = {
            'message': post_text,
            'access_token': page_token
        }
        post_url = f"https://graph.facebook.com/{page_id}/feed"
        
        response = requests.post(post_url, data=post_data)
        return response.json()
    
    def post_image(self, post_text: str, image_url: str, page_token: str, page_id: str) -> Dict[str, Any]:
        """Post image with text to Facebook page"""
        post_data = {
            'message': post_text,
            'url': image_url,
            'access_token': page_token
        }
        post_url = f"https://graph.facebook.com/{page_id}/photos"
        
        response = requests.post(post_url, data=post_data)
        return response.json()
    
    def get_recent_posts(self, page_token: str, page_id: str, limit: int = 20) -> Dict[str, Any]:
        """Get recent posts from Facebook page"""
        posts_url = f"https://graph.facebook.com/{page_id}/posts"
        posts_params = {
            'access_token': page_token,
            'fields': 'id,message,created_time,attachments',
            'limit': limit
        }
        
        response = requests.get(posts_url, params=posts_params)
        return response.json()
    
    def get_post_analytics(self, page_token: str, post_id: str) -> Dict[str, Any]:
        """Get detailed analytics for a specific post"""
        try:
            # Get post insights
            insights_url = f"https://graph.facebook.com/{post_id}/insights"
            insights_params = {
                'access_token': page_token,
                'metric': 'post_impressions,post_engaged_users,post_clicks,post_reactions_by_type_total'
            }
            
            insights_response = requests.get(insights_url, params=insights_params)
            insights_data = insights_response.json()
            
            # Get post reactions
            reactions_url = f"https://graph.facebook.com/{post_id}/reactions"
            reactions_params = {
                'access_token': page_token,
                'summary': 'total_count'
            }
            
            reactions_response = requests.get(reactions_url, params=reactions_params)
            reactions_data = reactions_response.json()
            
            # Process insights data
            analytics = {
                'views': 0,
                'engaged_users': 0,
                'clicks': 0,
                'likes': 0,
                'metadata': {
                    'reactions': {
                        'like': 0,
                        'love': 0,
                        'wow': 0,
                        'haha': 0,
                        'sad': 0,
                        'angry': 0
                    }
                }
            }
            
            if 'data' in insights_data:
                for metric in insights_data['data']:
                    if metric['name'] == 'post_impressions':
                        analytics['views'] = metric['values'][0]['value']
                    elif metric['name'] == 'post_engaged_users':
                        analytics['engaged_users'] = metric['values'][0]['value']
                    elif metric['name'] == 'post_clicks':
                        analytics['clicks'] = metric['values'][0]['value']
                    elif metric['name'] == 'post_reactions_by_type_total':
                        reactions = metric['values'][0]['value']
                        analytics['metadata']['reactions'] = reactions
                        analytics['likes'] = sum(reactions.values())
            
            # Add total reactions
            if 'summary' in reactions_data and 'total_count' in reactions_data['summary']:
                analytics['likes'] = reactions_data['summary']['total_count']
            
            return analytics
            
        except Exception as e:
            print(f"Error getting post analytics: {str(e)}")
            return {
                'views': 0,
                'engaged_users': 0,
                'clicks': 0,
                'likes': 0,
                'metadata': {'reactions': {}}
            }
