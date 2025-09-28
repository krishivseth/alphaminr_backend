#!/usr/bin/env python3
"""
Test script for Railway deployment with enhanced MCP integration
Tests the Brave Search MCP Server integration
"""
import os
import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Railway URL from environment
RAILWAY_URL = os.getenv("RAILWAY_URL", "http://localhost:5000")

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{RAILWAY_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_mcp_integration():
    """Test MCP integration"""
    print("🔍 Testing MCP integration...")
    try:
        # Test web search
        response = requests.post(f"{RAILWAY_URL}/api/test-mcp", 
                              json={"test_type": "web_search", "query": "S&P 500 current price"},
                              timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ MCP web search test passed")
                return True
            else:
                print(f"❌ MCP web search test failed: {result.get('error')}")
                return False
        else:
            print(f"❌ MCP test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ MCP test error: {e}")
        return False

def test_newsletter_generation():
    """Test newsletter generation with enhanced MCP"""
    print("🔍 Testing newsletter generation with enhanced MCP...")
    try:
        response = requests.post(f"{RAILWAY_URL}/api/generate", 
                              json={},
                              timeout=120)  # Longer timeout for generation
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Newsletter generation test passed")
                print(f"📄 Newsletter ID: {result.get('newsletter_id')}")
                return True
            else:
                print(f"❌ Newsletter generation test failed: {result.get('error')}")
                return False
        else:
            print(f"❌ Newsletter generation test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Newsletter generation test error: {e}")
        return False

def test_enhanced_search():
    """Test enhanced search capabilities"""
    print("🔍 Testing enhanced search capabilities...")
    try:
        # Test government policies search
        response = requests.post(f"{RAILWAY_URL}/api/test-search", 
                              json={"search_type": "government_policies"},
                              timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Enhanced search test passed")
                return True
            else:
                print(f"❌ Enhanced search test failed: {result.get('error')}")
                return False
        else:
            print(f"❌ Enhanced search test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced search test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Railway deployment with enhanced MCP integration")
    print("=" * 60)
    print(f"Testing URL: {RAILWAY_URL}")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health),
        ("MCP Integration", test_mcp_integration),
        ("Enhanced Search", test_enhanced_search),
        ("Newsletter Generation", test_newsletter_generation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        if test_func():
            passed += 1
        time.sleep(2)  # Wait between tests
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Railway deployment is working correctly.")
    else:
        print("❌ Some tests failed. Check the logs above for details.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()