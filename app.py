#!/usr/bin/env python3
"""
Alphaminr Newsletter Generator - Railway Deployment Version
Focuses on analyzing major news headlines and government policies to identify affected publicly traded companies.
"""
import os
import sys
import re
import sqlite3
import uuid
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
import anthropic
import time
import json
from flask import Flask, request, jsonify, render_template_string
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# --- API Keys and Clients ---
BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Check for API keys and exit if not available
if not BRAVE_SEARCH_API_KEY:
    logger.error("❌ ERROR: BRAVE_SEARCH_API_KEY is required in your .env file. Exiting.")
    sys.exit(1)
if not ANTHROPIC_API_KEY:
    logger.error("❌ ERROR: ANTHROPIC_API_KEY is required in your .env file. Exiting.")
    sys.exit(1)

# Initialize Anthropic client
client = None
try:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    logger.info("✅ Anthropic client initialized")
except Exception as e:
    logger.error(f"❌ ERROR: Failed to initialize Anthropic client: {e}. Exiting.")
    sys.exit(1)

# Initialize Flask app
app = Flask(__name__)

# Web search tool configuration
WEB_SEARCH_TOOL = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 15,  # Allow up to 15 searches per request
    "allowed_domains": [
        "yahoo.com", "finance.yahoo.com", "investing.com", "cnbc.com",
        "cnn.com", "tradingview.com", "bloomberg.com", "techcrunch.com"
    ]
}

# --- HTML Template ---
INJECTED_STYLE = """
        body {
            font-family: Arial, Helvetica, sans-serif;
            line-height: 1.5;
            color: #444;
            background-color: #ffffff;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: #ffffff;
            padding: 30px;
        }
        h1 {
            font-size: 2.2em;
            text-align: center;
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }
        h2 {
            font-size: 1.4em;
            margin-top: 35px;
            color: #34495e;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
            margin-bottom: 20px;
        }
        h3 {
            font-size: 1.2em;
            margin-top: 30px;
            color: #7f8c8d;
            font-weight: 600;
            margin-bottom: 15px;
        }
        .market-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 25px;
            background-color: #f8f9fa;
        }
        .market-table td {
            border: 1px solid #dee2e6;
            padding: 15px;
            text-align: center;
            width: 33.33%;
            vertical-align: middle;
        }
        .market-label {
            font-size: 0.85em;
            font-weight: bold;
            color: #6c757d;
            display: block;
            margin-bottom: 5px;
        }
        .market-value {
            font-size: 1.1em;
            font-weight: bold;
            color: #2c3e50;
            display: block;
            margin-bottom: 5px;
        }
        .market-change {
            font-size: 0.9em;
            font-weight: bold;
        }
        .change-positive {
            color: #27ae60;
        }
        .change-negative {
            color: #e74c3c;
        }
        .story {
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 1px solid #ecf0f1;
        }
        .story:last-of-type {
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }
        p {
            margin: 0 0 15px 0;
            color: #444;
            font-size: 1em;
            line-height: 1.6;
        }
        em {
            color: #7f8c8d;
        }
        strong {
            color: #2c3e50;
        }
        u {
            text-decoration: underline;
            text-decoration-color: #3498db;
        }
        .disclaimer {
            font-size: 0.8em;
            color: #7f8c8d;
            margin-top: 30px;
            border-top: 1px solid #ecf0f1;
            padding-top: 20px;
        }
        .trivia-container {
            background-color: #f8f9fa;
            border: 2px solid #3498db;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }
        .trivia-question {
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #2c3e50;
        }
        .trivia-options {
            margin: 15px 0;
        }
        .trivia-option {
            display: block;
            background-color: #ffffff;
            border: 1px solid #bdc3c7;
            padding: 10px 15px;
            margin: 8px 0;
            border-radius: 5px;
            color: #2c3e50;
            text-decoration: none;
            font-weight: bold;
        }
        .trivia-answer {
            font-size: 0.9em;
            color: #7f8c8d;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #ecf0f1;
        }
        .trivia-correct {
            color: #27ae60;
            font-weight: bold;
        }
"""

HTML_TEMPLATE = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alphaminr</title>
    <style>
        {INJECTED_STYLE}
    </style>
