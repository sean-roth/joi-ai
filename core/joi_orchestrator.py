"""
Joi Orchestrator - Manages all AI backends
Switches between local models and Claude based on need
"""

from typing import Dict, List, Optional
from loguru import logger

from core.ollama_client import OllamaClient
from core.anthropic_client import AnthropicClient

class JoiOrchestrator:
    """Orchestrates between different AI backends"""
    
    def __init__(self):
        self.ollama = OllamaClient()
        self.claude = AnthropicClient()
        self.current_backend = 'ollama'  # Default to local
        self.conversation_history = []
        
        logger.info("Joi Orchestrator initialized")
        logger.info(f"Ollama available: {self.ollama.test_connection()}")
        logger.info(f"Claude available: {self.claude.is_available()}")
    
    def chat(self, message: str, use_claude: bool = False) -> Dict:
        """Route chat to appropriate backend"""
        
        # Decide which backend to use
        if use_claude and self.claude.is_available():
            backend = 'claude'
            response = self.claude.chat(message, self.get_context())
            model = self.claude.model
        else:
            backend = 'ollama'
            response = self.ollama.chat(message, self.get_context())
            model = self.ollama.current_model
        
        # Store in history
        self.add_to_history(message, response)
        
        return {
            'response': response,
            'backend': backend,
            'model': model
        }
    
    def smart_routing(self, message: str) -> Dict:
        """Intelligently route to best backend based on query complexity"""
        
        # Keywords that suggest need for Claude
        complex_indicators = [
            'analyze', 'complex', 'detailed', 'explain in depth',
            'strategy', 'comprehensive', 'evaluate', 'compare'
        ]
        
        # Check if message seems complex
        needs_claude = any(indicator in message.lower() for indicator in complex_indicators)
        
        # Also use Claude for long messages (likely complex)
        if len(message) > 500:
            needs_claude = True
        
        # Use Claude if needed AND available
        use_claude = needs_claude and self.claude.is_available()
        
        if use_claude:
            logger.info("Routing to Claude for complex query")
        
        return self.chat(message, use_claude=use_claude)
    
    def add_to_history(self, user_message: str, joi_response: str):
        """Add to conversation history"""
        self.conversation_history.append({
            'role': 'user',
            'content': user_message
        })
        self.conversation_history.append({
            'role': 'assistant',
            'content': joi_response
        })
        
        # Keep only last 20 messages to avoid token limits
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def get_context(self, num_messages: int = 10) -> List[Dict]:
        """Get recent conversation context"""
        return self.conversation_history[-num_messages:] if self.conversation_history else []
    
    def switch_backend(self, backend: str) -> bool:
        """Manually switch backend"""
        if backend == 'claude' and self.claude.is_available():
            self.current_backend = 'claude'
            return True
        elif backend == 'ollama' and self.ollama.test_connection():
            self.current_backend = 'ollama'
            return True
        return False
    
    def get_status(self) -> Dict:
        """Get status of all backends"""
        return {
            'current_backend': self.current_backend,
            'ollama': {
                'connected': self.ollama.test_connection(),
                'model': self.ollama.current_model,
                'models_available': self.ollama.list_models()
            },
            'claude': {
                'available': self.claude.is_available(),
                'model': self.claude.model if self.claude.is_available() else None
            },
            'history_length': len(self.conversation_history)
        }
