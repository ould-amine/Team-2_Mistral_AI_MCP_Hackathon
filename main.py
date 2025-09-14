"""
MCP Server Template with Facebook Integration
"""

from mcp.server.fastmcp import FastMCP
from src import (
    FacebookClient, FacebookPosts, FacebookAnalytics, MistralClient,
    register_auth_tools, register_posting_tools, register_analytics_tools, register_ai_tools, 
    register_post_generation_tools, register_chart_tools
)



# Initialize MCP server
mcp = FastMCP("Facebook MCP Server", port=3000, stateless_http=True, debug=True)

# Initialize services
client = FacebookClient()
posts = FacebookPosts(client)
analytics = FacebookAnalytics(client, posts)
mistral = MistralClient()

# Register all tools
register_auth_tools(mcp, client)
register_posting_tools(mcp, client, posts)
register_analytics_tools(mcp, client, analytics)
register_ai_tools(mcp, client, analytics, mistral)
register_post_generation_tools(mcp, client, analytics, mistral)
register_chart_tools(mcp, client, analytics)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