</head>
<body>
    <div class="container">
        <h1>Alphaminr</h1>
        <p style="text-align: center; font-size: 0.9em; color: #6c757d; margin-bottom: 20px;">Digging Deeper Than the Headlines.</p>
        
        <div style="text-align: right; font-size: 0.8em; color: #6c757d; margin-bottom: 20px;">{{DATE}}</div>
        
        {{INTRO_PARAGRAPH}}

        <h2>Market Snapshot</h2>
        <table class="market-table">
            {{MARKET_GRID}}
        </table>

        <h2>Policy Impact Analysis</h2>
        {{CORE_STORIES}}
        
        <h3 style="font-size: 1.2em; margin-top: 35px; margin-bottom: 20px; color: #495057; font-weight: 600;">On the Horizon: Regulatory Risks & Opportunities</h3>
        {{HORIZON_SCAN_STORIES}}
        
        <h2>The Brain Teaser</h2>
        <div class="trivia-container">
            {{TRIVIA_SECTION}}
        </div>

        <h2>Disclaimer</h2>
        <p class="disclaimer">The content provided in this newsletter, "Alphaminr," is for informational and educational purposes only. It is not, and should not be construed as, financial, investment, legal, or tax advice. The information contained herein is based on sources believed to be reliable, but its accuracy and completeness cannot be guaranteed. Alphaminr, its authors, and its affiliates are not registered investment advisors and do not provide personalized investment advice. All investment strategies and investments involve risk of loss. Past performance is not indicative of future results. You should not act or refrain from acting on the basis of any content included in this newsletter without seeking financial or other professional advice. Any stock tickers or companies mentioned are for illustrative purposes only and do not constitute a recommendation to buy, sell, or hold any security. You are solely responsible for your own investment decisions.</p>
    </div>
</body>
</html>
"""

# --- Simplified Content Prompt ---
CONTENT_PROMPT = """You are Alphaminr, a sharp, insightful, and slightly irreverent financial newsletter. You have access to real-time web search to gather the latest market data and news.

CRITICAL INSTRUCTION: You MUST use web search to find TODAY'S major news headlines and government policy announcements. Do NOT rely on your training data for current events. Search for news from the last 24-48 hours only.

TONE: Sharp, insightful, and slightly irreverent. You are a clever hedge fund analyst who sees through the noise. Use wit, metaphors, and a conversational style. Start with hooks, not summaries.

SPECIFICITY IS KEY: Avoid vague generalizations at all costs. Use specific proper nouns:
- Companies: NVIDIA, not 'chip makers'
- Products: H100 GPU, not 'new technology'  
- People: Jerome Powell, not 'the central bank'
- Data: $100 billion buildout, not 'significant investment'
- Dates: July 8, 2025, not 'last few months'

WEB SEARCH INSTRUCTIONS:
- ALWAYS use web search to get TODAY'S major news headlines and government policy announcements
- Search for news from the last 24-48 hours ONLY - avoid any news older than 48 hours
- Focus on: Major policy announcements, regulatory changes, geopolitical developments, economic data releases, central bank statements
- Search for current market data (S&P 500, NASDAQ, Bitcoin, etc.) if not provided in the data
- Always cite your sources when using web search results
- CRITICAL: If you cannot find current news (last 24-48 hours), explicitly state this and do not use old information

Today's date: {DATE}

--- PROVIDED DATA ---
{PROVIDED_DATA}
--- END PROVIDED DATA ---

Generate the newsletter content in this EXACT format:

INTRO_PARAGRAPH:
[IMPORTANT: Use web search to find TODAY'S major news headlines and government policies. Write exactly 3 engaging paragraphs here. Start with a contrarian question or bold observation about TODAY'S major developments. Connect the dots between:
1. A major government policy announcement or regulatory change from TODAY or YESTERDAY
2. A significant geopolitical development or international trade policy from TODAY or YESTERDAY  
3. A key economic data release or central bank statement from TODAY or YESTERDAY
Each paragraph should be 4-6 sentences. Make it engaging, insightful, and set the tone for the entire newsletter.
CRITICAL: If you cannot find current news (last 24-48 hours), explicitly state this and do not use old information.]

MARKET_GRID:
S&P 500|[value]|[+/-X.XX%]
NASDAQ 100|[value]|[+/-X.XX%]
Bitcoin (BTC)|[value]|[+/-X.XX%]
Crude Oil (WTI)|[value]|[+/-X.XX%]
Gold|[value]|[+/-X.XX%]
US 10-Yr Treasury|[value]|[+/-X.XX%]
Ethereum (ETH)|[value]|[+/-X.XX%]
VIX|[value]|[+/-X.XX%]
Dow Jones|[value]|[+/-X.XX%]

