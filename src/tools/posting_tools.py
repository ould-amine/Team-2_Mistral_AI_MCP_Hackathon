"""
Facebook posting tools
"""
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from ..api.facebook_client import FacebookClient
from ..api.facebook_posts import FacebookPosts


def register_posting_tools(mcp: FastMCP, client: FacebookClient, posts: FacebookPosts):
    """Register posting tools"""
    
    @mcp.tool(
        title="Post to Facebook Page",
        description="Post text content and/or image to Facebook page",
    )
    def post_to_facebook_page(
        post_text: str = Field(description="Message content to post to Facebook page"),
        image_url: str = Field(description="URL of the image to post (optional)", default="")
    ) -> str:
        """Post text content and/or image to Facebook page"""
        try:
            if not client.is_connected():
                return "❌ Facebook not connected. Use 'get_facebook_auth_url()' to get the authorization URL."
            
            page = client.get_first_page()
            if not page:
                return "❌ No Facebook pages found. Please reconnect your account."
            
            page_token = page['access_token']
            page_id = page['id']
            page_name = page['name']
            
            # Determine post type and make the post
            if image_url:
                # Image post
                result = posts.post_image(post_text, image_url, page_token, page_id)
                post_type = "image"
            else:
                # Text post
                result = posts.post_text(post_text, page_token, page_id)
                post_type = "text"
            
            if 'id' in result:
                post_id = result['id']
                facebook_post_url = f"https://www.facebook.com/{post_id}"
                
                return f"✅ Successfully posted {post_type} to '{page_name}'!\n\n🔗 View post: {facebook_post_url}\n\n📝 Content: {post_text}"
            else:
                return f"❌ Error posting to Facebook: {result}"
                
        except Exception as e:
            return f"❌ Error posting to Facebook: {str(e)}"
