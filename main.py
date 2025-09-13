"""
MCP Server Template with Facebook Integration
"""

from mcp.server.fastmcp import FastMCP
from pydantic import Field
import json
import os
import urllib.parse
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv
import mcp.types as types


load_dotenv()
mcp = FastMCP("Facebook MCP Server", port=3000, stateless_http=True, debug=True)

# Facebook App Configuration
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
FACEBOOK_REDIRECT_URI = os.getenv("FACEBOOK_REDIRECT_URI") or "http://localhost:8000/facebook/callback"
LE_CHAT_USER_ID=os.getenv("LE_CHAT_USER_ID")

# Mistral AI Configuration
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "8D6fUPey5WOog0pZjaZmqB53CW1gYc6o")

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


def fetch_facebook_analytics_data(limit: int = 20) -> List[Dict[str, Any]]:
    """Reusable function to fetch Facebook posts with analytics data"""
    try:
        # Use hardcoded user ID
        facebook_user_id = LE_CHAT_USER_ID
        
        # Load user data
        user_data = load_user_data()
        
        if facebook_user_id not in user_data:
            return []
        
        # Get user's pages
        pages = user_data[facebook_user_id].get('pages', [])
        
        if not pages:
            return []
        
        # Use the first available page
        first_page = pages[0]
        page_token = first_page['access_token']
        page_id = first_page['id']
        
        # Get recent posts
        posts_url = f"https://graph.facebook.com/{page_id}/posts"
        posts_params = {
            'access_token': page_token,
            'fields': 'id,message,created_time,attachments',
            'limit': limit
        }
        
        posts_response = requests.get(posts_url, params=posts_params)
        posts_data = posts_response.json()
        
        if 'data' not in posts_data:
            return []
        
        posts = posts_data['data']
        if not posts:
            return []
        
        # Get analytics for each post and format as array of objects
        posts_with_analytics = []
        for post in posts:
            post_id = post['id']
            post_analytics = get_post_analytics_internal(page_token, post_id)
            
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


def generate_post_suggestion_with_mistral(business_info: str, analytics_data: List[Dict[str, Any]], additional_context: str = "") -> str:
    """Generate post suggestion using Mistral AI based on business info and analytics"""
    try:
        # Prepare analytics summary
        analytics_summary = ""
        if analytics_data:
            total_posts = len(analytics_data)
            total_views = sum(post['analytics'].get('views', 0) for post in analytics_data)
            total_reactions = sum(post['analytics'].get('likes', 0) for post in analytics_data)
            avg_views = total_views / total_posts if total_posts > 0 else 0
            avg_reactions = total_reactions / total_posts if total_posts > 0 else 0
            
            # Find best performing posts
            best_posts = sorted(analytics_data, key=lambda x: x['analytics'].get('views', 0), reverse=True)[:3]
            
            analytics_summary = f"""
Previous Performance Summary:
- Total posts analyzed: {total_posts}
- Average views per post: {avg_views:.0f}
- Average reactions per post: {avg_reactions:.0f}
- Best performing posts:
"""
            for i, post in enumerate(best_posts, 1):
                analytics_summary += f"  {i}. Views: {post['analytics'].get('views', 0)}, Reactions: {post['analytics'].get('likes', 0)}\n"
                analytics_summary += f"     Text: {post['text'][:100]}{'...' if len(post['text']) > 100 else ''}\n"
                analytics_summary += f"     Type: {'Image post' if post['has_image'] else 'Text post'}\n"
        else:
            analytics_summary = "No previous analytics data available."
        
        # Prepare prompt for Mistral
        prompt = f"""
You are a social media marketing expert. Generate a Facebook post suggestion based on the following information:

Business Information:
{business_info}

{analytics_summary}

Additional Context:
{additional_context}

Please generate:
1. A compelling Facebook post text (2-3 sentences max)
2. Post type recommendation (text or image)
3. Best time to post (if analytics suggest patterns)
4. Engagement strategy tips

Format your response as:
POST SUGGESTION:
[Your post text here]

TYPE: [text/image]

TIMING: [Your timing recommendation]

TIPS: [Your engagement tips]
"""
        
        # Call Mistral API
        mistral_url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "mistral-medium-latest",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        response = requests.post(mistral_url, headers=headers, json=data)
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            return "❌ Error generating post suggestion with Mistral AI"
            
    except Exception as e:
        return f"❌ Error generating post suggestion: {str(e)}"


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