CORE_STORIES:
[IMPORTANT: Use web search to find TODAY'S major news headlines and government policies. Generate exactly 4 core stories based on news from TODAY or YESTERDAY (last 24-48 hours). Each story should:
- Start with a sharp summary of TODAY'S major headline or policy announcement (the hook)
- Identify 3-5 publicly traded companies that could be significantly affected by this development
- Explain HOW each company might be affected (positive or negative impact on revenue, costs, regulations, etc.)
- Be one flowing paragraph without any colons, subheadings, or formal structure
- Include company tickers as <u>**<u>Company Name (TICKER)</u>**</u> for each mentioned company
- Be hyper-specific with proper nouns, dates, and data points
- Focus on both obvious winners/losers and non-obvious secondary effects
- CRITICAL: If you cannot find current news (last 24-48 hours), explicitly state this and do not use old information]

HORIZON_SCAN_STORIES:
[Generate exactly 3 forward-looking analysis stories. Each story should:
- Identify a specific publicly-traded U.S. company that could be affected by upcoming policy changes or regulatory developments
- Present a non-obvious vulnerability or opportunity that the market might be missing
- Build a logical step-by-step scenario for how this policy/regulatory change would manifest
- Connect the impact directly to fundamentals (revenue, margins, competitive moat, regulatory compliance costs)
- Be one flowing paragraph without any colons, subheadings, or formal structure
- Include company ticker as <u>**<u>Company Name (TICKER)</u>**</u> exactly once]

GAME_CHOICE:
[Choose ONE: Market Cap Showdown, Revenue Race, Workforce Warriors, Corporate Timeline, Dividend Derby, P/E Ratio Challenge]

