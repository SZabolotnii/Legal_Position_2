import os
import anthropic
client = anthropic.Anthropic()
for effort in ["low", "none", "high", "xhigh"]:
    try:
        client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            temperature=1,
            messages=[{"role": "user", "content": "hi"}],
            thinking={"type": "adaptive"},
            output_config={"effort": effort}
        )
        print(f"SUCCESS effort: {effort}")
    except Exception as e:
        print(f"Error effort {effort}: {str(e)}")
