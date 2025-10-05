# Alphaminr Backend - Newsletter Generation Engine

The backend API for the Alphaminr Newsletter Generator. This provides AI-powered newsletter generation with policy-focused analysis and company impact identification using the official Brave Search MCP Server.

## 🎯 Features

- **Policy-Focused Analysis** - Analyzes major news headlines and government policies
- **Company Impact Identification** - Identifies publicly traded companies affected by each development
- **Real-Time Web Search** - Uses official Brave Search MCP Server for current news and market data
- **AI Content Generation** - Claude AI generates insightful, policy-focused content
- **Enhanced MCP Integration** - Official Brave Search MCP Server with web search, news search, and summarizer
- **Structured HTML Output** - Generates complete HTML newsletters ready for email distribution
- **Database Storage** - PostgreSQL database for newsletter persistence
- **Health Monitoring** - Built-in health check endpoints
- **Test Endpoints** - Comprehensive testing for MCP integration

## 📰 Newsletter Format

The backend generates newsletters in a structured HTML format with:

- **5 Major Headlines** - Fresh news from the last 18 hours spanning different sectors
- **Impact Analysis** - Each headline includes 2-4 detailed impact vectors
- **Company Identification** - Specific tickers and company names woven naturally into analysis
- **Deep Analysis** - First, second, and third-order effects explained
- **Professional Styling** - Clean, email-ready HTML with responsive design

## 🚀 Deployment

### Deploy to Railway

1. **Connect Repository**:
   - Go to [Railway.app](https://railway.app)
   - Sign in with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select this repository

2. **Set Environment Variables**:
   - `BRAVE_SEARCH_API_KEY` - Your Brave Search API key
   - `ANTHROPIC_API_KEY` - Your Anthropic API key

3. **Deploy**:
   - Railway will automatically detect the Python app
   - It will install dependencies and start the server
   - You'll get a URL like `https://your-app.railway.app`

## 🔧 Local Development

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Node.js** (required for MCP Server):
   ```bash
   # Install Node.js 20+ from https://nodejs.org
   npm install -g @brave/brave-search-mcp-server
   ```

3. **Set Environment Variables**:
   ```bash
   export BRAVE_SEARCH_API_KEY=your_brave_api_key
   export ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

4. **Run Locally**:
   ```bash
   python app.py
   ```

## 📁 Project Structure

```
├── app.py                   # Main Flask application
├── mcp_client.py            # Enhanced MCP client for Brave Search MCP Server
├── test_railway.py          # Test script
├── requirements.txt         # Dependencies
├── Procfile                 # Railway process configuration
├── railway.toml             # Railway deployment settings
└── README.md                # This file
```

## 🔄 How It Works

1. **Enhanced News Search**: Uses official Brave Search MCP Server to search for today's major news headlines and government policies
2. **Policy Analysis**: Searches for government policies, economic data, central bank statements, and geopolitical developments
3. **Company Analysis**: Identifies publicly traded companies affected by each development
4. **Impact Assessment**: Explains how each company might be affected (positive/negative) with detailed causal chains
5. **Content Generation**: Claude AI creates structured HTML newsletters with professional styling
6. **Newsletter Formatting**: Generates complete HTML documents ready for email distribution

## 📊 API Endpoints

- `GET /` - Main interface
- `POST /api/generate` - Generate a new newsletter
- `GET /newsletter/<id>` - View a specific newsletter
- `GET /health` - Health check endpoint
- `POST /api/test-mcp` - Test MCP integration
- `POST /api/test-search` - Test enhanced search capabilities

### Example Usage

```bash
# Generate newsletter
curl -X POST https://your-app.railway.app/api/generate \
  -H "Content-Type: application/json" \
  -d '{}'

# Health check
curl https://your-app.railway.app/health

# Test MCP integration
curl -X POST https://your-app.railway.app/api/test-mcp \
  -H "Content-Type: application/json" \
  -d '{"test_type": "web_search", "query": "S&P 500 current price"}'

# Test enhanced search
curl -X POST https://your-app.railway.app/api/test-search \
  -H "Content-Type: application/json" \
  -d '{"search_type": "government_policies"}'
```

## 🧪 Testing

Run the test script to verify your deployment:

```bash
# Set your Railway URL
export RAILWAY_URL=https://your-app.railway.app

# Run tests
python test_railway.py
```

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BRAVE_SEARCH_API_KEY` | Brave Search API key | Yes |
| `ANTHROPIC_API_KEY` | Anthropic API key | Yes |
| `PORT` | Server port (Railway sets this) | No |

## 💰 Cost Considerations

- **Railway**: Free tier includes 500 hours/month
- **Brave Search**: Free tier available
- **Anthropic**: Pay-per-use pricing

## 🔒 Security

- API keys stored securely in Railway environment variables
- No sensitive data logged
- Database is local to deployment
- HTTPS enabled by default on Railway

## 📈 Monitoring

- Health check endpoint: `/health`
- Railway provides built-in monitoring
- Application logs available in dashboard
- Test endpoints for MCP integration verification

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
