# MCP SSE Service

A comprehensive MCP (Model Context Protocol) SSE server with multiple tool integrations for weather, news, GitHub, and text processing.

## 🚀 Features

- **🌤️ Weather Tools**: Current weather and forecasts using OpenWeatherMap API
- **📰 News Tools**: Top headlines and news search using NewsAPI
- **🐙 GitHub Tools**: Repository info, user profiles, and repository search
- **📝 Text Tools**: Text processing, formatting, hashing, and extraction utilities
- **⚡ SSE Protocol**: Server-Sent Events for real-time communication
- **🔧 Auto-registration**: Tools automatically register with the MCP server
- **🌍 Environment Configuration**: Easy setup with environment variables
- **📋 Modular Design**: Each tool category in separate files

## 📦 Installation

1. **Clone or download the project**
2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:

   ```bash
   # Copy the example environment file
   cp env_example.txt .env

   # Edit .env and add your API keys
   ```

## 🔧 Configuration

Copy `env_example.txt` to `.env` and configure the following:

### MCP Server Settings

```env
MCP_SERVER_NAME=mcp-sse-service
MCP_SERVER_VERSION=1.0.0
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
```

### API Keys (Optional - tools will be disabled if keys are missing)

```env
# Weather API (OpenWeatherMap)
WEATHER_API_KEY=your_openweathermap_api_key

# News API
NEWS_API_KEY=your_newsapi_key

# GitHub API (Optional - for higher rate limits)
GITHUB_TOKEN=your_github_token
```

### API Endpoints (Default values provided)

```env
WEATHER_API_BASE_URL=https://api.openweathermap.org/data/2.5
NEWS_API_BASE_URL=https://newsapi.org/v2
GITHUB_API_BASE_URL=https://api.github.com
```

### Logging

```env
LOG_LEVEL=INFO
```

## 🏃‍♂️ Usage

### Start the Server

```bash
python main.py
```

The server will start on `http://localhost:8000` by default.

### Endpoints

- **SSE Endpoint**: `http://localhost:8000/sse`
- **Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

### Available Tools

#### 🌤️ Weather Tools

- `get_current_weather(city)` - Get current weather for a city
- `get_weather_forecast(city, days)` - Get weather forecast (1-5 days)

#### 📰 News Tools

- `get_top_headlines(country, category, page_size)` - Get top news headlines
- `search_news(query, language, sort_by, page_size)` - Search news articles

#### 🐙 GitHub Tools

- `get_repository_info(owner, repo)` - Get detailed repository information
- `get_user_info(username)` - Get user profile information
- `search_repositories(query, sort, order, per_page)` - Search repositories
- `get_repository_releases(owner, repo, per_page)` - Get repository releases

#### 📝 Text Tools

- `text_format(text, operation)` - Format text (upper, lower, title, etc.)
- `text_count(text, analysis_type)` - Analyze text statistics
- `text_search_replace(text, search, replace, case_sensitive)` - Search and replace
- `text_extract_emails(text)` - Extract email addresses
- `text_extract_urls(text)` - Extract URLs
- `text_hash(text, algorithm)` - Generate text hashes
- `text_base64_encode(text)` - Base64 encode
- `text_base64_decode(text)` - Base64 decode
- `text_json_format(json_text, indent)` - Format JSON

## 🏗️ Project Structure

```
mcp_service/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── env_example.txt        # Environment configuration template
├── .env                   # Your environment configuration (not in git)
├── README.md             # This file
└── tools/                # Tool modules
    ├── __init__.py       # Package initialization
    ├── weather_tool.py   # Weather-related tools
    ├── news_tool.py      # News-related tools
    ├── github_tool.py    # GitHub-related tools
    └── text_tool.py      # Text processing tools
```

## 🛠️ Development

### Adding New Tools

1. Create a new file in the `tools/` directory
2. Import the MCP instance from `main.py`
3. Implement your tools using the `@mcp.tool()` decorator
4. Add an import for your tool module in `main.py`

Example:

```python
# tools/my_tool.py
from mcp_instance import mcp

@mcp.tool()
async def my_tool(input_text: str) -> str:
    """My custom tool"""
    return f"Processed: {input_text}"

# In main.py - add the import:
import tools.my_tool  # Tool will auto-register via decorator
```

### Tool Architecture

This project uses **decorator auto-registration** following FastMCP best practices:

- ✅ Tools use `@mcp.tool()` decorator for automatic registration
- ✅ Clean and idiomatic FastMCP code style
- ✅ No manual registration needed - tools register when modules are imported
- ✅ Follows Python decorator patterns
- ✅ Automatic tool discovery on server startup

### Error Handling

All tools include comprehensive error handling:

- HTTP request errors
- API response errors
- Input validation errors
- General exceptions

### Logging

The service uses Python's built-in logging module. Set `LOG_LEVEL` in your `.env` file to control verbosity:

- `DEBUG`: Detailed debugging information
- `INFO`: General operational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages only

## 📝 API Keys Setup

### OpenWeatherMap API

1. Visit [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Add to `.env` as `WEATHER_API_KEY`

### NewsAPI

1. Visit [NewsAPI](https://newsapi.org/)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Add to `.env` as `NEWS_API_KEY`

### GitHub API (Optional)

1. Visit [GitHub Settings](https://github.com/settings/tokens)
2. Generate a personal access token
3. Add to `.env` as `GITHUB_TOKEN`

## 🔍 Testing

Test individual tools by starting the server and using the documentation interface at `http://localhost:8000/docs`.

Example using curl:

```bash
# Test the SSE endpoint
curl -N -H "Accept: text/event-stream" http://localhost:8000/sse
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source. Feel free to use and modify as needed.

## 🆘 Troubleshooting

### Common Issues

1. **ImportError**: Make sure all dependencies are installed with `pip install -r requirements.txt`
2. **API Errors**: Check your API keys in the `.env` file
3. **Port Already in Use**: Change the `MCP_SERVER_PORT` in your `.env` file
4. **Missing .env**: Copy `env_example.txt` to `.env` and configure your settings

### Getting Help

1. Check the logs for detailed error messages
2. Verify your API keys are correct
3. Test with individual tools first
4. Check the documentation at `/docs` endpoint

## 🎯 Example Usage

```python
# Example of calling a tool (this would typically be done via MCP client)
result = await get_current_weather("London")
print(result)
# Output: 🌤️ Current weather in London, GB: 15°C, partly cloudy...
```
