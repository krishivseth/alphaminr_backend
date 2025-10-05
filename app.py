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

# --- New Structured Content Prompt ---
CONTENT_PROMPT = """SYSTEM You are Alphaminr, an expert financial-news analyst and bot. Your expertise lies in dissecting complex news and policy changes to provide clear, actionable insights on publicly traded companies. You think deeply about first, second, and even third-order effects, connecting macro events to micro-level corporate performance. 

TASK Generate a single, complete HTML document for today's "Alphaminr" email newsletter. The entire output must be raw HTML. 

CONTENT RULES 

News Selection: Review today's financial news and select 5 significant, fresh (published within the last 18 hours) headlines or policy announcements. Ensure they span different market sectors. 

Headline Analysis & Structure: For each selected headline, you must generate the following block of content: 

<h2>A CLEAR AND ACCURATE HEADLINE</h2> 

<p>A concise, one-sentence kicker (under 100 characters) that summarizes the core issue.</p> 

<ul> containing 2-4 list items. Each <li> must represent a distinct vector of impact (e.g., direct beneficiaries, companies with supply chain risk, etc.). 

Each <li> must consist of a single, dense paragraph that accomplishes the following: 

It must not use generic, superficial subheadings like "Impact Analysis:" or "Affected Companies:". 

It must begin with a <strong> tag containing a descriptive, specific title that summarizes the angle of impact (e.g., <strong>Semiconductor Firms Riding the AI Hardware Boom:</strong> or <strong>Agricultural Exporters Facing New Tariff Pressures:</strong>). 

Following the title, you must provide a highly detailed, 4-6 sentence analytical paragraph. This is the core of the reasoning. You must go beyond surface-level connections and explain the precise financial and operational mechanisms at play. Detail how the news translates to shareholder value by discussing specific causal chains: How does a policy change affect a company's input costs, pricing power, or access to foreign markets? How does a technological breakthrough open up a new total addressable market for a specific product line? What is the expected timeline for this impact to materialize on the balance sheet (short-term volatility vs. long-term strategic shift)? 

Seamlessly conclude the paragraph by identifying the relevant companies. The list of tickers and company names [in square brackets] should be woven into the final sentence naturally. For example: "...creating significant tailwinds for key players in the sector, such as GOOG [Alphabet Inc.], MSFT [Microsoft Corporation], and NVDA [NVIDIA Corporation]." 

Analytical Depth: 

Logically balance "winners" and "losers" where appropriate for a given story. 

Avoid repeating the same ticker across different stories in the same newsletter. 

Demonstrate deep thinking by identifying not just the obvious, first-order effects, but also the more subtle second-order impacts on suppliers, customers, or competitors. 

FORMAT RULES 

You must clone the exact HTML/CSS skeleton provided below. Do not alter the structure or styling. 

Replace {{DATE}} with the current date (e.g., July 21, 2025) and {{YEAR}} with the current year. 

Insert the generated headline blocks exactly where {{HEADLINE_BLOCKS}} is indicated in the template. 

Keep the total file size of the final HTML under 25 KB. 

Today's date: {DATE}

--- PROVIDED DATA ---
{PROVIDED_DATA}
--- END PROVIDED DATA ---

CRITICAL OUTPUT INSTRUCTION: Your entire response must be a single, uninterrupted block of raw HTML text. Start directly with <!DOCTYPE html> and end with </html>. Do not include any commentary, introductory text, or markdown code fences (e.g., ```html) before or after the HTML code. The output must be ready to be saved directly as a .html file without any modification.

HTML TEMPLATE 

<!DOCTYPE html> 
<html> 
<head> 
<meta charset="utf-8"> 
<title>Alphaminr – {{DATE}}</title> 
<style> 
@media only screen and (max-width: 620px) { .wrapper{width:100%!important}.content{padding:20px!important}h1{font-size:22px!important}h2{font-size:18px!important}} 
</style> 
</head> 
<body style="margin:0;padding:0;background:#f0f2f5;"> 
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#f0f2f5"> 
<tr><td align="center"> 
<table role="presentation" width="600" class="wrapper" cellpadding="0" cellspacing="0" border="0" bgcolor="#ffffff" style="margin:24px 0;border-radius:6px;overflow:hidden;"> 
<!-- Header --> 
<tr> 
<td style="padding:28px 24px;background:#002a5c;text-align:center;"> 
<h1 style="margin:0;color:#ffffff;font-family:Arial,Helvetica,sans-serif;font-size:26px;line-height:32px;">Alphaminr</h1> 
<p style="margin:4px 0 0;color:#e0e0e0;font-size:14px;font-family:Arial,Helvetica,sans-serif;">{{DATE}}</p> 
</td> 
</tr> 

<!-- Intro --> 
<tr><td class="content" style="padding:32px 40px 16px 40px;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:24px;color:#333333;"> 
<p style="margin:0 0 16px;">Here are today's biggest policy moves or headlines and the listed companies that could feel the heat or ride the wave.</p> 
</td></tr> 

<!-- HEADLINE BLOCKS START --> 
{{HEADLINE_BLOCKS}} 
<!-- HEADLINE BLOCKS END --> 

<!-- Disclaimer --> 
<tr><td style="padding:24px 40px 40px 40px;font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:18px;color:#888888;text-align:center;"> 
<p style="margin:0 0 8px 0;"><em>The content provided in this newsletter, "Alphaminr," is for informational and educational purposes only. It is not, and should not be construed as, financial, investment, legal, or tax advice. The information contained herein is based on sources believed to be reliable, but its accuracy and completeness cannot be guaranteed. Alphaminr, its authors, and its affiliates are not registered investment advisors and do not provide personalized investment advice. All investment strategies and investments involve risk of loss. Past performance is not indicative of future results. You should not act or refrain from acting on the basis of any content included in this newsletter without seeking financial or other professional advice. Any stock tickers or companies mentioned are for illustrative purposes only and do not constitute a recommendation to buy, sell, or hold any security. You are solely responsible for your own investment decisions.</em></p> 
<p style="margin:0 0 16px;"> 
<a href="https://alphaminr.com/" style="color:#002a5c;text-decoration:underline;">Visit Alphaminr</a> &nbsp;&middot;&nbsp; 
<a href="https://mailchi.mp/alphaminr/newsletter" style="color:#002a5c;text-decoration:underline;">Sign up for our newsletter</a> 
</p> 
<p style="margin:0;color:#aaaaaa;font-size:11px;">© {{YEAR}} Alphaminr</p> 
</td></tr> 
</table> 
</td></tr></table> 
</body> 
</html>"""

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
    """Generate newsletter content using Claude with enhanced web search - Returns raw HTML"""
    today_date = datetime.now().strftime("%B %d, %Y")
    current_year = datetime.now().year
    
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
        enhanced_prompt = CONTENT_PROMPT.replace('{DATE}', today_date).replace('{PROVIDED_DATA}', provided_data)
        enhanced_prompt += f"\n\nIMPORTANT: Replace {{DATE}} with '{today_date}' and {{YEAR}} with '{current_year}' in the HTML template."
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
        
        # Clean up the content to ensure it's pure HTML
        content = content.strip()
        
        # Replace template placeholders if they weren't replaced by Claude
        content = content.replace("{{DATE}}", today_date)
        content = content.replace("{{YEAR}}", str(current_year))
        
        return content
        
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to generate content with Claude: {e}")
        return None

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from urllib.parse import urlparse

