"""
AI-powered tools for post suggestions
"""
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from ..api.facebook_client import FacebookClient
from ..api.facebook_analytics import FacebookAnalytics
from ..ai.mistral_client import MistralClient


def register_ai_tools(mcp: FastMCP, client: FacebookClient, analytics: FacebookAnalytics, mistral: MistralClient):
    """Register AI-powered tools"""
    
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
            if not client.is_connected():
                return "❌ Facebook not connected. Use 'get_facebook_auth_url()' to get the authorization URL."
            
            # Fetch analytics data if requested
            analytics_data = []
            if use_analytics:
                print("📊 Fetching previous analytics data...")
                analytics_data = analytics.fetch_analytics_data(limit=20)
                print(f"📈 Found {len(analytics_data)} previous posts for analysis")
            
            # Generate suggestion using Mistral AI
            print("🤖 Generating post suggestion with Mistral AI...")
            suggestion = mistral.generate_post_suggestion(business_info, analytics_data, additional_context)
            
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
