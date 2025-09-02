# Village Simulator

🏘️ **LLM-Powered Conversational NPCs for Emergent Storytelling**

A village survival simulator where 3-5 NPCs powered by LLMs create emergent narratives through conversational dynamics. Players act as directors, setting up scenes and situations while NPCs respond naturally based on their personalities, relationships, and hidden complications.

## Quick Start

```bash
cd citysim
python3 main.py
```

Then try option **9: Quick Test Scene** to see the system in action.

## System Overview

### Core Architecture

- **Conversation Manager**: Turn-based dialogue with interjection system
- **NPC System**: Personality (nature/nurture) + bidirectional relationship matrices  
- **Memory System**: Recent → compressed → faded memory lifecycle
- **Prompt System**: Modular blocks for different contexts
- **Director Interface**: Scene setup and beat management

### Key Features

- **Round-based conversations** with 8-round maximum
- **Strategic interjections** (1 per character per round)
- **Bidirectional relationships** (A→B trust ≠ B→A trust)
- **Hidden complications** drive character behavior
- **Memory compression** forces interesting choices
- **Emergent drama** from information asymmetry

## Narrative Structure

```
Story
├── Scene (Major narrative segment)
│   ├── Premise: What's happening
│   └── Stakes: What could go wrong
└── Beat (Conversation segment)  
    ├── Situation: Immediate challenge
    ├── Characters: Who's present
    └── Complications: Hidden secrets per character
```

## Character System

### NPCs Have Two Personality Layers

**Nature** (Permanent core)
- Core traits: ["generous", "anxious", "hardworking"] 
- Cognitive style: "overthinking"
- Stress response: "people-pleasing"
- Moral compass: "fairness-first"

**Nurture** (Evolves per scene)
- Recent treatment: "appreciated" 
- Current confidence: 7/10
- Learned behaviors: ["Bob responds to guilt"]
- Temporary beliefs: ["We might survive"]

### Relationship Matrix

Each relationship is **bidirectional** and tracks:
- **Trust**: 0-10 (Will they do what they say?)
- **Affection**: 0-10 (Do I enjoy their company?) 
- **Label**: Derived from trust+affection ("reliable stranger", "charming liar")
- **Memories**: Recent interactions and historical events
- **Gossip**: Things heard but not witnessed

## Usage Guide

### 1. Create Scene
```
Scene Title: "The Missing Food"
Premise: "The food storage was raided overnight"  
Stakes: "Find the thief or the group falls apart from suspicion"
```

### 2. Set Up Beat
```
Situation: "Discovering the empty storage at dawn"
Location: "Food storage area" 
Time: "Dawn"
Characters: Alice, Bob, Charlie

Complications (secrets):
- Alice: "You saw someone near storage but couldn't tell who"
- Bob: "You sleep-walked last night and don't remember"  
- Charlie: "You took the food but regret it immediately"
```

### 3. Run Conversation
The system manages:
- Turn order with interjection opportunities
- Relationship updates based on interactions  
- Memory formation and compression
- Natural conversation flow and exits

## Example Output

```
🎬 Starting conversation... (max 8 rounds)
========================================

Round 1:
Alice (panicked): "This is a disaster. We barely had enough as it was."
  (checks the storage again desperately)

Bob (confused): "I don't understand how this could happen..."

🗯️ Charlie interjects: "Maybe we should focus on solutions instead of blame!"
Bob (defensive): "I wasn't blaming anyone!"

Round 2:
Charlie (guilty): "Look, we need to stay calm and figure this out together."
...
```

## Directory Structure

```
citysim/
├── core/                    # Core systems
│   ├── conversation_manager.py  # Turn-based dialogue  
│   └── game_state.py           # Scene/beat management
├── npc/                     # NPC systems
│   ├── personality.py          # Nature/nurture system
│   ├── relationships.py        # Bidirectional matrices
│   └── npc_manager.py          # Central NPC coordination
├── prompts/                 # LLM interface
│   ├── prompt_builder.py       # Modular prompt blocks
│   └── llm_interface.py        # LLM communication
├── director/                # User interface  
│   ├── scene_director.py       # Scene management API
│   └── cli_interface.py        # Command-line interface
├── saves/                   # Game state persistence
├── logs/                    # Session and debug logs  
├── exports/                 # Story exports
└── main.py                  # Entry point
```

## Requirements

- Python 3.8+
- Local LLM via Ollama (default: gemma2:4b)
- Optional: asyncio support for concurrent operations

## LLM Setup

Install Ollama and pull a compatible model:

```bash
# Install Ollama (see ollama.ai)
ollama pull gemma2:4b
# or 
ollama pull llama3.2:3b  # Smaller/faster option
```

The system will use `http://localhost:11434/api/generate` by default.

## Configuration

Edit these files to customize:
- `npc/personality.py`: Modify default character archetypes
- `prompts/prompt_builder.py`: Adjust prompt templates  
- `director/cli_interface.py`: Add new menu options

## Performance

- **Target**: <500ms per turn response
- **Tokens**: ~180 tokens per prompt (optimized blocks)
- **Conversations**: 20-40 turns typical (8 rounds × 3 characters)
- **Memory**: Compressed after each scene to prevent bloat

## Debugging

Session logs: `logs/session.log`
Game state: `saves/game_state.json`  
Story exports: `exports/story_YYYYMMDD_HHMMSS.txt`

Use menu option **7: Performance Stats** to monitor LLM response times and token usage.

## Design Philosophy

1. **Hidden Information**: Complications never shared between NPCs
2. **Bidirectional Relationships**: A→B feelings ≠ B→A feelings  
3. **Memory Compression**: Forces interesting choices about what to remember
4. **Controlled Conversations**: Round limits prevent infinite loops
5. **Director as Orchestrator**: Set situations, not outcomes
6. **Emergent Drama**: Conflict from information asymmetry and relationship dynamics

## Credits

Built on patterns from the existing mafia game system, reimagined for conversational storytelling.

---

*Generate emergent narratives where every conversation matters.*