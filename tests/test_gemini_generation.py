"""
Test script to verify Gemini models for legal position generation
"""
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

SYSTEM_PROMPT = """Ти - експертний юридичний асистент, який спеціалізується на аналізі судових рішень 
та формуванні правових позицій Верховного Суду України."""

def test_gemini_model(model_name: str, test_content: str):
    """Test a specific Gemini model"""
    print(f"\n{'='*80}")
    print(f"Testing model: {model_name}")
    print(f"{'='*80}\n")
    
    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        
        json_instruction = """
Відповідь ОБОВ'ЯЗКОВО має бути у форматі JSON з такою структурою:
{
    "title": "Заголовок правової позиції",
    "text": "Текст правової позиції", 
    "proceeding": "Вид провадження",
    "category": "Категорія"
}
"""
        full_content = f"{test_content}\n\n{json_instruction}"
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=full_content),
                ],
            ),
        ]
        
        # Build config based on model version
        config_params = {
            "temperature": 0,
            "max_output_tokens": 1000,
            "system_instruction": [
                types.Part.from_text(text=SYSTEM_PROMPT),
            ],
        }
        
        # Only add response_mime_type for models that support it
        if not model_name.startswith("gemini-3"):
            config_params["response_mime_type"] = "application/json"
            print("✓ Using response_mime_type='application/json'")
        else:
            print("✓ NOT using response_mime_type (Gemini 3 model)")
        
        generate_content_config = types.GenerateContentConfig(**config_params)
        
        print(f"Sending request to {model_name}...")
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=generate_content_config,
        )
        
        response_text = response.text
        print(f"\n📝 Raw response (first 300 chars):\n{response_text[:300]}...\n")
        
        # Try to parse JSON
        text_to_parse = response_text.strip()
        
        # Remove markdown code blocks if present
        if text_to_parse.startswith("```json"):
            text_to_parse = text_to_parse[7:]
            print("✓ Removed ```json wrapper")
        elif text_to_parse.startswith("```"):
            text_to_parse = text_to_parse[3:]
            print("✓ Removed ``` wrapper")
        
        if text_to_parse.endswith("```"):
            text_to_parse = text_to_parse[:-3]
            print("✓ Removed trailing ```")
        
        text_to_parse = text_to_parse.strip()
        
        # Try to find JSON object in the text
        start_idx = text_to_parse.find('{')
        end_idx = text_to_parse.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            text_to_parse = text_to_parse[start_idx:end_idx + 1]
            print(f"✓ Extracted JSON from position {start_idx} to {end_idx}")
        
        json_response = json.loads(text_to_parse)
        
        print(f"\n✅ Successfully parsed JSON!")
        print(f"📋 Parsed response:")
        print(json.dumps(json_response, ensure_ascii=False, indent=2))
        
        # Check required fields
        required_fields = ["title", "text", "proceeding", "category"]
        missing_fields = [field for field in required_fields if field not in json_response]
        
        if missing_fields:
            print(f"\n⚠️  Missing fields: {missing_fields}")
        else:
            print(f"\n✅ All required fields present!")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON parsing error: {str(e)}")
        print(f"Failed to parse: {text_to_parse[:200]}...")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Test content
    test_content = """
Проаналізуй це судове рішення та сформуй правову позицію:

Суд встановив, що позивач звернувся з позовом про стягнення заборгованості по заробітній платі.
Відповідач заперечував проти позову, посилаючись на відсутність трудових відносин.
Суд встановив наявність трудових відносин та задовольнив позов.
"""
    
    print("="*80)
    print("GEMINI MODELS COMPARISON TEST")
    print("="*80)
    
    models = [
        "gemini-2.0-flash-exp",
        "gemini-3-flash-preview"
    ]
    
    results = {}
    for model in models:
        results[model] = test_gemini_model(model, test_content)
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    for model, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{model}: {status}")
