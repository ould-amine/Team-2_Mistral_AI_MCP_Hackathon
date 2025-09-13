"""
Facebook analytics management
"""
from typing import Dict, Any, List
from .facebook_client import FacebookClient
from .facebook_posts import FacebookPosts


class FacebookAnalytics:
    """Facebook analytics management"""
    
    def __init__(self, client: FacebookClient, posts: FacebookPosts):
        self.client = client
        self.posts = posts
    
    def fetch_analytics_data(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch Facebook posts with analytics data"""
        try:
            if not self.client.is_connected():
                return []
            
            page = self.client.get_first_page()
            if not page:
                return []
            
            page_token = page['access_token']
            page_id = page['id']
            
            # Get recent posts
            posts_data = self.posts.get_recent_posts(page_token, page_id, limit)
            
            if 'data' not in posts_data:
                return []
            
            posts = posts_data['data']
            if not posts:
                return []
            
            # Get analytics for each post and format as array of objects
            posts_with_analytics = []
            for post in posts:
                post_id = post['id']
                post_analytics = self.posts.get_post_analytics(page_token, post_id)
                
                # Check if it's an image post
                has_image = False
                image_url = None
                if post.get('attachments', {}).get('data'):
                    attachments = post['attachments']['data']
                    for attachment in attachments:
                        if attachment.get('type') == 'photo':
                            has_image = True
                            if attachment.get('media', {}).get('image'):
                                image_url = attachment['media']['image']['src']
                            break
                
                post_info = {
                    'post_id': post_id,
                    'created_date': post['created_time'],
                    'text': post.get('message', ''),
                    'has_image': has_image,
                    'image_url': image_url,
                    'analytics': post_analytics
                }
                
                posts_with_analytics.append(post_info)
            
            return posts_with_analytics
            
        except Exception as e:
            print(f"Error fetching analytics data: {str(e)}")
            return []
    
    def get_post_history_summary(self, limit: int = 20) -> str:
        """Get formatted post history summary"""
        try:
            if not self.client.is_connected():
                return "❌ Facebook not connected. Use 'get_facebook_auth_url()' to get the authorization URL."
            
            page = self.client.get_first_page()
            if not page:
                return "❌ No Facebook pages found. Please reconnect your account."
            
            page_token = page['access_token']
            page_id = page['id']
            page_name = page['name']
            
            # Get recent posts
            posts_data = self.posts.get_recent_posts(page_token, page_id, limit)
            
            if 'data' not in posts_data:
                return f"❌ Error getting posts: {posts_data}"
            
            posts = posts_data['data']
            if not posts:
                return f"📭 No posts found on '{page_name}'"
            
            # Get analytics for each post
            result = f"📊 Facebook Post History for '{page_name}'\n"
            result += f"📈 Found {len(posts)} recent posts\n\n"
            
            for i, post in enumerate(posts, 1):
                post_id = post['id']
                post_analytics = self.posts.get_post_analytics(page_token, post_id)
                
                result += f"📝 Post #{i}\n"
                result += f"   ID: {post_id}\n"
                result += f"   Created: {post['created_time']}\n"
                result += f"   Message: {post.get('message', 'No message')[:100]}{'...' if len(post.get('message', '')) > 100 else ''}\n"
                result += f"   Views: {post_analytics['views']:,}\n"
                result += f"   Reactions: {post_analytics['likes']:,}\n"
                result += f"   Clicks: {post_analytics['clicks']:,}\n"
                result += f"   URL: https://www.facebook.com/{post_id}\n\n"
            
            return result
            
        except Exception as e:
            return f"❌ Error getting post history: {str(e)}"
    
    def get_detailed_post_analytics(self, post_id: str) -> str:
        """Get detailed analytics for a specific post"""
        try:
            if not self.client.is_connected():
                return "❌ Facebook not connected. Use 'get_facebook_auth_url()' to get the authorization URL."
            
            page = self.client.get_first_page()
            if not page:
                return "❌ No Facebook pages found. Please reconnect your account."
            
            page_token = page['access_token']
            
            # Get post analytics
            analytics = self.posts.get_post_analytics(page_token, post_id)
            
            # Format the response
            result = f"📊 Detailed Analytics for Post {post_id}\n"
            result += f"🔗 URL: https://www.facebook.com/{post_id}\n\n"
            
            result += f"📈 Performance Metrics:\n"
            result += f"  👀 Views: {analytics['views']:,}\n"
            result += f"  👥 Engaged Users: {analytics['engaged_users']:,}\n"
            result += f"  🖱️ Clicks: {analytics['clicks']:,}\n"
            result += f"  ❤️ Total Reactions: {analytics['likes']:,}\n\n"
            
            # Reaction breakdown
            reactions = analytics['metadata']['reactions']
            if reactions:
                result += f"😊 Reaction Breakdown:\n"
                for reaction_type, count in reactions.items():
                    if count > 0:
                        result += f"  {reaction_type.title()}: {count:,}\n"
            
            return result
            
        except Exception as e:
            return f"❌ Error getting post analytics: {str(e)}"
