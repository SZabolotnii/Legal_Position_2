"""
Test script to verify Google Genai API integration
"""
import os
from google import genai
from google.genai import types


def test_gemini_api():
    """Test the new Gemini API"""
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        print("⚠️  GEMINI_API_KEY not found in environment variables")
        print("Set it in your .env file to test Gemini integration")
        return False
    
    try:
        client = genai.Client(api_key=api_key)
        
        # Test with a simple prompt
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="Say 'Hello from Gemini!' in JSON format: {\"message\": \"...\"}"),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=0,
            max_output_tokens=100,
            response_mime_type="application/json",
        )

        print("🔄 Testing Gemini API connection...")
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=contents,
            config=generate_content_config,
        )
        
        print("✅ Gemini API test successful!")
        print(f"Response: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Gemini API test failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Google Gemini API Test")
    print("=" * 60)
    test_gemini_api()
