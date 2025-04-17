import os
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

class LLMClient:
    """Client for LLM API interactions"""
    
    def __init__(self, api_key=None):
        """Initialize with API key"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
    
    def analyze_with_gpt4(self, prompt, max_tokens=1000, temperature=0.2):
        """
        Analyze text with GPT-4
        
        Args:
            prompt: Text prompt for analysis
            max_tokens: Maximum tokens in response
            temperature: Temperature parameter (0-1)
            
        Returns:
            Response text
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error in GPT-4 analysis: {str(e)}")
            raise

# Create a global instance
_llm_client = None

def get_llm_client():
    """Get or create LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

def analyze_with_gpt4(prompt, max_tokens=1000, temperature=0.2):
    """Wrapper function for GPT-4 analysis"""
    client = get_llm_client()
    return client.analyze_with_gpt4(prompt, max_tokens, temperature) 