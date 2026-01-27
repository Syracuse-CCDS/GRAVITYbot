"""
GRAVITYbot LLM Client
---------------------
Azure OpenAI client abstraction.
"""
import os
import sys

import openai

# Add project root to path for config import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config


class LLMClient:
    """Singleton client for Azure OpenAI."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def initialize(self):
        if self._initialized:
            return self
        
        self._client = openai.AzureOpenAI(
            api_key=config.AZURE_OPENAI_API_KEY,
            api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT
        )
        self._model = config.AZURE_OPENAI_DEPLOYMENT
        self._initialized = True
        return self
    
    def generate(self, messages: list, **kwargs) -> str:
        """
        Generate a completion from the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            **kwargs: Additional arguments passed to the API (temperature, max_tokens, etc.)
        
        Returns:
            The generated text response
        """
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content
    
    def is_available(self) -> bool:
        """Test that the Azure OpenAI connection is working."""
        try:
            self._client.models.list()
            return True
        except Exception:
            return False