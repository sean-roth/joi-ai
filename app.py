#!/usr/bin/env python3
"""
Joi AI Orchestration System
Main Flask application
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

# Initialize Joi
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
        use_claude = data.get('use_claude', False)  # Option to force Claude
        
        if not message:
            return jsonify({
                'status': 'error',
                'message': 'No message provided'
            }), 400
        
        # Let Joi decide which backend to use (or force Claude)
        if use_claude:
            result = joi.chat(message, use_claude=True)
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

@app.route('/api/switch_backend', methods=['POST'])
def switch_backend():
    """Switch between Ollama and Claude"""
    data = request.json
    backend = data.get('backend')
    
    if joi.switch_backend(backend):
        return jsonify({
            'status': 'success',
            'message': f'Switched to {backend}'
        })
    else:
        return jsonify({
            'status': 'error',
            'message': f'Backend {backend} not available'
        }), 400

if __name__ == '__main__':
    logger.info("Starting Joi AI System...")
    status = joi.get_status()
    logger.info(f"Ollama: {status['ollama']['connected']}")
    logger.info(f"Claude: {status['claude']['available']}")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('FLASK_DEBUG', 'False') == 'True'
    )
