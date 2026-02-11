"""
Test script to verify Claude 4.5 models with thinking mode
"""
import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()

SYSTEM_PROMPT = """Ти - експертний юридичний асистент, який спеціалізується на аналізі судових рішень 
та формуванні правових позицій Верховного Суду України."""

def test_claude_model(model_name: str, with_thinking: bool = False):
    """Test a specific Claude model"""
    print(f"\n{'='*80}")
    print(f"Testing model: {model_name}")
    print(f"Thinking mode: {'ENABLED' if with_thinking else 'DISABLED'}")
    print(f"{'='*80}\n")
    
    try:
        client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        
        content = """
Проаналізуй це судове рішення та сформуй правову позицію у форматі JSON:
{
    "title": "Заголовок",
    "text": "Текст позиції",
    "proceeding": "Вид провадження",
    "category": "Категорія"
}

Судове рішення:
Суд встановив, що позивач звернувся з позовом про стягнення заборгованості по заробітній платі.
Відповідач заперечував проти позову, посилаючись на відсутність трудових відносин.
Суд встановив наявність трудових відносин та задовольнив позов.
"""
        
        messages = [{
            "role": "user",
            "content": f"{SYSTEM_PROMPT}\n\n{content}"
        }]
        
        # Prepare message parameters
        message_params = {
            "model": model_name,
            "max_tokens": 10000,
            "messages": messages,
            "temperature": 0
        }
        
        # Add thinking if enabled
        if with_thinking:
            message_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": 5000
            }
            print("✓ Thinking enabled with 5000 tokens budget")
        
        print(f"Sending request to {model_name}...")
        response = client.messages.create(**message_params)
        
        # Extract all text from response
        response_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                response_text += block.text
                print(f"📝 Block type: {block.type}")
        
        print(f"\n📄 Response (first 500 chars):\n{response_text[:500]}...\n")
        
        # Try to parse JSON
        import json
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
    print("="*80)
    print("CLAUDE 4.5 MODELS TEST")
    print("="*80)
    
    models = [
        "claude-sonnet-4-5-20250929",
        "claude-haiku-4-5-20251001",
        "claude-opus-4-5-20251101"
    ]
    
    results = {}
    
    # Test without thinking
    for model in models:
        results[f"{model} (no thinking)"] = test_claude_model(model, with_thinking=False)
    
    # Test with thinking (only Sonnet)
    results[f"{models[0]} (with thinking)"] = test_claude_model(models[0], with_thinking=True)
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    for model, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{model}: {status}")
