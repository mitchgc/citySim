# Together API Integration

The citysim project has been updated to use the Together API instead of local Ollama for LLM inference.

## Setup

1. **Environment Variable**: Make sure your `.env` file contains:
   ```
   TOGETHER_API_KEY=your_api_key_here
   ```

2. **Dependencies**: The following Python packages are required:
   - `python-dotenv` (for loading .env files)
   - `aiohttp` (for async HTTP requests)

## Usage

### Quick Start

```python
from citysim.prompts.llm_interface import LLMInterface

# Use default model (DeepSeek-V3.1)
llm = LLMInterface()

# Use a specific model
llm = LLMInterface(model_name="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")
```

### Changing Models

There are three ways to change models:

1. **Change default model** - Edit `DEFAULT_MODEL` in `citysim/prompts/llm_interface.py`:
   ```python
   DEFAULT_MODEL = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
   ```

2. **Pass model at initialization**:
   ```python
   llm = LLMInterface(model_name="Qwen/Qwen2.5-72B-Instruct-Turbo")
   ```

3. **Change model on existing instance**:
   ```python
   llm.set_model("mistralai/Mixtral-8x7B-Instruct-v0.1")
   ```

### Available Models

- `deepseek-ai/DeepSeek-V3.1` (default)
- `meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo`
- `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo`
- `mistralai/Mixtral-8x7B-Instruct-v0.1`
- `Qwen/Qwen2.5-72B-Instruct-Turbo`
- `microsoft/WizardLM-2-8x22B`

You can get this list programmatically:
```python
models = LLMInterface.get_available_models()
```

## Example

Run the model switching example:
```bash
cd citysim
python3 examples/model_switching.py
```

## API Details

- **Base URL**: `https://api.together.xyz/v1/chat/completions`
- **Temperature**: 1.05 (as specified in your example)
- **Max Tokens**: 1000
- **Stream**: False

## Migration Notes

The existing code should work without changes since:
- The constructor defaults to the Together API
- All existing method signatures remain the same
- Error handling and response parsing remain compatible

The main changes are:
- Ollama URL → Together API endpoint
- Ollama prompt format → OpenAI-compatible chat format
- Added SSL handling for macOS certificate issues
- Added model switching convenience methods