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

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'development-key')
CORS(app)

@app.route('/')
def index():
    """Main interface"""
    return jsonify({
        'status': 'online',
        'message': 'Joi AI System Ready'
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.json
        message = data.get('message')
        
        # For now, echo back - will connect to Joi
        response = f"Received: {message}"
        
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

@app.route('/status')
def status():
    """System status endpoint"""
    return jsonify({
        'status': 'online',
        'version': '0.1.0'
    })

if __name__ == '__main__':
    logger.info("Starting Joi AI System...")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('FLASK_DEBUG', 'False') == 'True'
    )
