"""
Facebook analytics tools
"""
from mcp.server.fastmcp import FastMCP
from pydantic import Field
import json
from ..api.facebook_client import FacebookClient
from ..api.facebook_analytics import FacebookAnalytics


def register_analytics_tools(mcp: FastMCP, client: FacebookClient, analytics: FacebookAnalytics):
    """Register analytics tools"""
    
    @mcp.tool(
        title="Get Facebook Post History",
        description="Get recent Facebook posts with basic analytics (last 20 posts)",
    )
    def get_facebook_post_history() -> str:
        """Get recent Facebook posts with basic analytics"""
        return analytics.get_post_history_summary(limit=20)

    @mcp.tool(
        title="Get Facebook Post Analytics",
        description="Get detailed analytics for a specific Facebook post",
    )
    def get_facebook_post_analytics(
        post_id: str = Field(description="Facebook post ID to get analytics for")
    ) -> str:
        """Get detailed analytics for a specific Facebook post"""
        return analytics.get_detailed_post_analytics(post_id)

    @mcp.tool(
        title="Get Facebook Analytics Data",
        description="Get structured analytics data as JSON for external processing",
    )
    def get_facebook_analytics_data(
        limit: int = Field(description="Number of recent posts to analyze", default=20)
    ) -> str:
        """Get structured Facebook analytics data as JSON string"""
        try:
            if not client.is_connected():
                return "❌ Facebook not connected. Use 'get_facebook_auth_url()' to get the authorization URL."
            
            # Fetch analytics data
            analytics_data = analytics.fetch_analytics_data(limit)
            
            if not analytics_data:
                return "📭 No posts found or error fetching data"
            
            # Return as JSON string
            return json.dumps(analytics_data, indent=2)
            
        except Exception as e:
            return f"❌ Error getting analytics data: {str(e)}"
