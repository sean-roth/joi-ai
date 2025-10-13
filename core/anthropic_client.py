"""
Anthropic Claude integration for Clara
Provides access to frontier-level intelligence when needed
"""

import os
from typing import Dict, List, Optional
import anthropic
from loguru import logger

class AnthropicClient:
    """Manages Anthropic Claude API interactions"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = None
        self.model = "claude-3-5-sonnet-20241022"  # Latest model
        self.system_prompt = self.load_system_prompt()
        
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info("Anthropic client initialized")
        else:
            logger.warning("No Anthropic API key found")
    
    def load_system_prompt(self) -> str:
        """Load Clara's personality for Claude"""
        try:
            with open('prompts/clara_system.txt', 'r') as f:
                return f.read()
        except FileNotFoundError:
            return "You are Clara, an AI companion and intellectual partner."
    
    def is_available(self) -> bool:
        """Check if Anthropic API is configured"""
        return self.client is not None
    
    def chat(self, message: str, context: List[Dict] = None) -> str:
        """Send message to Claude as Clara"""
        if not self.client:
            return "Claude integration not configured. Add ANTHROPIC_API_KEY to .env"
        
        try:
            # Build message history
            messages = []
            
            # Add context if provided
            if context:
                for ctx in context:
                    # Convert from Ollama format to Anthropic format
                    if ctx.get('role') == 'system':
                        continue  # System goes separately
                    messages.append({
                        'role': ctx['role'] if ctx['role'] in ['user', 'assistant'] else 'user',
                        'content': ctx['content']
                    })
            
            # Add current message
            messages.append({
                'role': 'user',
                'content': message
            })
            
            # Send to Claude with Clara's personality
            response = self.client.messages.create(
                model=self.model,
                system=self.system_prompt,
                messages=messages,
                max_tokens=4096,
                temperature=0.7
            )
            
            return response.content[0].text
            
        except anthropic.RateLimitError:
            logger.error("Claude API rate limit hit")
            return "I need to pace myself - too many complex thoughts at once. Try again in a moment."
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            return "Having trouble accessing my extended capabilities right now."
        except Exception as e:
            logger.error(f"Unexpected error with Claude: {e}")
            return "Something went wrong connecting to my extended processing."
    
    def estimate_tokens(self, text: str) -> int:
        """Rough estimate of token count"""
        # Approximate: 1 token ~= 4 characters
        return len(text) // 4
    
    def get_usage_estimate(self, message: str) -> Dict:
        """Estimate API cost for a message"""
        tokens = self.estimate_tokens(message)
        # Claude 3.5 Sonnet pricing (as of Oct 2024)
        input_cost = (tokens / 1_000_000) * 3.00  # $3 per 1M input tokens
        output_cost = (tokens / 1_000_000) * 15.00  # $15 per 1M output tokens (estimate)
        
        return {
            'estimated_tokens': tokens,
            'estimated_cost': f"${input_cost + output_cost:.4f}",
            'model': self.model
        }
