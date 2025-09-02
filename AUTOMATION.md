# Mafia Game Automation System

This repository includes a complete automation loop for running AI-powered Mafia games with self-improving strategies.

## Quick Start

### 1. Interactive Menu
```bash
./run_games.sh
```
This launches an interactive menu with options for running 5 games, 10 games, continuously, or with custom settings.

### 2. Command Line
```bash
# Run 5 games with full reporting
python3 run_loop.py --games 5

# Run 10 games with quick results only  
python3 run_loop.py --games 10 --quick

# Run continuously (Ctrl+C to stop)
python3 run_loop.py

# Update strategies every 2 games instead of 3
python3 run_loop.py --games 10 --strategy-frequency 2
```

## How It Works

The automation loop consists of three main phases:

### 1. 🎮 Game Execution
- Runs a complete AI-only Mafia game with 4 players
- Each player has unique personalities and evolving strategies  
- Games feature card-based mechanics (20 cards: 8 good, 12 bad)
- All game data is logged comprehensively

### 2. 📊 Results Analysis
- Displays team statistics (good vs bad wins)
- Shows individual player performance metrics
- Tracks role-specific win rates 
- Provides game history and trends

### 3. 🧠 Strategy Evolution
- AI players analyze their own game performance
- Uses complete conversation logs for self-reflection
- Generates updated strategies based on what worked/failed
- Maintains strategy version history

## Files Overview

### Core Game Files
- **`mafia.py`** - Main game engine with 4 AI players
- **`scoresheet.py`** - Win/loss tracking and statistics
- **`conversation_logger.py`** - Comprehensive game logging
- **`strategy_manager.py`** - Player strategy storage and evolution

### Automation Scripts
- **`run_loop.py`** - Main automation loop (Python)
- **`run_games.sh`** - Interactive menu wrapper (Bash)
- **`update_strategies.py`** - AI strategy self-improvement

### Utility Scripts
- **`view_strategies.py`** - View current player strategies
- **`view_conversation_log.py`** - Browse game conversation logs

## Configuration Options

### Strategy Update Frequency
By default, strategies update every 3 games. Modify with:
```bash
python3 run_loop.py --strategy-frequency 2  # Update every 2 games
```

### Reporting Detail Level
- **Full reporting** (default): Shows detailed player statistics
- **Quick reporting** (`--quick`): Shows summary only

### Game Count
- **Fixed count**: `--games N` runs exactly N games
- **Continuous**: No `--games` flag runs until interrupted

## Data Storage

### Generated Files
- **`game_results.json`** - Scoresheet data
- **`conversation_log.json`** - Machine-readable game logs  
- **`conversation_log.txt`** - Human-readable game logs
- **`strategies.json`** - Player strategy evolution data
- **`debug.log`** - Detailed debug information

### Data Persistence
All game data persists between runs. The automation system:
- Builds on previous results
- Maintains strategy evolution history
- Tracks long-term performance trends

## Strategy Evolution Example

Players start with basic default strategies and evolve them based on performance:

**Blake's Initial Strategy:**
- Good role: "Stay calm and logical, build trust through consistent behavior"  
- Bad role: "Maintain smooth-talking persona, occasionally admit to bad cards"

**Blake's Evolved Strategy (after analyzing games):**
- Adds tactical elements like "diversify suspicion each round"
- Includes counter-strategies like "variable voting patterns"  
- Develops meta-tactics like "strategic praise to build trust"

## Performance Monitoring

The system tracks:
- **Team Performance**: Good vs Bad team win rates
- **Individual Performance**: Per-player win rates in each role
- **Strategy Effectiveness**: Win rates for each strategy version
- **Game Trends**: Performance over time

## Dependencies

- **Python 3.x** with `aiohttp` for async LLM calls
- **Ollama** running locally with `gemma3:4b` model
- **Bash** for interactive menu script

## Tips for Best Results

1. **Let it run long-term**: Strategy evolution improves with more games
2. **Monitor strategy updates**: Check how players adapt their approaches  
3. **Analyze conversation logs**: See how strategies play out in practice
4. **Experiment with frequency**: Try different strategy update intervals

The system is designed to run continuously, with AI players becoming more sophisticated opponents over time through self-analysis and strategy refinement.