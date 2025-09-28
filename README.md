# Alphaminr Backend - Newsletter Generation Engine

The backend API for the Alphaminr Newsletter Generator. This provides AI-powered newsletter generation with policy-focused analysis and company impact identification.

## 🎯 Features

- **Policy-Focused Analysis** - Analyzes major news headlines and government policies
- **Company Impact Identification** - Identifies 3-5 publicly traded companies affected by each development
- **Real-Time Web Search** - Uses Brave Search API for current news and market data
- **AI Content Generation** - Claude AI generates insightful, policy-focused content
- **MCP Integration** - Model Context Protocol for enhanced web search
- **Database Storage** - SQLite database for newsletter persistence
- **Health Monitoring** - Built-in health check endpoints

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

2. **Set Environment Variables**:
   ```bash
   export BRAVE_SEARCH_API_KEY=your_brave_api_key
   export ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

3. **Run Locally**:
   ```bash
   python app.py
   ```

## 📁 Project Structure

```
├── app.py                   # Main Flask application
├── mcp_client.py            # MCP client for web search
├── test_railway.py          # Test script
├── requirements.txt         # Dependencies
├── Procfile                 # Railway process configuration
├── railway.toml             # Railway deployment settings
└── README.md                # This file
```

## 🔄 How It Works

1. **News Search**: Searches for today's major news headlines and government policies
2. **Company Analysis**: Identifies publicly traded companies affected by each development
3. **Impact Assessment**: Explains how each company might be affected (positive/negative)
4. **Content Generation**: Claude AI creates engaging, policy-focused content
5. **Newsletter Formatting**: Generates clean HTML newsletter with market data

## 📊 API Endpoints

- `GET /` - Main interface
- `POST /api/generate` - Generate a new newsletter
- `GET /newsletter/<id>` - View a specific newsletter
- `GET /health` - Health check endpoint

### Example Usage

```bash
# Generate newsletter
curl -X POST https://your-app.railway.app/api/generate \
  -H "Content-Type: application/json" \
  -d '{}'

# Health check
curl https://your-app.railway.app/health

# View newsletter
curl https://your-app.railway.app/newsletter/your-newsletter-id
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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
