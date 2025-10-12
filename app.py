#!/usr/bin/env python3
"""
Joi AI Orchestration System
Main Flask application with voice and memory
"""

import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from loguru import logger

from core.joi_orchestrator import JoiOrchestrator

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'development-key')
CORS(app)

# Initialize Joi with all capabilities
joi = JoiOrchestrator()

@app.route('/')
def index():
    """Main interface"""
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with Joi"""
    try:
        data = request.json
        message = data.get('message')
        use_claude = data.get('use_claude', False)
        use_gemini = data.get('use_gemini', False)
        
        if not message:
            return jsonify({
                'status': 'error',
                'message': 'No message provided'
            }), 400
        
        # Route based on backend preference
        if use_claude:
            result = joi.chat(message, use_claude=True)
        elif use_gemini:
            result = joi.chat(message, use_gemini=True)
        else:
            result = joi.smart_routing(message)  # Smart routing based on complexity
        
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
    """Handle voice interactions"""
    try:
        result = joi.voice_chat(use_voice_input=True, use_voice_output=True)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Voice error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/speak', methods=['POST'])
def speak():
    """Text-to-speech only"""
    try:
        data = request.json
        text = data.get('text')
        
        if not text:
            return jsonify({
                'status': 'error',
                'message': 'No text provided'
            }), 400
        
        success = joi.voice.speak(text)
        return jsonify({
            'status': 'success' if success else 'error',
            'spoken': success
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
    conversations = joi.memory.get_recent_conversations(limit=limit)
    return jsonify(conversations)

@app.route('/api/memory/important')
def get_important_memories():
    """Get important memories"""
    memories = joi.memory.get_important_memories()
    return jsonify(memories)

@app.route('/api/memory/search')
def search_memory():
    """Search through memories"""
    query = request.args.get('query', '')
    if not query:
        return jsonify([])
    
    results = joi.memory.search_memories(query)
    return jsonify(results)

@app.route('/api/status')
def status():
    """System status endpoint"""
    return jsonify(joi.get_status())

@app.route('/api/switch_model', methods=['POST'])
def switch_model():
    """Switch Ollama model"""
    data = request.json
    model_name = data.get('model')
    
    if joi.ollama.switch_model(model_name):
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
    logger.info("Starting Joi AI System...")
    logger.info("=" * 50)
    
    status = joi.get_status()
    
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
    logger.info("Joi is ready at http://localhost:5000")
    logger.info("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('FLASK_DEBUG', 'False') == 'True'
    )
