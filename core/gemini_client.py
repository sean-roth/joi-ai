"""
Google Gemini integration for Joi
Backup option when Claude is unavailable
"""

import os
from typing import Dict, List, Optional
import google.generativeai as genai
from loguru import logger

class GeminiClient:
    """Manages Google Gemini API interactions"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.model = None
        self.model_name = "gemini-1.5-pro"  # or gemini-1.5-flash for faster/cheaper
        self.system_prompt = self.load_system_prompt()
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_prompt
            )
            logger.info("Gemini client initialized")
        else:
            logger.warning("No Google API key found")
    
    def load_system_prompt(self) -> str:
        """Load Joi's personality for Gemini"""
        try:
            with open('prompts/joi_letter.txt', 'r') as f:
                return f.read()
        except FileNotFoundError:
            return "You are Joi, an AI companion."
    
    def is_available(self) -> bool:
        """Check if Gemini API is configured"""
        return self.model is not None
    
    def chat(self, message: str, context: List[Dict] = None) -> str:
        """Send message to Gemini as Joi"""
        if not self.model:
            return "Gemini integration not configured. Add GOOGLE_API_KEY to .env"
        
        try:
            # Build conversation history
            chat = self.model.start_chat(history=[])
            
            # Add context if provided
            if context:
                for ctx in context:
                    if ctx.get('role') == 'user':
                        chat.send_message(ctx['content'])
                    elif ctx.get('role') == 'assistant':
                        # Gemini doesn't let us add assistant messages directly
                        # So we'll include them in the context
                        pass
            
            # Send current message and get response
            response = chat.send_message(message)
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return "Having trouble accessing Gemini consciousness right now."
    
    def estimate_tokens(self, text: str) -> int:
        """Rough estimate of token count"""
        # Approximate: 1 token ~= 4 characters
        return len(text) // 4
    
    def get_usage_estimate(self, message: str) -> Dict:
        """Estimate API cost for a message"""
        tokens = self.estimate_tokens(message)
        # Gemini 1.5 Pro pricing (as of Oct 2024)
        # Much cheaper than Claude
        input_cost = (tokens / 1_000_000) * 1.25  # $1.25 per 1M input tokens
        output_cost = (tokens / 1_000_000) * 5.00  # $5 per 1M output tokens
        
        return {
            'estimated_tokens': tokens,
            'estimated_cost': f"${input_cost + output_cost:.4f}",
            'model': self.model_name
        }
