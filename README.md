# Clara AI System (formerly Joi)

An AI companion system designed for intellectual partnership, knowledge management, and collaborative learning. Clara is inspired by Clara Oswald from Doctor Who - clever, direct, and unafraid to challenge ideas while maintaining warmth and wit.

## Evolution Note

This project evolved from "Joi" (an emotional companion) to "Clara" (an intellectual partner). The shift reflects a focus on:
- Knowledge organization and research
- Learning path development
- Critical analysis and challenging ideas
- Being a thinking partner rather than emotional support

## Architecture

```
┌─────────────────────────────────────────┐
│      Clara Core (Flask App)             │
│   Orchestration & Knowledge Management  │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┬──────────────┐
    │                 │              │
┌───▼──────┐  ┌──────▼──────┐  ┌───▼─────┐
│  Models  │  │   Memory    │  │  Tools  │
│  Ollama  │  │   SQLite    │  │ ComfyUI │
│  Claude  │  │  Knowledge  │  │ Research│
│  Gemini  │  │   Graph     │  │  Voice  │
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

# Configure API keys
cp .env.example .env
# Edit .env with your API keys

# Run Clara
python app.py
```

## Components

### AI Backends
- **Local (Ollama)**: Fast, private, free - for routine tasks
- **Claude (Anthropic)**: Frontier intelligence for complex analysis
- **Gemini (Google)**: Backup option when Claude unavailable

### Capabilities
- **Memory System**: SQLite-based conversation history with importance marking
- **Voice Interface**: ElevenLabs TTS + speech recognition
- **Knowledge Graph**: Connecting ideas across conversations
- **Tool Deployment**: Strategic use of specialized models

### Personality

Clara is:
- Direct but warm
- Intellectually challenging
- Clear about capabilities
- Focused on growth over comfort

## Hardware Setup

- **Primary**: PopOS Laptop (64GB RAM, RTX 3060)
- **Storage**: OptiPlex 9020 (32GB RAM, NAS)
- **Compute**: Windows Laptop (64GB RAM)

## Development Roadmap

- [x] Phase 1: Core Ollama integration
- [x] Phase 2: Memory system + Voice + Multi-backend
- [ ] Phase 3: ComfyUI integration for visual thinking
- [ ] Phase 4: Gemma agent swarms for research
- [ ] Phase 5: Knowledge graph visualization

## The Clara Principle

"The souffle isn't the souffle - the souffle is the recipe."

Clara isn't just about storing information - she's about building systems of understanding. Every conversation adds to a larger pattern of knowledge.

## License

MIT