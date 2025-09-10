#!/usr/bin/env python3
"""
Gemini API Connection Test for OpportunityDetection backend
"""

import os
import asyncio
import sys
from datetime import datetime

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    import google.generativeai as genai
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Missing required packages: {e}")
    print("Please install: pip install google-generativeai python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()

def test_gemini_api():
    """Test Gemini API connection and basic functionality"""
    
    print("🔍 Testing Gemini API Connection...")
    print("-" * 50)
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment variables")
        print("🔧 Please set GOOGLE_API_KEY in your .env file")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]} (masked)")
    
    try:
        # Configure Gemini API
        print("\n1. Configuring Gemini API...")
        genai.configure(api_key=api_key)
        print("✅ API configured successfully")
        
        # List available models
        print("\n2. Listing available models...")
        models = []
        try:
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    models.append(model.name)
                    print(f"   - {model.name}")
            
            if not models:
                print("⚠️ No models with generateContent support found")
                return False
            
        except Exception as e:
            print(f"⚠️ Could not list models (but API might still work): {e}")
        
        # Test model creation
        print("\n3. Creating model instance...")
        model_name = "gemini-1.5-pro"
        model = genai.GenerativeModel(model_name)
        print(f"✅ Model '{model_name}' created successfully")
        
        # Test simple generation
        print("\n4. Testing content generation...")
        test_prompt = "Hello! Please respond with 'Gemini API is working correctly' to confirm the connection."
        
        try:
            response = model.generate_content(test_prompt)
            
            if response and response.text:
                print("✅ Content generation successful!")
                print(f"Response: {response.text.strip()}")
                
                # Test with a business-related prompt similar to what market_analyzer uses
                print("\n5. Testing business analysis prompt...")
                business_prompt = """
                Analyze this business concept briefly:
                - Company: TechStart
                - Industry: Software Development
                - Location: Paris
                
                Provide a short market analysis in JSON format with market_size and growth_rate.
                """
                
                business_response = model.generate_content(business_prompt)
                if business_response and business_response.text:
                    print("✅ Business analysis prompt successful!")
                    print(f"Response length: {len(business_response.text)} characters")
                    print(f"Response preview: {business_response.text[:200]}...")
                else:
                    print("⚠️ Business analysis prompt returned empty response")
                
            else:
                print("❌ Content generation returned empty response")
                return False
                
        except Exception as e:
            print(f"❌ Content generation failed: {e}")
            print(f"Error type: {type(e).__name__}")
            
            # Check for specific error types
            if "quota" in str(e).lower():
                print("💡 This appears to be a quota/billing issue")
                print("   - Check your Google Cloud billing account")
                print("   - Verify Gemini API quota limits")
            elif "permission" in str(e).lower():
                print("💡 This appears to be a permissions issue")
                print("   - Verify API key has Gemini API access")
                print("   - Check Google Cloud project settings")
            elif "safety" in str(e).lower():
                print("💡 Content was blocked by safety filters")
                print("   - Try a different prompt")
            
            return False
        
        # Test rate limiting awareness
        print("\n6. Testing API response metadata...")
        try:
            if hasattr(response, 'prompt_feedback'):
                print(f"   - Prompt feedback: {response.prompt_feedback}")
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    print(f"   - Finish reason: {candidate.finish_reason}")
                if hasattr(candidate, 'safety_ratings'):
                    print(f"   - Safety ratings available: {len(candidate.safety_ratings)} ratings")
        except Exception as e:
            print(f"   - Could not access response metadata: {e}")
        
        print("\n" + "="*50)
        print("🎉 GEMINI API TEST COMPLETED SUCCESSFULLY!")
        print("✅ API connection is working")
        print("✅ Content generation is functional")
        print("✅ Business analysis prompts work")
        print("✅ Ready for use in OpportunityDetection backend")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Gemini API test failed!")
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        
        # Provide specific troubleshooting based on error
        error_str = str(e).lower()
        if "api key" in error_str:
            print("\n🔧 API Key Issues:")
            print("1. Verify GOOGLE_API_KEY is set correctly in .env")
            print("2. Check if the API key is valid and not expired")
            print("3. Ensure the key has Gemini API permissions")
        elif "network" in error_str or "connection" in error_str:
            print("\n🔧 Network Issues:")
            print("1. Check internet connection")
            print("2. Verify firewall settings")
            print("3. Try again in a moment")
        elif "quota" in error_str or "billing" in error_str:
            print("\n🔧 Quota/Billing Issues:")
            print("1. Check Google Cloud billing account")
            print("2. Verify Gemini API quotas")
            print("3. Check usage limits")
        
        return False


if __name__ == "__main__":
    print("Starting Gemini API Test for OpportunityDetection...")
    print(f"Timestamp: {datetime.now()}")
    
    success = test_gemini_api()
    
    if success:
        print("\n🚀 Gemini API is ready for OpportunityDetection!")
        sys.exit(0)
    else:
        print("\n⚠️ Gemini API issues detected")
        print("Please resolve the issues above before using market analysis tools")
        sys.exit(1)