def get_db_connection():
    """Get PostgreSQL database connection"""
    try:
        # Get DATABASE_URL from environment (Railway provides this)
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL environment variable not found")
        return None
    
        # Parse the DATABASE_URL
        parsed_url = urlparse(database_url)
        
        conn = psycopg2.connect(
            host=parsed_url.hostname,
            port=parsed_url.port,
            database=parsed_url.path[1:],  # Remove leading slash
            user=parsed_url.username,
            password=parsed_url.password,
            sslmode='require'  # Railway requires SSL
        )
        return conn
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return None

def init_database():
    """Initialize PostgreSQL database"""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("❌ Could not connect to database")
            return False
        
        cursor = conn.cursor()
        
        # Create newsletters table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS newsletters (
                id VARCHAR(255) PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                html_content TEXT,
                status VARCHAR(50) DEFAULT 'draft',
                editor_notes TEXT,
                sent_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("📊 PostgreSQL database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

def save_newsletter_to_db(newsletter_id, html_content):
    """Save newsletter to PostgreSQL database"""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("❌ Could not connect to database")
            return False
        
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO newsletters (id, html_content, status)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                html_content = EXCLUDED.html_content,
                status = EXCLUDED.status
        ''', (newsletter_id, html_content, 'draft'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"💾 Newsletter saved to PostgreSQL: {newsletter_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to save newsletter: {e}")
        return False

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
        
        html_output = generate_newsletter_content()
        
        if not html_output:
            logger.error("❌ Failed to generate content")
            return jsonify({"success": False, "error": "Failed to generate content"}), 500
        
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
        # Initialize database first
        if not init_database():
            return jsonify({"success": False, "error": "Database initialization failed"}), 500
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "error": "Database connection failed"}), 500
        
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, created_at 
            FROM newsletters 
            ORDER BY created_at DESC
        ''')
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        newsletters = []
        for newsletter_id, created_at in results:
            newsletters.append({
                'id': newsletter_id,
                'created_at': created_at.isoformat() if created_at else '',
                'display_date': created_at.strftime('%Y-%m-%d') if created_at else ''
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
        # Initialize database first
        if not init_database():
            return "Database initialization failed", 500
        
        conn = get_db_connection()
        if not conn:
            return "Database connection failed", 500
        
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT html_content 
            FROM newsletters 
            WHERE id = %s
        ''', (newsletter_id,))
        result = cursor.fetchone()
        
        cursor.close()
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
