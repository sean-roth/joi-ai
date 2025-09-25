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

from core.ollama_client import OllamaClient

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'development-key')
CORS(app)

# Initialize Joi's consciousness
ollama_client = OllamaClient()

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
        
        if not message:
            return jsonify({
                'status': 'error',
                'message': 'No message provided'
            }), 400
        
        # Get response from Joi
        response = ollama_client.chat(message)
        
        return jsonify({
            'status': 'success',
            'response': response
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
    return jsonify(ollama_client.get_status())

@app.route('/api/models')
def list_models():
    """List available models"""
    return jsonify({
        'models': ollama_client.list_models(),
        'current': ollama_client.current_model
    })

@app.route('/api/switch_model', methods=['POST'])
def switch_model():
    """Switch to a different model"""
    data = request.json
    model_name = data.get('model')
    
    if ollama_client.switch_model(model_name):
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
    logger.info("Starting Joi AI System...")
    logger.info(f"Ollama connected: {ollama_client.test_connection()}")
    logger.info(f"Current model: {ollama_client.current_model}")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('FLASK_DEBUG', 'False') == 'True'
    )
