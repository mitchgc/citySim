# CitySim - LLM-Powered Village Simulator

A village survival simulator where 3-5 NPCs are powered by LLMs, creating emergent narratives through conversational dynamics.

## Project Structure

```
citysim/
├── core/              # Core game systems (game state, conversation manager)
├── director/          # Director interface and CLI
├── examples/          # Usage examples and demonstrations
├── npc/              # NPC management, personalities, and relationships
├── prompts/          # LLM interface and prompt building
├── saves/            # Configuration and save data
└── tests/            # Test files
```

## Setup

1. **Environment Variables**: Copy `.env.example` to `.env` and add your API keys:
   ```
   TOGETHER_API_KEY=your_together_api_key_here
   ```

2. **Dependencies**: Install required packages:
   ```bash
   pip install python-dotenv aiohttp
   ```

## Quick Start

```python
from citysim.prompts.llm_interface import LLMInterface

# Use default model (DeepSeek-V3.1)
llm = LLMInterface()

# Or specify a different model
llm = LLMInterface(model_name="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")
```

## Documentation

- [CLAUDE.md](CLAUDE.md) - Complete design document and implementation guide
- [TOGETHER_API_SETUP.md](TOGETHER_API_SETUP.md) - Together API integration details
- [citysim/examples/](citysim/examples/) - Code examples

## Development

The project uses the Together API for LLM inference. See `TOGETHER_API_SETUP.md` for configuration details.

### Running Examples

```bash
cd citysim
python3 examples/model_switching.py
```

## Git Workflow

The `.gitignore` is configured to exclude:
- Runtime logs and temporary files
- Development notebooks
- API keys and secrets
- Python cache files
- IDE-specific files

Configuration files like `citysim/saves/npc_data.json` are tracked in git as examples/defaults.