@mcp.tool(
    title="Get Facebook Post History",
    description="Get recent Facebook posts with basic analytics (last 20 posts)",
)
def get_facebook_post_history() -> str:
    """Get recent Facebook posts with analytics data"""
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
        
        # Use the first available page
        first_page = pages[0]
        page_token = first_page['access_token']
        page_name = first_page['name']
        page_id = first_page['id']
        
        print(f"📊 Getting post history for page: {page_name} (ID: {page_id})")
        
        # Get recent posts
        posts_url = f"https://graph.facebook.com/{page_id}/posts"
        posts_params = {
            'access_token': page_token,
            'fields': 'id,message,created_time,attachments',
            'limit': 20
        }
        
        posts_response = requests.get(posts_url, params=posts_params)
        posts_data = posts_response.json()
        
        if 'data' not in posts_data:
            error_msg = posts_data.get('error', {}).get('message', 'Unknown error')
            return f"❌ Error getting posts: {error_msg}"
        
        posts = posts_data['data']
        if not posts:
            return f"📭 No posts found for '{page_name}'"
        
        # Get analytics for each post
        posts_with_analytics = []
        for post in posts:
            post_id = post['id']
            post_analytics = get_post_analytics_internal(page_token, post_id)
            
            post_info = {
                'id': post_id,
                'message': post.get('message', ''),
                'created_time': post['created_time'],
                'post_url': f"https://www.facebook.com/{post_id}",
                'analytics': post_analytics
            }
            
            # Check if it's an image post
            if post.get('attachments', {}).get('data'):
                attachments = post['attachments']['data']
                for attachment in attachments:
                    if attachment.get('type') == 'photo':
                        post_info['has_image'] = True
                        if attachment.get('media', {}).get('image'):
                            post_info['image_url'] = attachment['media']['image']['src']
                        break
            
            posts_with_analytics.append(post_info)
        
        # Format response
        result = f"📊 Post Analytics for '{page_name}'\n"
        result += f"📅 Found {len(posts_with_analytics)} recent posts\n\n"
        
        for i, post in enumerate(posts_with_analytics, 1):
            result += f"📝 Post #{i}\n"
            result += f"🔗 URL: {post['post_url']}\n"
            result += f"📅 Date: {post['created_time']}\n"
            if post.get('message'):
                result += f"💬 Message: {post['message'][:100]}{'...' if len(post.get('message', '')) > 100 else ''}\n"
            if post.get('has_image'):
                result += f"🖼️ Type: Image post\n"
            else:
                result += f"📄 Type: Text post\n"
            
            analytics = post['analytics']
            result += f"📊 Analytics:\n"
            result += f"  👀 Views: {analytics.get('views', 0)}\n"
            result += f"  👍 Total Reactions: {analytics.get('likes', 0)}\n"
            result += f"  🖱️ Clicks: {analytics.get('clicks', 0)}\n"
            
            if analytics.get('metadata', {}).get('reactions'):
                reactions = analytics['metadata']['reactions']
                result += f"  😊 Reactions: Like({reactions.get('like', 0)}) Love({reactions.get('love', 0)}) Wow({reactions.get('wow', 0)}) Haha({reactions.get('haha', 0)})\n"
            
            result += "\n" + "-"*50 + "\n\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error getting post history: {str(e)}"


