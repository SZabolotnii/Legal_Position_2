#!/usr/bin/env python3
import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

def test_rest():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    url = "https://api.anthropic.com/v1/messages"
    
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "output-128k-2025-02-19", # test if needed
        "content-type": "application/json"
    }

    payload = {
        "model": "claude-opus-4-6",
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": "Write a short poem about justice in 4 lines."}],
        "temperature": 1.0,
        "thinking": {"type": "adaptive"}
    }
    
    # Also test effort
    payload_effort = {
        "model": "claude-opus-4-6",
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": "Write a short poem about justice in 4 lines."}],
        "temperature": 1.0,
        "thinking": {"type": "adaptive", "effort": "low"}
    }
    
    client = httpx.Client(timeout=30.0)
    print("Testing adaptive without effort...")
    r = client.post(url, headers=headers, json=payload)
    print("Status:", r.status_code)
    if r.status_code != 200:
        print(r.json())
        
    print("\nTesting adaptive with effort parameter...")
    r = client.post(url, headers=headers, json=payload_effort)
    print("Status:", r.status_code)
    if r.status_code != 200:
        print(r.json())
        
if __name__ == "__main__":
    test_rest()
