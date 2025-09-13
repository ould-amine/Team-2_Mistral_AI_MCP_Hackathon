"""
Facebook authentication tools
"""
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from ..api.facebook_client import FacebookClient


def register_auth_tools(mcp: FastMCP, client: FacebookClient):
    """Register authentication tools"""
    
    @mcp.tool(
        title="Get Facebook Auth URL",
        description="Generate Facebook OAuth URL for page connection",
    )
    def get_facebook_auth_url() -> str:
        """Generate Facebook OAuth URL for page connection"""
        return client.get_auth_url()

    @mcp.tool(
        title="Check Facebook Connection",
        description="Check if Facebook page is connected and ready for posting",
    )
    def check_facebook_connection() -> str:
        """Check if Facebook page is connected and ready for posting"""
        try:
            if not client.is_connected():
                return "❌ Facebook not connected. Use 'get_facebook_auth_url()' to get the authorization URL."
            
            page = client.get_first_page()
            if not page:
                return "❌ No Facebook pages found. Please reconnect your account using 'get_facebook_auth_url()'."
            
            page_name = page['name']
            return f"✅ Facebook connected! Ready to post to '{page_name}'"
            
        except Exception as e:
            return f"❌ Error checking Facebook connection: {str(e)}"
