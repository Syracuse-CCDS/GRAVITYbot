# test/test_openai_access.py
"""Test Azure OpenAI connectivity."""
import os
import sys

from dotenv import find_dotenv, load_dotenv

# Add _src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '_src'))

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
    load_dotenv(find_dotenv())
    test_api_connection()