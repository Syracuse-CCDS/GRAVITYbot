"""
GRAVITYbot LLM Client
---------------------
Azure OpenAI client abstraction with logging and config-driven defaults.
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import openai

# Add project root to path for config import
# TODO: Remove when proper packaging is implemented
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config


class LLMError(Exception):
    """Raised when LLM operations fail."""
    pass


class LLMClient:
    """
    Azure OpenAI client with automatic initialization, logging, and defaults.
    
    Usage:
        client = LLMClient()
        response = client.generate("Summarize this text", system_prompt="You are a helpful assistant.")
        
    Or use the module-level convenience function:
        response = llm_client.generate("Summarize this text")
    """
    
    _instance: Optional["LLMClient"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_client()
        return cls._instance
    
    def _init_client(self):
        """Initialize the Azure OpenAI client."""
        self._client = openai.AzureOpenAI(
            api_key=config.AZURE_OPENAI_API_KEY,
            api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
        )
        self._model = config.AZURE_OPENAI_DEPLOYMENT
        self._default_log_path = config.OUTPUT_FOLDER_PATH / "llm_calls.log"
    
    def generate(
        self,
        user_prompt: str,
        system_prompt: str = "You are a helpful assistant.",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        log_call: bool = True,
        log_file: Optional[str] = None,
    ) -> str:
        """
        Generate a completion from the LLM.
        
        Args:
            user_prompt: The user message content
            system_prompt: System message defining assistant behavior
            temperature: Sampling temperature (default from config.LLM_TEMPERATURE)
            max_tokens: Maximum response tokens (default from config.LLM_MAX_TOKENS)
            log_call: Whether to log the prompt/response to file
            log_file: Log filename (in OUTPUT_FOLDER_PATH). Defaults to "llm_calls.log".
                      Each unique log file is overwritten per run.
        
        Returns:
            The generated text response
        
        Raises:
            LLMError: If the API call fails
        """
        temperature = temperature if temperature is not None else config.LLM_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else config.LLM_MAX_TOKENS
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            result = response.choices[0].message.content
        except openai.APIError as e:
            raise LLMError(f"Azure OpenAI API error: {e}") from e
        
        if log_call:
            log_path = config.OUTPUT_FOLDER_PATH / log_file if log_file else self._default_log_path
            self._log_interaction(system_prompt, user_prompt, result, log_path)
        
        return result
    
    def generate_from_messages(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        log_call: bool = True,
        log_file: Optional[str] = None,
    ) -> str:
        """
        Generate a completion from a pre-built message list.
        
        Use this when you need more control over the message structure
        (e.g., multi-turn conversations).
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (default from config.LLM_TEMPERATURE)
            max_tokens: Maximum response tokens (default from config.LLM_MAX_TOKENS)
            log_call: Whether to log the prompt/response to file
            log_file: Log filename (in OUTPUT_FOLDER_PATH). Defaults to "llm_calls.log".
            
        Returns:
            The generated text response
            
        Raises:
            LLMError: If the API call fails
        """
        temperature = temperature if temperature is not None else config.LLM_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else config.LLM_MAX_TOKENS
        
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            result = response.choices[0].message.content
        except openai.APIError as e:
            raise LLMError(f"Azure OpenAI API error: {e}") from e
        
        if log_call:
            # Extract system/user for logging (best effort)
            sys_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
            user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
            log_path = config.OUTPUT_FOLDER_PATH / log_file if log_file else self._default_log_path
            self._log_interaction(sys_msg, user_msg, result, log_path)
        
        return result
    
    def _log_interaction(self, system_prompt: str, user_prompt: str, response: str, log_path: Path):
        """Write prompt/response to log file (overwrites)."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = f"""
{'='*60}
TIMESTAMP: {timestamp}
{'='*60}
SYSTEM PROMPT:
{system_prompt}
{'='*60}
USER PROMPT ({len(user_prompt)} chars):
{user_prompt}
{'='*60}
RESPONSE ({len(response)} chars):
{response}
{'='*60}
        """

        with open(log_path, "w", encoding="utf-8") as f:
            f.write(log_entry)


    def _log_interaction2(self, system_prompt: str, user_prompt: str, response: str, log_path: Path):
        """Write prompt/response to log file (overwrites)."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Truncate long prompts in log for readability
        max_log_len = 2000
        user_display = (
            user_prompt[:max_log_len] + f"... [truncated, {len(user_prompt)} chars total]"
            if len(user_prompt) > max_log_len 
            else user_prompt
        )
        
        log_entry = f"""
{'='*60}
TIMESTAMP: {timestamp}
{'='*60}
SYSTEM PROMPT:
{system_prompt}

USER PROMPT ({len(user_prompt)} chars):
{user_display}

RESPONSE ({len(response)} chars):
{response}
"""
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(log_entry)
    
    def test_connection(self) -> bool:
        """
        Test that the Azure OpenAI connection is working.
        
        Returns:
            True if a test completion succeeds, False otherwise
        """
        try:
            self.generate(
                user_prompt="Say 'ok'",
                system_prompt="Respond with only the word requested.",
                max_tokens=5,
                log_call=False,
            )
            return True
        except LLMError:
            return False


# ---------------------
# Module-level convenience functions
# ---------------------

def generate(
    user_prompt: str, 
    system_prompt: str = "You are a helpful assistant.", 
    **kwargs
) -> str:
    """
    Module-level convenience function for simple LLM calls.
    
    Usage:
        import llm_client
        response = llm_client.generate("Summarize this text", "You are a summarizer.")
    """
    return LLMClient().generate(user_prompt, system_prompt, **kwargs)


def generate_from_messages(messages: list[dict], **kwargs) -> str:
    """
    Module-level convenience function for message-based LLM calls.
    
    Usage:
        import llm_client
        response = llm_client.generate_from_messages([
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
        ])
    """
    return LLMClient().generate_from_messages(messages, **kwargs)


def test_connection() -> bool:
    """Module-level convenience function to test the connection."""
    return LLMClient().test_connection()