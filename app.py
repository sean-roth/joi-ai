#!/usr/bin/env python3
"""
Clara AI System
Intellectual companion and knowledge management system
"""

import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from loguru import logger

from core.clara_orchestrator import ClaraOrchestrator

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'development-key')
CORS(app)

# Initialize Clara with all capabilities
clara = ClaraOrchestrator()

@app.route('/')
def index():
    """Main interface"""
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with Clara"""
    try:
        data = request.json
        message = data.get('message')
        use_claude = data.get('use_claude', False)
        use_gemini = data.get('use_gemini', False)
        voice_mode = data.get('voice_mode', False)  # Flag for concise responses
        
        if not message:
            return jsonify({
                'status': 'error',
                'message': 'No message provided'
            }), 400
        
        # Route based on backend preference
        if use_claude:
            result = clara.chat(message, use_claude=True, voice_mode=voice_mode)
        elif use_gemini:
            result = clara.chat(message, use_gemini=True, voice_mode=voice_mode)
        else:
            result = clara.smart_routing(message, voice_mode=voice_mode)
        
        return jsonify({
            'status': 'success',
            'response': result['response'],
            'backend': result['backend'],
            'model': result['model']
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/voice', methods=['POST'])
def voice_chat():
    """Handle voice interactions with proper conversational flow"""
    try:
        result = clara.voice_chat(use_voice_input=True, use_voice_output=True)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Voice error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/speak', methods=['POST'])
def speak():
    """Text-to-speech with optional summarization"""
    try:
        data = request.json
        text = data.get('text')
        summarize = data.get('summarize', False)  # Should we create a concise version?
        
        if not text:
            return jsonify({
                'status': 'error',
                'message': 'No text provided'
            }), 400
        
        # If summarize is true, generate concise version
        if summarize and len(text) > 100:
            spoken_text = clara.generate_voice_summary(text, "User requested TTS")
        else:
            spoken_text = text
        
        success = clara.voice.speak(spoken_text)
        return jsonify({
            'status': 'success' if success else 'error',
            'original': text,
            'spoken': spoken_text,
            'success': success
        })
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/memory/recent')
def get_recent_memory():
    """Get recent conversations from memory"""
    limit = request.args.get('limit', 10, type=int)
    conversations = clara.memory.get_recent_conversations(limit=limit)
    return jsonify(conversations)

@app.route('/api/memory/important')
def get_important_memories():
    """Get important memories"""
    memories = clara.memory.get_important_memories()
    return jsonify(memories)

@app.route('/api/memory/search')
def search_memory():
    """Search through memories"""
    query = request.args.get('query', '')
    if not query:
        return jsonify([])
    
    results = clara.memory.search_memories(query)
    return jsonify(results)

@app.route('/api/status')
def status():
    """System status endpoint"""
    return jsonify(clara.get_status())

@app.route('/api/switch_model', methods=['POST'])
def switch_model():
    """Switch Ollama model"""
    data = request.json
    model_name = data.get('model')
    
    if clara.ollama.switch_model(model_name):
        return jsonify({
            'status': 'success',
            'message': f'Switched to {model_name}'
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Model {model_name} not available'
        }), 400

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("Starting Clara AI System...")
    logger.info("Intellectual Companion & Knowledge Manager")
    logger.info("=" * 50)
    
    status = clara.get_status()
    
    # Log backend status
    logger.info("AI Backends:")
    logger.info(f"  Ollama: {status['backends']['ollama']['connected']}")
    logger.info(f"  Claude: {status['backends']['claude']['available']}")
    logger.info(f"  Gemini: {status['backends']['gemini']['available']}")
    
    # Log capabilities
    logger.info("Capabilities:")
    logger.info(f"  Memory: {status['memory']['total_conversations']} conversations stored")
    logger.info(f"  Voice: {status['voice']['tts_provider']} TTS")
    
    logger.info("=" * 50)
    logger.info("Clara is ready at http://localhost:5000")
    logger.info('"Run, you clever boy, and remember"')
    logger.info("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('FLASK_DEBUG', 'False') == 'True'
    )
