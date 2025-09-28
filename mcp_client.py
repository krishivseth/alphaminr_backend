#!/usr/bin/env python3
"""
MCP Client for Alphaminr Newsletter Generator
Uses the official Brave Search MCP Server for enhanced web search functionality
"""
import requests
import logging
import json
import subprocess
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class BraveSearchMCPClient:
    """MCP Client for Brave Search using the official MCP Server"""
    
    def __init__(self, brave_api_key: str):
        self.brave_api_key = brave_api_key
        self.mcp_process = None
        
    def _start_mcp_server(self):
        """Start the Brave Search MCP Server"""
        if self.mcp_process and self.mcp_process.poll() is None:
            return self.mcp_process
        
        try:
            # Use NPX to run the official Brave Search MCP Server
            self.mcp_process = subprocess.Popen(
                ['npx', '-y', '@brave/brave-search-mcp-server', '--transport', 'stdio'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**os.environ, 'BRAVE_API_KEY': self.brave_api_key}
            )
            logger.info("✅ Brave Search MCP Server started")
            return self.mcp_process
        except Exception as e:
            logger.error(f"❌ Failed to start MCP server: {e}")
            return None
    
    def _send_mcp_request(self, method: str, params: Dict) -> Optional[Dict]:
        """Send a request to the MCP server"""
        process = self._start_mcp_server()
        if not process:
            return None
        
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params
            }
            
            # Send request
            process.stdin.write(json.dumps(request) + '\n')
            process.stdin.flush()
            
            # Read response
            response_line = process.stdout.readline()
            if response_line:
                response = json.loads(response_line.strip())
                return response
            else:
                logger.error("❌ No response from MCP server")
                return None
                
        except Exception as e:
            logger.error(f"❌ MCP request failed: {e}")
            return None
    
    def web_search(self, query: str, count: int = 10, freshness: str = "pd") -> Dict:
        """Perform web search using Brave Search MCP Server"""
        try:
            params = {
                "name": "brave_web_search",
                "arguments": {
                    "query": query,
                    "count": count,
                    "freshness": freshness,  # Past day
                    "country": "US",
                    "search_lang": "en",
                    "safesearch": "moderate",
                    "summary": True  # Enable AI summaries
                }
            }
            
            response = self._send_mcp_request("tools/call", params)
            
            if response and "result" in response:
                return response["result"]
            else:
                logger.error(f"❌ Web search failed: {response}")
                return {"results": []}
                
        except Exception as e:
            logger.error(f"❌ Web search error: {e}")
            return {"results": []}
    
    def news_search(self, query: str, count: int = 20, freshness: str = "pd") -> Dict:
        """Search for news using Brave Search MCP Server"""
        try:
            params = {
                "name": "brave_news_search",
                "arguments": {
                    "query": query,
                    "count": count,
                    "freshness": freshness,  # Past day
                    "country": "US",
                    "search_lang": "en",
                    "safesearch": "moderate"
                }
            }
            
            response = self._send_mcp_request("tools/call", params)
            
            if response and "result" in response:
                return response["result"]
            else:
                logger.error(f"❌ News search failed: {response}")
                return {"results": []}
                
        except Exception as e:
            logger.error(f"❌ News search error: {e}")
            return {"results": []}
    
    def summarizer_search(self, summary_key: str) -> Dict:
        """Generate AI-powered summaries using Brave Search MCP Server"""
        try:
            params = {
                "name": "brave_summarizer",
                "arguments": {
                    "key": summary_key,
                    "entity_info": True,
                    "inline_references": True
                }
            }
            
            response = self._send_mcp_request("tools/call", params)
            
            if response and "result" in response:
                return response["result"]
            else:
                logger.error(f"❌ Summarizer search failed: {response}")
                return {"summary": ""}
                
        except Exception as e:
            logger.error(f"❌ Summarizer search error: {e}")
            return {"summary": ""}
    
    def search_market_data(self, query: str) -> Dict:
        """Search for market data with AI summary"""
        return self.web_search(f"{query} current price today market data", count=10, freshness="pd")
    
    def search_news_headlines(self, query: str) -> Dict:
        """Search for news headlines from past 24 hours"""
        return self.news_search(f"{query} news headlines today", count=20, freshness="pd")
    
    def search_government_policies(self, query: str) -> Dict:
        """Search for government policy announcements from past 24 hours"""
        return self.news_search(f"{query} government policy announcement today", count=15, freshness="pd")
    
    def search_economic_data(self, query: str) -> Dict:
        """Search for economic data releases from past 24 hours"""
        return self.news_search(f"{query} economic data release today", count=15, freshness="pd")
    
    def search_central_bank_statements(self, query: str) -> Dict:
        """Search for central bank statements from past 24 hours"""
        return self.news_search(f"{query} central bank statement today", count=15, freshness="pd")
    
    def get_enhanced_summary(self, web_search_result: Dict) -> str:
        """Get AI-powered summary from web search results"""
        try:
            # Check if web search result has a summary key
            if "summary" in web_search_result and "key" in web_search_result["summary"]:
                summary_key = web_search_result["summary"]["key"]
                summary_result = self.summarizer_search(summary_key)
                
                if "summary" in summary_result:
                    return summary_result["summary"]
            
            return ""
        except Exception as e:
            logger.error(f"❌ Enhanced summary error: {e}")
            return ""
    
    def cleanup(self):
        """Clean up MCP server process"""
        if self.mcp_process and self.mcp_process.poll() is None:
            self.mcp_process.terminate()
            self.mcp_process.wait()
            logger.info("✅ MCP server process cleaned up")

# Global MCP client instance
mcp_client = None

def get_mcp_client() -> Optional[BraveSearchMCPClient]:
    """Get the global MCP client instance"""
    return mcp_client

def init_mcp_client(brave_api_key: str) -> BraveSearchMCPClient:
    """Initialize the global MCP client"""
    global mcp_client
    mcp_client = BraveSearchMCPClient(brave_api_key)
    logger.info("✅ Brave Search MCP Client initialized")
    return mcp_client