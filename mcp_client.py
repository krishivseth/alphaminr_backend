#!/usr/bin/env python3
"""
MCP Client for Alphaminr Newsletter Generator
Provides MCP (Model Context Protocol) integration for web search functionality
"""
import requests
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class MCPClient:
    """MCP Client for web search functionality"""
    
    def __init__(self, brave_api_key: str):
        self.brave_api_key = brave_api_key
        self.base_url = "https://api.search.brave.com/res/v1"
        
    def web_search(self, query: str, count: int = 10) -> Dict:
        """Perform web search using Brave Search API"""
        try:
            url = f"{self.base_url}/web/search"
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.brave_api_key
            }
            params = {
                "q": query,
                "count": count,
                "freshness": "pd",  # Past day
                "country": "US",
                "search_lang": "en",
                "safesearch": "moderate"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"❌ Web search error: {e}")
            return {"results": []}
    
    def news_search(self, query: str, count: int = 10) -> Dict:
        """Perform news search using Brave Search API"""
        try:
            url = f"{self.base_url}/news/search"
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.brave_api_key
            }
            params = {
                "q": query,
                "count": count,
                "freshness": "pd",  # Past day
                "country": "US",
                "search_lang": "en",
                "safesearch": "moderate"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"❌ News search error: {e}")
            return {"results": []}
    
    def search_market_data(self, query: str) -> Dict:
        """Search for market data"""
        return self.web_search(f"{query} current price today market data")
    
    def search_news_headlines(self, query: str) -> Dict:
        """Search for news headlines"""
        return self.news_search(f"{query} news headlines today")
    
    def search_government_policies(self, query: str) -> Dict:
        """Search for government policy announcements"""
        return self.news_search(f"{query} government policy announcement today")

# Global MCP client instance
mcp_client = None

def get_mcp_client() -> Optional[MCPClient]:
    """Get the global MCP client instance"""
    return mcp_client

def init_mcp_client(brave_api_key: str) -> MCPClient:
    """Initialize the global MCP client"""
    global mcp_client
    mcp_client = MCPClient(brave_api_key)
    logger.info("✅ MCP Client initialized")
    return mcp_client
