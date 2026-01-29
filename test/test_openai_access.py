# test/test_openai_access.py
"""Test Azure OpenAI connectivity."""
import os
import sys

# Add project root to path for config import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '_src')))

import config
import llm_client


def test_api_connection():
    client = llm_client.LLMClient().initialize()
    
    if not client.is_available():
        print("✗ Azure OpenAI connection failed.")
        sys.exit(1)
    
    print("✓ Azure OpenAI connection successful.")
    
    # Optional: test actual generation
    response = client.generate([
        {"role": "user", "content": "Say 'hello' and nothing else."}
    ])
    print(f"✓ Generation test: {response}")
    

if __name__ == "__main__":
    test_api_connection()