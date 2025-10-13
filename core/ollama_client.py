"""
Ollama integration for Clara
Handles all communication with Ollama models
"""

import ollama
import json
from typing import Dict, List, Optional
from loguru import logger

class OllamaClient:
    """Manages Ollama model interactions"""
    
    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host
        self.client = ollama.Client(host=host)
        self.current_model = "dolphin-mistral:7b"  # Default until Mixtral
        self.system_prompt = self.load_system_prompt()
        
    def load_system_prompt(self) -> str:
        """Load Clara's personality from file"""
        try:
            with open('prompts/clara_system.txt', 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("Clara system prompt not found, using default")
            return "You are Clara, an AI companion and intellectual partner."
    
    def chat(self, message: str, context: List[Dict] = None) -> str:
        """Send message to Clara and get response"""
        try:
            messages = []
            
            # Add system prompt
            messages.append({
                'role': 'system',
                'content': self.system_prompt
            })
            
            # Add context if provided (memory)
            if context:
                for ctx in context:
                    messages.append(ctx)
            
            # Add current message
            messages.append({
                'role': 'user',
                'content': message
            })
            
            # Get response from Ollama
            response = self.client.chat(
                model=self.current_model,
                messages=messages
            )
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            return "Having trouble accessing my local processing. Check if Ollama is running."
    
    def list_models(self) -> List[str]:
        """List available models"""
        try:
            models = self.client.list()
            return [m['name'] for m in models['models']]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    def switch_model(self, model_name: str) -> bool:
        """Switch to a different model"""
        available = self.list_models()
        if model_name in available:
            self.current_model = model_name
            logger.info(f"Switched to model: {model_name}")
            return True
        else:
            logger.warning(f"Model {model_name} not available")
            return False
    
    def get_status(self) -> Dict:
        """Get current status"""
        return {
            'connected': self.test_connection(),
            'current_model': self.current_model,
            'available_models': self.list_models()
        }
    
    def test_connection(self) -> bool:
        """Test if Ollama is reachable"""
        try:
            self.client.list()
            return True
        except:
            return False
