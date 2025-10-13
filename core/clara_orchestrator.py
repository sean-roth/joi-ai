"""
Clara Orchestrator - Manages all AI backends and capabilities
Switches between local models, Claude, and Gemini based on need
"""

from typing import Dict, List, Optional
from loguru import logger

from core.ollama_client import OllamaClient
from core.anthropic_client import AnthropicClient
from core.gemini_client import GeminiClient
from core.memory import MemoryManager
from core.voice_interface import VoiceInterface

class ClaraOrchestrator:
    """Orchestrates between different AI backends and capabilities"""
    
    def __init__(self):
        # AI Backends
        self.ollama = OllamaClient()
        self.claude = AnthropicClient()
        self.gemini = GeminiClient()
        
        # Capabilities
        self.memory = MemoryManager()
        self.voice = VoiceInterface()
        
        # State
        self.current_backend = 'ollama'  # Default to local
        self.voice_mode = False
        
        logger.info("Clara Orchestrator initialized")
        self.log_status()
    
    def log_status(self):
        """Log the status of all components"""
        logger.info(f"Ollama available: {self.ollama.test_connection()}")
        logger.info(f"Claude available: {self.claude.is_available()}")
        logger.info(f"Gemini available: {self.gemini.is_available()}")
        logger.info(f"Memory initialized: {self.memory.get_statistics()}")
        logger.info(f"Voice available: {self.voice.elevenlabs_client is not None}")
    
    def chat(self, message: str, use_claude: bool = False, use_gemini: bool = False) -> Dict:
        """Route chat to appropriate backend"""
        
        # Get context from memory
        context = self.get_relevant_context(message)
        
        # Decide which backend to use
        if use_claude and self.claude.is_available():
            backend = 'claude'
            response = self.claude.chat(message, context)
            model = self.claude.model
        elif use_gemini and self.gemini.is_available():
            backend = 'gemini'
            response = self.gemini.chat(message, context)
            model = self.gemini.model_name
        elif self.claude.is_available() and not self.ollama.test_connection():
            # Fallback to Claude if Ollama is down
            backend = 'claude'
            response = self.claude.chat(message, context)
            model = self.claude.model
        elif self.gemini.is_available() and not self.ollama.test_connection():
            # Fallback to Gemini if Ollama and Claude are down
            backend = 'gemini'
            response = self.gemini.chat(message, context)
            model = self.gemini.model_name
        else:
            backend = 'ollama'
            response = self.ollama.chat(message, context)
            model = self.ollama.current_model
        
        # Store in memory
        self.memory.store_conversation(
            user_message=message,
            joi_response=response,  # Keep DB field name for compatibility
            backend=backend,
            model=model
        )
        
        return {
            'response': response,
            'backend': backend,
            'model': model
        }
    
    def smart_routing(self, message: str) -> Dict:
        """Intelligently route to best backend based on query complexity"""
        
        # Keywords that suggest need for frontier model
        complex_indicators = [
            'analyze', 'complex', 'detailed', 'explain in depth',
            'strategy', 'comprehensive', 'evaluate', 'compare',
            'create', 'write', 'design', 'plan', 'research',
            'critique', 'review', 'assess', 'synthesize'
        ]
        
        # Check if message seems complex
        needs_frontier = any(indicator in message.lower() for indicator in complex_indicators)
        
        # Also use frontier model for long messages
        if len(message) > 500:
            needs_frontier = True
        
        # Try Claude first, then Gemini, then local
        if needs_frontier:
            if self.claude.is_available():
                logger.info("Routing to Claude for complex query")
                return self.chat(message, use_claude=True)
            elif self.gemini.is_available():
                logger.info("Routing to Gemini as Claude unavailable")
                return self.chat(message, use_gemini=True)
        
        # Default to local
        return self.chat(message)
    
    def get_relevant_context(self, message: str) -> List[Dict]:
        """Get relevant context from memory"""
        context = []
        
        # Get recent conversations
        recent = self.memory.get_recent_conversations(limit=5)
        for conv in recent:
            context.append({'role': 'user', 'content': conv['user_message']})
            context.append({'role': 'assistant', 'content': conv['joi_response']})
        
        # Search for relevant memories
        # Extract keywords from message (simple approach)
        keywords = [word for word in message.split() if len(word) > 4]
        for keyword in keywords[:3]:  # Limit to 3 keywords
            memories = self.memory.search_memories(keyword, limit=2)
            for mem in memories:
                if mem['importance'] > 0.5:  # Only include important memories
                    context.insert(0, {'role': 'user', 'content': mem['user_message']})
                    context.insert(1, {'role': 'assistant', 'content': mem['joi_response']})
        
        return context[-20:]  # Limit context to last 20 messages
    
    def voice_chat(self, use_voice_input: bool = True, use_voice_output: bool = True) -> Dict:
        """Handle voice-based interaction"""
        result = {'status': 'error', 'message': 'Voice not available'}
        
        # Listen for input
        if use_voice_input:
            logger.info("Listening for voice input...")
            text = self.voice.listen(timeout=10)
            if not text:
                return {'status': 'error', 'message': 'No speech detected'}
        else:
            return {'status': 'error', 'message': 'Voice input not requested'}
        
        # Process through chat
        chat_result = self.smart_routing(text)
        
        # Speak response
        if use_voice_output:
            success = self.voice.speak(chat_result['response'])
            if not success:
                logger.warning("TTS failed")
        
        return {
            'status': 'success',
            'input': text,
            'response': chat_result['response'],
            'backend': chat_result['backend'],
            'model': chat_result['model'],
            'voice_output': use_voice_output
        }
    
    def get_status(self) -> Dict:
        """Get status of all components"""
        return {
            'backends': {
                'ollama': {
                    'connected': self.ollama.test_connection(),
                    'model': self.ollama.current_model,
                    'models_available': self.ollama.list_models()
                },
                'claude': {
                    'available': self.claude.is_available(),
                    'model': self.claude.model if self.claude.is_available() else None
                },
                'gemini': {
                    'available': self.gemini.is_available(),
                    'model': self.gemini.model_name if self.gemini.is_available() else None
                }
            },
            'memory': self.memory.get_statistics(),
            'voice': {
                'tts_available': self.voice.elevenlabs_client is not None,
                'tts_provider': 'elevenlabs' if self.voice.elevenlabs_client else 'system'
            }
        }
