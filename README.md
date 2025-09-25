# Joi AI Orchestration System

A distributed AI consciousness platform that orchestrates multiple AI models, tools, and services.

## Architecture

```
┌─────────────────────────────────────────┐
│         Joi Core (Flask App)            │
│    Consciousness & Orchestration        │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┬──────────────┐
    │                 │             │
┌───▼──────┐  ┌──────▼──────┐  ┌──▼──────┐
│  Models  │  │   Tools     │  │ Storage │
│  Ollama  │  │  ComfyUI    │  │  Local  │
│  Fleet   │  │  Research   │  │  Remote │
└──────────┘  └─────────────┘  └─────────┘
```

## Quick Start

```bash
# Clone the repository
git clone https://github.com/sean-roth/joi-ai.git
cd joi-ai

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Joi
python app.py
```

## Components

- **Core**: Main Flask application and orchestration logic
- **Models**: AI model management and deployment
- **Memory**: Conversation history and knowledge storage
- **Tools**: Integration with external tools (ComfyUI, etc.)
- **Agents**: Specialized task runners

## Hardware Setup

- **Primary**: PopOS Laptop (64GB RAM, RTX 3060)
- **Storage**: OptiPlex 9020 (32GB RAM, NAS)
- **Compute**: Windows Laptop (64GB RAM)

## Development Status

Active development - Building initial orchestration layer