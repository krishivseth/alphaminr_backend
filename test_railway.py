#!/usr/bin/env python3
"""
Test script for Railway deployment
Tests the main functionality of the Alphaminr Newsletter Generator
"""
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_health_endpoint(base_url):
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            print(f"   Environment: {data['environment']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_newsletter_generation(base_url):
    """Test newsletter generation"""
    print("🚀 Testing newsletter generation...")
    try:
        response = requests.post(
            f"{base_url}/api/generate",
            json={},
            timeout=60  # Newsletter generation can take time
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Newsletter generated successfully!")
                print(f"   Generation time: {data.get('generation_time_seconds', 0):.2f}s")
                print(f"   Newsletter ID: {data.get('newsletter_id', 'N/A')}")
                
                # Test viewing the newsletter
                newsletter_id = data.get('newsletter_id')
                if newsletter_id:
                    view_response = requests.get(f"{base_url}/newsletter/{newsletter_id}")
                    if view_response.status_code == 200:
                        print("✅ Newsletter viewing works")
                        return True
                    else:
                        print(f"❌ Newsletter viewing failed: {view_response.status_code}")
                        return False
                return True
            else:
                print(f"❌ Newsletter generation failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Newsletter generation request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Newsletter generation error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Alphaminr Newsletter Generator - Railway Deployment Test")
    print("=" * 60)
    
    # Get base URL from environment or use default
    base_url = os.getenv("RAILWAY_URL", "http://localhost:5000")
    
    if base_url == "http://localhost:5000":
        print("⚠️ Using localhost URL. Set RAILWAY_URL environment variable for remote testing.")
    
    print(f"🌐 Testing against: {base_url}")
    print()
    
    # Run tests
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Health endpoint
    if test_health_endpoint(base_url):
        tests_passed += 1
    print()
    
    # Test 2: Newsletter generation
    if test_newsletter_generation(base_url):
        tests_passed += 1
    print()
    
    # Summary
    print("📊 Test Results:")
    print(f"   Passed: {tests_passed}/{total_tests}")
    print(f"   Success rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Railway deployment is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check the logs and configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()
