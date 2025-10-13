"""
Clara Orchestrator - Manages all AI backends and capabilities
Switches between local models, Claude, and Gemini based on need
"""

from typing import Dict, List, Optional, Tuple
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
    
    def chat(self, message: str, use_claude: bool = False, use_gemini: bool = False, voice_mode: bool = False) -> Dict:
        """Route chat to appropriate backend"""
        
        # Get context from memory
        context = self.get_relevant_context(message)
        
        # If voice mode, add instruction for concise response
        if voice_mode:
            message = f"[Respond concisely for voice - max 2-3 sentences] {message}"
        
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
            user_message=message.replace("[Respond concisely for voice - max 2-3 sentences] ", ""),
            joi_response=response,  # Keep DB field name for compatibility
            backend=backend,
            model=model
        )
        
        return {
            'response': response,
            'backend': backend,
            'model': model
        }
    
    def generate_voice_summary(self, full_response: str, original_query: str) -> str:
        """Generate a concise voice-appropriate version of the response"""
        
        # Use local model for quick summarization
        summary_prompt = f"""
        Original question: {original_query}
        
        Full response: {full_response}
        
        Create a 1-2 sentence spoken response that:
        - Captures the key point
        - Sounds natural when spoken aloud
        - Uses conversational language
        - Ends with a natural pause point
        
        Remember: You are Clara, direct and clear.
        """
        
        try:
            # Use local model for speed
            summary = self.ollama.chat(summary_prompt)
            return summary
        except:
            # Fallback: take first two sentences
            sentences = full_response.split('. ')[:2]
            return '. '.join(sentences) + '.'
    
    def smart_routing(self, message: str, voice_mode: bool = False) -> Dict:
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
        if needs_frontier and not voice_mode:  # Don't use expensive models for voice summaries
            if self.claude.is_available():
                logger.info("Routing to Claude for complex query")
                return self.chat(message, use_claude=True, voice_mode=voice_mode)
            elif self.gemini.is_available():
                logger.info("Routing to Gemini as Claude unavailable")
                return self.chat(message, use_gemini=True, voice_mode=voice_mode)
        
        # Default to local
        return self.chat(message, voice_mode=voice_mode)
    
    def voice_chat(self, use_voice_input: bool = True, use_voice_output: bool = True) -> Dict:
        """Handle voice-based interaction with concise responses"""
        result = {'status': 'error', 'message': 'Voice not available'}
        
        # Listen for input
        if use_voice_input:
            logger.info("Listening for voice input...")
            text = self.voice.listen(timeout=10)
            if not text:
                return {'status': 'error', 'message': 'No speech detected'}
        else:
            return {'status': 'error', 'message': 'Voice input not requested'}
        
        # Process through chat - get BOTH full and voice responses
        chat_result = self.smart_routing(text, voice_mode=False)  # Get full response first
        full_response = chat_result['response']
        
        # Generate concise voice version
        voice_response = self.generate_voice_summary(full_response, text)
        
        # Speak the concise version
        if use_voice_output:
            success = self.voice.speak(voice_response)
            if not success:
                logger.warning("TTS failed")
        
        return {
            'status': 'success',
            'input': text,
            'response': full_response,  # Full response for text display
            'voice_response': voice_response,  # What was actually spoken
            'backend': chat_result['backend'],
            'model': chat_result['model'],
            'voice_output': use_voice_output
        }
    
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
