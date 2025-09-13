# 🚀 Facebook MCP Server

A powerful Model Context Protocol (MCP) server for Facebook integration with AI-powered post suggestions, analytics, and automated posting capabilities.

## 🌟 Features

- **🔐 Facebook OAuth Integration** - Secure page connection and authentication
- **📝 Smart Posting** - Post text and images to Facebook pages
- **📊 Advanced Analytics** - Detailed post performance insights
- **🤖 AI-Powered Suggestions** - Mistral AI generates optimized post content
- **📈 Performance Tracking** - Historical data analysis and recommendations
- **🏗️ Modular Architecture** - Clean, maintainable, enterprise-grade code structure

## 📁 Project Structure

```
Team-2_Mistral_AI_MCP_Hackathon/
├── main.py                          # 🚀 Main entry point
├── facebook_callback_server.py      # 🌐 OAuth callback server
├── dev.py                          # 🔄 Development runner (auto-restart)
├── run_servers.py                  # 🏭 Production runner
├── pyproject.toml                  # 📦 Dependencies
├── example_env                     # 🔐 Environment template
│
├── src/                            # 📦 Source code package
│   ├── config/                     # ⚙️ Configuration management
│   │   └── settings.py             # Environment variables & settings
│   ├── utils/                      # 🛠️ Utility functions
│   │   └── data_manager.py         # JSON data management
│   ├── api/                        # 📡 API Layer
│   │   ├── facebook_client.py      # Facebook OAuth & connection
│   │   ├── facebook_posts.py       # Post creation & management
│   │   └── facebook_analytics.py   # Analytics & insights
│   ├── ai/                         # 🤖 AI Integration
│   │   └── mistral_client.py       # Mistral AI for suggestions
│   └── tools/                      # 🔧 MCP Tools
│       ├── auth_tools.py           # Authentication tools
│       ├── posting_tools.py        # Posting tools
│       ├── analytics_tools.py      # Analytics tools
│       └── ai_tools.py             # AI suggestion tools
│
└── docs/                           # 📚 Documentation
    └── ARCHITECTURE.md             # Complete architecture guide
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Facebook Developer Account
- Mistral AI API Key (optional, for AI suggestions)

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd Team-2_Mistral_AI_MCP_Hackathon

# Install dependencies
uv python install
uv sync --locked
```

### 2. Environment Setup

Copy the environment template and configure your credentials:

```bash
cp example_env .env
```

Edit `.env` with your credentials:

```env
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
FACEBOOK_REDIRECT_URI=http://localhost:8000/facebook/callback
LE_CHAT_USER_ID=your_user_id
MISTRAL_API_KEY=your_mistral_api_key
```

### 3. Facebook App Setup

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app
3. Add Facebook Login product
4. Set redirect URI: `http://localhost:8000/facebook/callback`
5. Add permissions: `pages_manage_posts`, `pages_read_engagement`, `pages_show_list`

### 4. Running the Server

#### Development Mode (with auto-restart)
```bash
python3 dev.py
```

#### Production Mode (both MCP and callback servers)
```bash
python3 run_servers.py
```

## 🔧 Available Tools

### Authentication Tools
- **`get_facebook_auth_url()`** - Generate Facebook OAuth URL
- **`process_facebook_callback(code)`** - Process OAuth callback
- **`check_facebook_connection()`** - Check connection status

### Posting Tools
- **`post_to_facebook_page(post_text, image_url?)`** - Post to Facebook page

### Analytics Tools
- **`get_facebook_post_history()`** - Get recent posts with analytics
- **`get_facebook_post_analytics(post_id)`** - Get detailed post analytics
- **`get_facebook_analytics_data(limit?)`** - Get structured analytics data

### AI Tools
- **`suggest_facebook_post(business_info, additional_context?, use_analytics?)`** - AI-powered post suggestions

## 🤖 AI-Powered Features

### Smart Post Suggestions

The server uses Mistral AI to generate optimized Facebook posts based on:

- **Business Information** - Your company, products, services
- **Historical Analytics** - Previous post performance data
- **Context** - Specific requirements or campaigns

Example usage:
```python
suggest_facebook_post(
    business_info="Coffee shop in downtown Seattle",
    additional_context="Promoting new seasonal drinks",
    use_analytics=True
)
```

### Analytics-Driven Insights

- **Performance Analysis** - Views, reactions, clicks tracking
- **Content Optimization** - Best performing post types
- **Engagement Patterns** - Optimal posting times and strategies

## 📊 Analytics Data Structure

The server provides structured analytics data:

```json
[
  {
    "post_id": "123456789",
    "created_date": "2024-01-15T10:30:00+0000",
    "text": "Post content...",
    "has_image": true,
    "image_url": "https://...",
    "analytics": {
      "views": 1234,
      "likes": 45,
      "clicks": 12,
      "metadata": {
        "reactions": {
          "like": 30,
          "love": 10,
          "wow": 3,
          "haha": 2
        }
      }
    }
  }
]
```

## 🏗️ Architecture

### Modular Design

The server follows a clean, modular architecture:

- **Configuration Layer** - Centralized settings management
- **API Layer** - Facebook Graph API integration
- **AI Layer** - Mistral AI integration
- **Tools Layer** - MCP tool definitions
- **Utilities** - Shared helper functions

### Key Benefits

- **Maintainable** - Clear separation of concerns
- **Testable** - Each component can be unit tested
- **Scalable** - Easy to add new features
- **Professional** - Enterprise-grade code organization

## 🔄 Development Workflow

### Adding New Tools

1. Create tool function in appropriate `src/tools/` file
2. Register tool in the corresponding register function
3. Import and register in `main.py`

### Adding New AI Providers

1. Create new client in `src/ai/`
2. Update `src/ai/__init__.py`
3. Add tools in `src/tools/ai_tools.py`

### Adding New Social Platforms

1. Create API clients in `src/api/`
2. Add tools in `src/tools/`
3. Update configuration in `src/config/`

## 🧪 Testing

### Running the Inspector

```bash
# Install inspector
npm install -g @modelcontextprotocol/inspector

# Start inspector
npx @modelcontextprotocol/inspector
```

Access the UI at: http://localhost:6274

Configure connection:
- **Transport Type**: Streamable HTTP
- **URL**: http://127.0.0.1:3000/mcp

## 📚 Documentation

- **`docs/ARCHITECTURE.md`** - Complete architecture documentation
- **`src/`** - Well-documented source code
- **Inline Comments** - Detailed function documentation

## 🚀 Deployment

### Production Setup

1. Set up environment variables
2. Configure Facebook app for production domain
3. Update redirect URI in Facebook app settings
4. Run with `python3 run_servers.py`

### Environment Variables

```env
FACEBOOK_APP_ID=your_production_app_id
FACEBOOK_APP_SECRET=your_production_app_secret
FACEBOOK_REDIRECT_URI=https://yourdomain.com/facebook/callback
LE_CHAT_USER_ID=your_user_id
MISTRAL_API_KEY=your_mistral_api_key
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the documentation
2. Review the architecture guide
3. Open an issue on GitHub

---

**Built with ❤️ using FastMCP, Facebook Graph API, and Mistral AI**