def get_post_analytics_internal(page_token: str, post_id: str) -> dict:
    """Internal function to get analytics for a specific post"""
    try:
        # Get post insights
        insights_url = f"https://graph.facebook.com/{post_id}/insights"
        insights_params = {
            'access_token': page_token,
            'metric': 'post_impressions,post_reactions_by_type_total,post_clicks',
            'period': 'lifetime'
        }
        
        insights_response = requests.get(insights_url, params=insights_params)
        insights_data = insights_response.json()
        
        if 'data' not in insights_data:
            return {
                'views': 0,
                'likes': 0,
                'clicks': 0,
                'metadata': {
                    'platform': 'facebook',
                    'postId': post_id,
                    'reactions': {'like': 0, 'love': 0, 'wow': 0, 'haha': 0, 'sorry': 0, 'anger': 0, 'total': 0},
                    'lastUpdated': 'error'
                }
            }
        
        # Process metrics
        metrics = {}
        total_reactions = 0
        reaction_breakdown = {}
        
        for metric in insights_data['data']:
            if metric.get('values') and len(metric['values']) > 0:
                value = metric['values'][0]['value']
                
                if metric['name'] == 'post_reactions_by_type_total':
                    if isinstance(value, dict):
                        reaction_breakdown = value
                        total_reactions = sum(reaction_breakdown.values())
                        metrics['total_reactions'] = total_reactions
                    else:
                        metrics['total_reactions'] = value
                        total_reactions = value
                else:
                    metrics[metric['name']] = value
        
        return {
            'views': metrics.get('post_impressions', 0),
            'likes': total_reactions,
            'clicks': metrics.get('post_clicks', 0),
            'metadata': {
                'platform': 'facebook',
                'postId': post_id,
                'reactions': {
                    'like': reaction_breakdown.get('like', 0),
                    'love': reaction_breakdown.get('love', 0),
                    'wow': reaction_breakdown.get('wow', 0),
                    'haha': reaction_breakdown.get('haha', 0),
                    'sorry': reaction_breakdown.get('sorry', 0),
                    'anger': reaction_breakdown.get('anger', 0),
                    'total': total_reactions
                },
                'lastUpdated': '2024-01-01T00:00:00Z'  # Current timestamp would be better
            }
        }
        
    except Exception as e:
        print(f"Error getting analytics for post {post_id}: {str(e)}")
        return {
            'views': 0,
            'likes': 0,
            'clicks': 0,
            'metadata': {
                'platform': 'facebook',
                'postId': post_id,
                'reactions': {'like': 0, 'love': 0, 'wow': 0, 'haha': 0, 'sorry': 0, 'anger': 0, 'total': 0},
                'lastUpdated': 'error'
            }
        }


@mcp.tool(
    title="Get Facebook Post Analytics",
    description="Get detailed analytics for a specific Facebook post",
)
def get_facebook_post_analytics(
    post_id: str = Field(description="Facebook post ID to get analytics for")
) -> str:
    """Get detailed analytics for a specific Facebook post"""
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
        
        # Use the first available page
        first_page = pages[0]
        page_token = first_page['access_token']
        page_name = first_page['name']
        
        print(f"📊 Getting analytics for post: {post_id}")
        
        # Get analytics
        analytics = get_post_analytics_internal(page_token, post_id)
        
        # Format response
        result = f"📊 Analytics for Post: {post_id}\n"
        result += f"📄 Page: {page_name}\n"
        result += f"🔗 URL: https://www.facebook.com/{post_id}\n\n"
        
        result += f"📈 Performance Metrics:\n"
        result += f"  👀 Views: {analytics['views']:,}\n"
        result += f"  👍 Total Reactions: {analytics['likes']:,}\n"
        result += f"  🖱️ Clicks: {analytics['clicks']:,}\n\n"
        
        reactions = analytics['metadata']['reactions']
        result += f"😊 Reaction Breakdown:\n"
        result += f"  👍 Like: {reactions['like']:,}\n"
        result += f"  ❤️ Love: {reactions['love']:,}\n"
        result += f"  😮 Wow: {reactions['wow']:,}\n"
        result += f"  😂 Haha: {reactions['haha']:,}\n"
        result += f"  😢 Sorry: {reactions['sorry']:,}\n"
        result += f"  😡 Anger: {reactions['anger']:,}\n"
        result += f"  📊 Total: {reactions['total']:,}\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error getting post analytics: {str(e)}"