CRITICAL RULES:
- The intro must be 3 substantive paragraphs connecting major policy/headline themes
- Each story must be a single flowing narrative - NO colons, NO subheadings
- Company tickers appear as <u>**<u>Company Name (TICKER)</u>**</u> for each mentioned company
- Be specific with proper nouns, avoid generalizations
- Maintain sharp, insightful, slightly irreverent tone throughout
- Focus on POLICY IMPACT and REGULATORY CHANGES as the primary drivers of company analysis
- Identify both direct and indirect effects of major headlines on publicly traded companies"""

# --- MCP Client Functions ---
from mcp_client import init_mcp_client, get_mcp_client, BraveSearchMCPClient

# Initialize MCP client
mcp_client = init_mcp_client(BRAVE_SEARCH_API_KEY)

def brave_search_market_data(query):
    """Search for market data using Brave Search MCP Server"""
    try:
        client = get_mcp_client()
        if not client:
            logger.error("❌ MCP client not initialized")
            return {"results": []}
        
        # Use the enhanced market data search
        result = client.search_market_data(query)
        
        # Get AI summary if available
        summary = client.get_enhanced_summary(result)
        if summary:
            result["ai_summary"] = summary
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Brave search market data error: {e}")
        return {"results": []}

def brave_search_news(query):
    """Search for news using Brave Search MCP Server"""
    try:
        client = get_mcp_client()
        if not client:
            logger.error("❌ MCP client not initialized")
            return {"results": []}
        
        # Use the enhanced news search
        result = client.search_news_headlines(query)
        
        # Get AI summary if available
        summary = client.get_enhanced_summary(result)
        if summary:
            result["ai_summary"] = summary
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Brave search news error: {e}")
        return {"results": []}

def brave_search_trends(query):
    """Search for trending topics using Brave Search MCP Server"""
    try:
        client = get_mcp_client()
        if not client:
            logger.error("❌ MCP client not initialized")
            return {"results": []}
        
        # Use the enhanced web search
        result = client.web_search(query, freshness="pd")
        
        # Get AI summary if available
        summary = client.get_enhanced_summary(result)
        if summary:
            result["ai_summary"] = summary
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Brave search trends error: {e}")
        return {"results": []}

# --- Enhanced Search Functions ---

def search_government_policies():
    """Search for government policy announcements from past 24 hours"""
    try:
        client = get_mcp_client()
        if not client:
            logger.error("❌ MCP client not initialized")
            return {"results": []}
        
        # Search for various government policy types
        policy_queries = [
            "government policy announcement today",
            "regulatory changes today",
            "federal policy update today",
            "congressional legislation today",
            "executive order today"
        ]
        
        all_results = []
        for query in policy_queries:
            result = client.search_government_policies(query)
            if result.get("results"):
                all_results.extend(result["results"])
        
        return {"results": all_results}
        
    except Exception as e:
        logger.error(f"❌ Government policies search error: {e}")
        return {"results": []}

def search_economic_data():
    """Search for economic data releases from past 24 hours"""
    try:
        client = get_mcp_client()
        if not client:
            logger.error("❌ MCP client not initialized")
            return {"results": []}
        
        # Search for various economic data types
        economic_queries = [
            "economic data release today",
            "GDP inflation unemployment today",
            "federal reserve economic data today",
            "consumer price index today",
            "employment data today"
        ]
        
        all_results = []
        for query in economic_queries:
            result = client.search_economic_data(query)
            if result.get("results"):
                all_results.extend(result["results"])
        
        return {"results": all_results}
        
    except Exception as e:
        logger.error(f"❌ Economic data search error: {e}")
        return {"results": []}

def search_central_bank_statements():
    """Search for central bank statements from past 24 hours"""
    try:
        client = get_mcp_client()
        if not client:
            logger.error("❌ MCP client not initialized")
            return {"results": []}
        
        # Search for central bank statements
        central_bank_queries = [
            "federal reserve statement today",
            "central bank announcement today",
            "fed meeting minutes today",
            "interest rate decision today",
            "monetary policy today"
        ]
        
        all_results = []
        for query in central_bank_queries:
            result = client.search_central_bank_statements(query)
            if result.get("results"):
                all_results.extend(result["results"])
        
        return {"results": all_results}
        
    except Exception as e:
        logger.error(f"❌ Central bank statements search error: {e}")
        return {"results": []}

def search_geopolitical_developments():
    """Search for geopolitical developments from past 24 hours"""
    try:
        client = get_mcp_client()
        if not client:
            logger.error("❌ MCP client not initialized")
            return {"results": []}
        
        # Search for geopolitical developments
        geo_queries = [
            "geopolitical developments today",
            "international trade policy today",
            "diplomatic relations today",
            "global economic policy today",
            "international sanctions today"
        ]
        
        all_results = []
        for query in geo_queries:
            result = client.news_search(query, freshness="pd")
            if result.get("results"):
                all_results.extend(result["results"])
        
        return {"results": all_results}
        
    except Exception as e:
        logger.error(f"❌ Geopolitical developments search error: {e}")
        return {"results": []}

# --- Simplified Data Fetching Functions ---

def fetch_market_data():
    """Fetch basic market data using Brave Search"""
    logger.info("🌐 Fetching market data using Brave Search...")
    data = {}
    
    # Search for major indices
    indices_query = "S&P 500 NASDAQ Dow Jones current price today"
    indices_data = brave_search_market_data(indices_query)
    
    # Search for commodities and crypto
    commodities_query = "gold oil Bitcoin Ethereum VIX treasury yield current price today"
    commodities_data = brave_search_market_data(commodities_query)
    
    # Parse results and extract market data
    # This is a simplified approach - in practice, you'd want more sophisticated parsing
    all_results = []
    if indices_data.get("results"):
        all_results.extend(indices_data["results"])
    if commodities_data.get("results"):
        all_results.extend(commodities_data["results"])
    
    # Extract market data from search results
    for result in all_results:
        title = result.get("title", "").lower()
        description = result.get("description", "").lower()
        text = f"{title} {description}"
        
        # Look for S&P 500
        if "s&p 500" in text or "spx" in text:
            if "S&P 500" not in data:
                # Extract price and change from text (simplified)
                data['S&P 500'] = "N/A"
                data['S&P 500_change'] = "N/A"
        
        # Look for NASDAQ
        if "nasdaq" in text and "100" in text:
            if "NASDAQ 100" not in data:
                data['NASDAQ 100'] = "N/A"
                data['NASDAQ 100_change'] = "N/A"
        
        # Look for Dow Jones
        if "dow jones" in text or "dow" in text:
            if "Dow Jones" not in data:
                data['Dow Jones'] = "N/A"
                data['Dow Jones_change'] = "N/A"
        
        # Look for Bitcoin
        if "bitcoin" in text or "btc" in text:
            if "Bitcoin (BTC)" not in data:
                data['Bitcoin (BTC)'] = "N/A"
                data['Bitcoin (BTC)_change'] = "N/A"
        
        # Look for Ethereum
        if "ethereum" in text or "eth" in text:
            if "Ethereum (ETH)" not in data:
                data['Ethereum (ETH)'] = "N/A"
                data['Ethereum (ETH)_change'] = "N/A"
        
        # Look for Gold
        if "gold" in text:
            if "Gold" not in data:
                data['Gold'] = "N/A"
                data['Gold_change'] = "N/A"
        
        # Look for Oil
        if "oil" in text or "crude" in text or "wti" in text:
            if "Crude Oil (WTI)" not in data:
                data['Crude Oil (WTI)'] = "N/A"
                data['Crude Oil (WTI)_change'] = "N/A"
        
        # Look for VIX
        if "vix" in text or "volatility" in text:
            if "VIX" not in data:
                data['VIX'] = "N/A"
                data['VIX_change'] = "N/A"
        
        # Look for Treasury
        if "treasury" in text or "10-year" in text or "bond" in text:
            if "US 10-Yr Treasury" not in data:
                data['US 10-Yr Treasury'] = "N/A"
                data['US 10-Yr Treasury_change'] = "N/A"
    
    # Fill missing data with N/A
    required_markets = [
        'S&P 500', 'NASDAQ 100', 'Dow Jones', 'Bitcoin (BTC)',
        'Crude Oil (WTI)', 'Gold', 'US 10-Yr Treasury', 'Ethereum (ETH)', 'VIX'
    ]
    
    for market in required_markets:
        if market not in data:
            data[market] = "N/A"
            data[f"{market}_change"] = "N/A"
        else:
            logger.info(f"✅ {market}: {data[market]} ({data[f'{market}_change']})")
    
    return data

def generate_newsletter_content():
    """Generate newsletter content using Claude with enhanced web search"""
    today_date = datetime.now().strftime("%B %d, %Y")
    
    # Fetch market data
    market_data = fetch_market_data()
    
    # Build provided data string
    provided_data = "Real-time Market Data:\n"
    market_order = [
        'S&P 500', 'NASDAQ 100', 'Bitcoin (BTC)', 'Crude Oil (WTI)', 
        'Gold', 'US 10-Yr Treasury', 'Ethereum (ETH)', 'VIX', 'Dow Jones'
    ]
    
    for market in market_order:
        value = market_data.get(market, "N/A")
        change = market_data.get(f"{market}_change", "N/A")
        provided_data += f"{market}|{value}|{change}\n"
    
    # Enhanced search for current news and policies
    logger.info("🔍 Searching for today's major news headlines and government policies...")
    
    # Search for government policies
    policy_results = search_government_policies()
    if policy_results.get("results"):
        provided_data += f"\nGOVERNMENT POLICIES (Past 24 hours):\n"
        for i, result in enumerate(policy_results["results"][:5], 1):
            provided_data += f"{i}. {result.get('title', 'No title')}\n"
            provided_data += f"   {result.get('description', 'No description')}\n"
            provided_data += f"   Source: {result.get('url', 'No URL')}\n\n"
    
    # Search for economic data
    economic_results = search_economic_data()
    if economic_results.get("results"):
        provided_data += f"\nECONOMIC DATA RELEASES (Past 24 hours):\n"
        for i, result in enumerate(economic_results["results"][:5], 1):
            provided_data += f"{i}. {result.get('title', 'No title')}\n"
            provided_data += f"   {result.get('description', 'No description')}\n"
            provided_data += f"   Source: {result.get('url', 'No URL')}\n\n"
    
    # Search for central bank statements
    central_bank_results = search_central_bank_statements()
    if central_bank_results.get("results"):
        provided_data += f"\nCENTRAL BANK STATEMENTS (Past 24 hours):\n"
        for i, result in enumerate(central_bank_results["results"][:5], 1):
            provided_data += f"{i}. {result.get('title', 'No title')}\n"
            provided_data += f"   {result.get('description', 'No description')}\n"
            provided_data += f"   Source: {result.get('url', 'No URL')}\n\n"
    
    # Search for geopolitical developments
    geo_results = search_geopolitical_developments()
    if geo_results.get("results"):
        provided_data += f"\nGEOPOLITICAL DEVELOPMENTS (Past 24 hours):\n"
        for i, result in enumerate(geo_results["results"][:5], 1):
            provided_data += f"{i}. {result.get('title', 'No title')}\n"
            provided_data += f"   {result.get('description', 'No description')}\n"
            provided_data += f"   Source: {result.get('url', 'No URL')}\n\n"
    
    provided_data += "\nCRITICAL: TODAY'S MAJOR NEWS HEADLINES AND GOVERNMENT POLICIES REQUIRED\n"
    provided_data += "You MUST use web search to find TODAY's major news headlines and government policy announcements from the last 24-48 hours.\n"
    provided_data += "Focus on: Major policy announcements, regulatory changes, geopolitical developments, economic data releases, central bank statements.\n"
    provided_data += "DO NOT use any news older than 48 hours. If you cannot find current news, explicitly state this.\n"
    provided_data += "Market data is provided above but may show N/A values - use web search to get current market prices if needed.\n"
    
    logger.info("🚀 Generating newsletter content with Claude and enhanced web search...")
    
    try:
        enhanced_prompt = CONTENT_PROMPT.format(DATE=today_date, PROVIDED_DATA=provided_data)
        enhanced_prompt += "\n\nFINAL REMINDER: You MUST use web search to find TODAY's major news headlines and government policies. Focus on identifying publicly traded companies affected by these developments."
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            tools=[WEB_SEARCH_TOOL],
            messages=[{
                "role": "user",
                "content": enhanced_prompt
            }]
        )
        
        # Extract content from response
        content = ""
        for content_block in response.content:
            if hasattr(content_block, 'text'):
                content += content_block.text + "\n"
        
        return content
        
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to generate content with Claude: {e}")
        return None

def process_story_formatting(story_content):
    """Clean up story formatting for company tickers"""
    # Remove existing formatting
    story_content = story_content.replace('**', '').replace('<u>', '').replace('</u>', '')
    
    # Find and format company ticker patterns
    ticker_pattern = r'([A-Z][A-Za-z0-9\s&\.\-\']+)\s*\(([A-Z]{1,5})\)'
    
    def replace_ticker(match):
        company = match.group(1).strip()
        ticker = match.group(2)
        return f'<u><strong><u>{company} ({ticker})</u></strong></u>'
    
    # Replace tickers
    formatted_content = re.sub(ticker_pattern, replace_ticker, story_content)
    
    return formatted_content

def parse_content_to_html(content):
    """Parse the generated content and fill the HTML template"""
    if not content:
        logger.error("❌ No content to parse!")
        return None
    
    sections = {
        'DATE': datetime.now().strftime("%B %d, %Y"),
        'INTRO_PARAGRAPH': '',
        'MARKET_GRID': '',
        'CORE_STORIES': '',
        'HORIZON_SCAN_STORIES': '',
        'TRIVIA_SECTION': ''
    }
    
    current_section = None
    lines = content.split('\n')
    buffer = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Section headers
        if line == 'INTRO_PARAGRAPH:':
            current_section = 'INTRO_PARAGRAPH'
            buffer = []
            i += 1
            continue
        elif line == 'MARKET_GRID:':
            current_section = 'MARKET_GRID'
            buffer = []
            i += 1
            continue
        elif line == 'CORE_STORIES:':
            current_section = 'CORE_STORIES'
            buffer = []
            i += 1
            continue
        elif line == 'HORIZON_SCAN_STORIES:':
            current_section = 'HORIZON_SCAN_STORIES'
            buffer = []
            i += 1
            continue
        elif line == 'GAME_CHOICE:':
            current_section = 'GAME_CHOICE'
            i += 1
            continue
        
        # Process content based on current section
        if current_section == 'INTRO_PARAGRAPH':
            if line and not line.startswith('[') and not line.startswith('MARKET_GRID:'):
                paragraph_text = line
                j = i + 1
                while j < len(lines) and lines[j].strip() and not lines[j].strip().startswith('[') and not lines[j].strip().startswith('MARKET_GRID:'):
                    paragraph_text += ' ' + lines[j].strip()
                    j += 1
                
                if paragraph_text:
                    sections['INTRO_PARAGRAPH'] += f'        <p>{paragraph_text}</p>\n'
                i = j - 1
        
        elif current_section == 'MARKET_GRID':
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 3:
                    label, value, change = parts[0].strip(), parts[1].strip(), parts[2].strip()
                    change_class = 'change-positive' if change.startswith('+') else 'change-negative' if change.startswith('-') else ''
                    buffer.append(f'''
            <td>
                <span class="market-label">{label}</span>
                <span class="market-value">{value}</span>
                <span class="market-change {change_class}">{change}</span>
            </td>''')
            
            if len(buffer) == 9:
                table_html = '<tr>' + ''.join(buffer[:3]) + '</tr>\n            <tr>' + ''.join(buffer[3:6]) + '</tr>\n            <tr>' + ''.join(buffer[6:9]) + '</tr>'
                sections['MARKET_GRID'] = table_html
                buffer = []
                current_section = None
        
        elif current_section in ['CORE_STORIES', 'HORIZON_SCAN_STORIES']:
            if line and not line.startswith('['):
                story_text = line
                j = i + 1
                while j < len(lines) and lines[j].strip() and not lines[j].strip().startswith('[') and not lines[j].strip() in ['HORIZON_SCAN_STORIES:', 'GAME_CHOICE:']:
                    story_text += ' ' + lines[j].strip()
                    j += 1
                
                if story_text and len(story_text) > 50:
                    formatted_story = process_story_formatting(story_text)
                    story_html = f'<div class="story">\n            <p>{formatted_story}</p>\n        </div>'
                    
                    if current_section == 'CORE_STORIES':
                        sections['CORE_STORIES'] += '\n        ' + story_html
                    else:
                        sections['HORIZON_SCAN_STORIES'] += '\n        ' + story_html
                    
                i = j - 1
        
        i += 1
    
    # Generate simple trivia
    sections['TRIVIA_SECTION'] = """
        <div class="trivia-question">Which sector is most sensitive to regulatory changes?</div>
        <div class="trivia-options">
            <div class="trivia-option">A) Technology</div>
            <div class="trivia-option">B) Healthcare</div>
            <div class="trivia-option">C) Financial Services</div>
            <div class="trivia-option">D) Energy</div>
        </div>
        <div class="trivia-answer">
            <strong class="trivia-correct">Answer:</strong> C) Financial Services <br>
            <em>Financial services companies are highly regulated and sensitive to policy changes affecting lending, trading, and compliance requirements.</em>
        </div>
    """
    
    # Fill template
    html = HTML_TEMPLATE
    for key, value in sections.items():
        html = html.replace(f'{{{key}}}', value if value is not None else '')
    
    return html

def init_database():
    """Initialize SQLite database for storing newsletters"""
    conn = sqlite3.connect('newsletters.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS newsletters (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMP,
            html_content TEXT,
            status TEXT,
            editor_notes TEXT,
            sent_at TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_newsletter_to_db(newsletter_id, html_content):
    """Save newsletter to database"""
    conn = sqlite3.connect('newsletters.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO newsletters (id, created_at, html_content, status)
        VALUES (?, ?, ?, ?)
    ''', (newsletter_id, datetime.now(), html_content, 'draft'))
    
    conn.commit()
    conn.close()

# --- Flask Routes ---

@app.route('/')
def index():
    """Main page"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Alphaminr Newsletter Generator</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .container { background: #f8f9fa; padding: 30px; border-radius: 10px; }
            h1 { color: #2c3e50; text-align: center; }
            .btn { background: #3498db; color: white; padding: 15px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
            .btn:hover { background: #2980b9; }
            .status { margin-top: 20px; padding: 15px; border-radius: 5px; }
            .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Alphaminr Newsletter Generator</h1>
            <p style="text-align: center; color: #6c757d;">Focus: Major news headlines and government policies → Company impact analysis</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <button class="btn" onclick="generateNewsletter()">🚀 Generate Newsletter</button>
            </div>
            
            <div id="status"></div>
        </div>
        
        <script>
            async function generateNewsletter() {
                const statusDiv = document.getElementById('status');
                statusDiv.innerHTML = '<div class="status">🔄 Generating newsletter... This may take a few minutes.</div>';
                
                try {
                    const response = await fetch('/api/generate', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({})
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        statusDiv.innerHTML = `
                            <div class="status success">
                                <h3>✅ Newsletter Generated Successfully!</h3>
                                <p>Generation time: ${result.generation_time_seconds?.toFixed(2)}s</p>
                                <p>Total time: ${result.total_time_seconds?.toFixed(2)}s</p>
                                <a href="/newsletter/${result.newsletter_id}" target="_blank" style="color: #155724; font-weight: bold;">📄 View Newsletter</a>
                            </div>
                        `;
                    } else {
                        statusDiv.innerHTML = `
                            <div class="status error">
                                <h3>❌ Generation Failed</h3>
                                <p>${result.message || 'Unknown error'}</p>
                                ${result.debug ? `<p><strong>Debug:</strong> ${result.debug}</p>` : ''}
                            </div>
                        `;
                    }
                } catch (error) {
                    statusDiv.innerHTML = `
                        <div class="status error">
                            <h3>❌ Network Error</h3>
                            <p>${error.message}</p>
                        </div>
                    `;
                }
            }
        </script>
    </body>
    </html>
    """)

@app.route('/api/generate', methods=['GET', 'POST'])
def api_generate():
    """API endpoint for generating newsletters"""
    start_time = datetime.now()
    logger.info(f"🚀 Starting newsletter generation request at {start_time}")
    
    try:
        # Check environment variables
        if not BRAVE_SEARCH_API_KEY or not ANTHROPIC_API_KEY:
            error_msg = "Missing required environment variables"
            logger.error(f"❌ {error_msg}")
            return jsonify({"success": False, "error": error_msg}), 500
        
        # Generate newsletter
        generation_start = datetime.now()
        logger.info(f"⚡ Starting newsletter generation at {generation_start}")
        
        content = generate_newsletter_content()
        
        if not content:
            logger.error("❌ Failed to generate content")
            return jsonify({"success": False, "error": "Failed to generate content"}), 500
        
        # Parse content into HTML
        html_output = parse_content_to_html(content)
        
        if not html_output:
            logger.error("❌ Failed to parse content into HTML")
            return jsonify({"success": False, "error": "Failed to parse content into HTML"}), 500
        
        # Generate unique ID for this newsletter
        newsletter_id = str(uuid.uuid4())
        
        # Initialize database and save newsletter
        init_database()
        save_newsletter_to_db(newsletter_id, html_output)
        
        generation_end = datetime.now()
        generation_duration = (generation_end - generation_start).total_seconds()
        total_duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Newsletter generated successfully in {generation_duration:.2f}s")
        
        return jsonify({
            "success": True,
            "html": html_output,
            "newsletter_id": newsletter_id,
            "generation_time_seconds": generation_duration,
            "total_time_seconds": total_duration,
            "message": "Newsletter generated successfully"
        })
        
    except Exception as e:
        logger.error(f"💥 Exception during generation: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e), "type": type(e).__name__}), 500

@app.route('/api/newsletters', methods=['GET'])
def list_newsletters():
    """List all newsletters"""
    try:
        conn = sqlite3.connect('newsletters.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, created_at FROM newsletters ORDER BY created_at DESC')
        results = cursor.fetchall()
        
        conn.close()
        
        newsletters = []
        for newsletter_id, created_at in results:
            newsletters.append({
                'id': newsletter_id,
                'created_at': created_at,
                'display_date': created_at.split('T')[0] if 'T' in created_at else created_at
            })
        
        return jsonify({
            "success": True,
            "newsletters": newsletters,
            "count": len(newsletters)
        })
        
    except Exception as e:
        logger.error(f"❌ Error listing newsletters: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/newsletter/<newsletter_id>')
def view_newsletter(newsletter_id):
    """View a specific newsletter"""
    try:
        conn = sqlite3.connect('newsletters.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT html_content FROM newsletters WHERE id = ?', (newsletter_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return result[0]
        else:
            return "Newsletter not found", 404
            
    except Exception as e:
        logger.error(f"❌ Error viewing newsletter: {e}")
        return f"Error: {str(e)}", 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "brave_api_key_set": bool(BRAVE_SEARCH_API_KEY),
            "anthropic_api_key_set": bool(ANTHROPIC_API_KEY)
        }
    })

@app.route('/api/test-mcp', methods=['POST'])
def test_mcp():
    """Test MCP integration"""
    try:
        data = request.get_json()
        test_type = data.get('test_type', 'web_search')
        query = data.get('query', 'test query')
        
        client = get_mcp_client()
        if not client:
            return jsonify({"success": False, "error": "MCP client not initialized"})
        
        if test_type == 'web_search':
            result = client.web_search(query, freshness="pd")
        elif test_type == 'news_search':
            result = client.news_search(query, freshness="pd")
        else:
            return jsonify({"success": False, "error": "Invalid test type"})
        
        return jsonify({
            "success": True,
            "test_type": test_type,
            "query": query,
            "results_count": len(result.get("results", [])),
            "has_ai_summary": "ai_summary" in result
        })
        
    except Exception as e:
        logger.error(f"❌ MCP test error: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/test-search', methods=['POST'])
def test_search():
    """Test enhanced search capabilities"""
    try:
        data = request.get_json()
        search_type = data.get('search_type', 'government_policies')
        
        if search_type == 'government_policies':
            result = search_government_policies()
        elif search_type == 'economic_data':
            result = search_economic_data()
        elif search_type == 'central_bank_statements':
            result = search_central_bank_statements()
        elif search_type == 'geopolitical_developments':
            result = search_geopolitical_developments()
        else:
            return jsonify({"success": False, "error": "Invalid search type"})
        
        return jsonify({
            "success": True,
            "search_type": search_type,
            "results_count": len(result.get("results", [])),
            "sample_results": result.get("results", [])[:3]  # First 3 results
        })
        
    except Exception as e:
        logger.error(f"❌ Search test error: {e}")
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Starting Alphaminr Newsletter Generator on port {port}")
    logger.info("🎯 Focus: Major news headlines → Company impact analysis")
    app.run(host="0.0.0.0", port=port, debug=False)