@mcp.tool(
    title="Suggest Facebook Post",
    description="Generate AI-powered Facebook post suggestions based on business info and previous analytics",
)
def suggest_facebook_post(
    business_info: str = Field(description="Information about your business, products, or services"),
    additional_context: str = Field(description="Any additional context or specific requirements for the post", default=""),
    use_analytics: bool = Field(description="Whether to analyze previous post performance for better suggestions", default=True)
) -> str:
    """Generate AI-powered Facebook post suggestions using Mistral AI"""
    try:
        # Check if Facebook is connected
        facebook_user_id = LE_CHAT_USER_ID
        user_data = load_user_data()
        
        if facebook_user_id not in user_data:
            return "❌ Facebook not connected. Use 'get_facebook_auth_url()' to get the authorization URL."
        
        # Fetch analytics data if requested
        analytics_data = []
        if use_analytics:
            print("📊 Fetching previous analytics data...")
            analytics_data = fetch_facebook_analytics_data(limit=20)
            print(f"📈 Found {len(analytics_data)} previous posts for analysis")
        
        # Generate suggestion using Mistral AI
        print("🤖 Generating post suggestion with Mistral AI...")
        suggestion = generate_post_suggestion_with_mistral(business_info, analytics_data, additional_context)
        
        # Format the response
        result = f"🎯 AI-Powered Facebook Post Suggestion\n"
        result += f"📊 Based on {len(analytics_data)} previous posts\n\n"
        result += suggestion
        
        if analytics_data:
            result += f"\n\n📈 Analytics Summary:\n"
            result += f"• Analyzed {len(analytics_data)} recent posts\n"
            total_views = sum(post['analytics'].get('views', 0) for post in analytics_data)
            avg_views = total_views / len(analytics_data) if analytics_data else 0
            result += f"• Average views: {avg_views:.0f}\n"
            
            # Find best performing post type
            image_posts = [p for p in analytics_data if p['has_image']]
            text_posts = [p for p in analytics_data if not p['has_image']]
            
            if image_posts and text_posts:
                avg_image_views = sum(p['analytics'].get('views', 0) for p in image_posts) / len(image_posts)
                avg_text_views = sum(p['analytics'].get('views', 0) for p in text_posts) / len(text_posts)
                
                if avg_image_views > avg_text_views:
                    result += f"• Image posts perform better (avg: {avg_image_views:.0f} views)\n"
                else:
                    result += f"• Text posts perform better (avg: {avg_text_views:.0f} views)\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error generating post suggestion: {str(e)}"


@mcp.tool(
    title="Get Facebook Analytics Data",
    description="Get structured analytics data as JSON for external processing",
)
def get_facebook_analytics_data(
    limit: int = Field(description="Number of recent posts to analyze", default=20)
) -> str:
    """Get structured Facebook analytics data as JSON string"""
    try:
        # Check if Facebook is connected
        facebook_user_id = LE_CHAT_USER_ID
        user_data = load_user_data()
        
        if facebook_user_id not in user_data:
            return "❌ Facebook not connected. Use 'get_facebook_auth_url()' to get the authorization URL."
        
        # Fetch analytics data
        analytics_data = fetch_facebook_analytics_data(limit)
        
        if not analytics_data:
            return "📭 No posts found or error fetching data"
        
        # Return as JSON string
        return json.dumps(analytics_data, indent=2)
        
    except Exception as e:
        return f"❌ Error getting analytics data: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
