#!/usr/bin/env python3
"""
Strategy Manager for AI Players
Manages player strategies that evolve over time based on game outcomes
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field

@dataclass
class StrategyEntry:
    """A single strategy entry for a player"""
    version: int
    timestamp: str
    strategy_text: str
    games_played: int = 0
    win_rate: float = 0.0
    metadata: Dict = field(default_factory=dict)

@dataclass
class PlayerStrategy:
    """Complete strategy history for a player"""
    player_name: str
    current_version: int
    current_strategy: str
    history: List[StrategyEntry] = field(default_factory=list)
    
class StrategyManager:
    """Manages AI player strategies and their evolution"""
    
    def __init__(self, filename: str = "strategy/strategies.json"):
        self.filename = filename
        self.strategies: Dict[str, PlayerStrategy] = {}
        self.load_strategies()
        
    def load_strategies(self):
        """Load existing strategies from file"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    
                for player_name, strategy_data in data.items():
                    history = [StrategyEntry(**entry) for entry in strategy_data.get('history', [])]
                    self.strategies[player_name] = PlayerStrategy(
                        player_name=player_name,
                        current_version=strategy_data.get('current_version', 1),
                        current_strategy=strategy_data.get('current_strategy', ''),
                        history=history
                    )
                    
                print(f"📚 Loaded strategies for {len(self.strategies)} players")
            except Exception as e:
                print(f"⚠️  Error loading strategies: {e}")
                print("Starting with default strategies")
                self._initialize_default_strategies()
        else:
            print("📚 No existing strategies found. Initializing defaults.")
            self._initialize_default_strategies()
            
    def _initialize_default_strategies(self):
        """Initialize default strategies for each player"""
        default_strategies = {
            "Alex": {
                "good": "As a good player, I analyze patterns carefully. I watch for hesitation, track who claims to have good cards, and vote to exclude players who seem suspicious or contradictory.",
                "bad": "As the bad player, I must blend in perfectly. I'll claim to have good cards, participate actively in discussions, and deflect suspicion onto others subtly."
            },
            "Blake": {
                "good": "As a good player, I stay calm and logical. I build trust through consistent behavior and focus on identifying inconsistencies in others' claims.",
                "bad": "As the bad player, I maintain my smooth-talking persona. I'll mirror the good players' enthusiasm, occasionally 'admit' to having bad cards to seem honest, and create doubt about the most observant players."
            },
            "Casey": {
                "good": "As a good player, I trust my emotions and instincts. I react strongly to suspicious behavior and rally the team with enthusiasm to play good cards.",
                "bad": "As the bad player, I use my emotional nature as cover. I'll act shocked when bad cards are played, enthusiastically support good plays, and emotionally accuse innocent players."
            },
            "Dana": {
                "good": "As a good player, I focus on facts and evidence. I track voting patterns, analyze card distributions, and use logic to identify the bad player.",
                "bad": "As the bad player, I use logic as my shield. I'll present reasonable arguments, admit to having bad cards when necessary, and use data to misdirect suspicion toward good players."
            }
        }
        
        for player_name, role_strategies in default_strategies.items():
            # Combine both role strategies into one comprehensive strategy
            combined_strategy = f"Good role: {role_strategies['good']}\n\nBad role: {role_strategies['bad']}"
            
            self.strategies[player_name] = PlayerStrategy(
                player_name=player_name,
                current_version=1,
                current_strategy=combined_strategy,
                history=[
                    StrategyEntry(
                        version=1,
                        timestamp=datetime.now().isoformat(),
                        strategy_text=combined_strategy,
                        games_played=0,
                        win_rate=0.0,
                        metadata={"type": "default"}
                    )
                ]
            )
        
        self.save_strategies()
        
    def save_strategies(self):
        """Save current strategies to file"""
        data = {}
        for player_name, strategy in self.strategies.items():
            data[player_name] = {
                'current_version': strategy.current_version,
                'current_strategy': strategy.current_strategy,
                'history': [asdict(entry) for entry in strategy.history]
            }
            
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"💾 Saved strategies to {self.filename}")
        
    def get_strategy(self, player_name: str, role: str = None) -> str:
        """Get current strategy for a player"""
        if player_name not in self.strategies:
            print(f"⚠️  No strategy found for {player_name}, using default")
            self._initialize_default_strategies()
            
        strategy = self.strategies[player_name].current_strategy
        
        # If role is specified, extract role-specific part
        if role:
            # Try multiple formats: "Good role:", "**1. Good Role**", etc.
            role_patterns = [
                f"{role.capitalize()} role:",
                f"**1. {role.capitalize()} Role**" if role == "good" else f"**2. {role.capitalize()} Role**",
                f"{role.upper()} ROLE:",
                f"## {role.capitalize()} Role"
            ]
            
            for pattern in role_patterns:
                if pattern in strategy:
                    # Extract the role-specific section
                    lines = strategy.split('\n')
                    role_section = []
                    in_role = False
                    
                    for line in lines:
                        if pattern in line:
                            in_role = True
                        elif in_role and line.strip():
                            # Stop at next role section (look for other role patterns)
                            is_next_role = any(other_pattern in line for other_pattern in [
                                "role:", "Role**", "ROLE:", "## ", "**1.", "**2."
                            ] if other_pattern not in pattern)
                            if is_next_role:
                                break
                        
                        if in_role:
                            role_section.append(line)
                    
                    if role_section:
                        return '\n'.join(role_section).strip()
                    break
                    
        return strategy
        
    def get_current_version(self, player_name: str) -> int:
        """Get current strategy version for a player"""
        if player_name not in self.strategies:
            self._initialize_default_strategies()
        return self.strategies[player_name].current_version
        
    def update_strategy(self, player_name: str, new_strategy: str, metadata: Dict = None):
        """Update a player's strategy"""
        if player_name not in self.strategies:
            print(f"Creating new strategy entry for {player_name}")
            self.strategies[player_name] = PlayerStrategy(
                player_name=player_name,
                current_version=0,
                current_strategy="",
                history=[]
            )
            
        player_strat = self.strategies[player_name]
        player_strat.current_version += 1
        player_strat.current_strategy = new_strategy
        
        # Add to history
        entry = StrategyEntry(
            version=player_strat.current_version,
            timestamp=datetime.now().isoformat(),
            strategy_text=new_strategy,
            games_played=0,
            win_rate=0.0,
            metadata=metadata or {}
        )
        player_strat.history.append(entry)
        
        # Keep only last 10 versions in history
        if len(player_strat.history) > 10:
            player_strat.history = player_strat.history[-10:]
        
        new_version = player_strat.current_version
            
        self.save_strategies()
        print(f"📝 Updated {player_name}'s strategy to version {player_strat.current_version}")
        return new_version
        
    def record_game_result(self, player_name: str, won: bool):
        """Record a game result for the current strategy"""
        if player_name in self.strategies:
            if self.strategies[player_name].history:
                current = self.strategies[player_name].history[-1]
                current.games_played += 1
                # Update win rate
                wins = current.win_rate * (current.games_played - 1)
                if won:
                    wins += 1
                current.win_rate = wins / current.games_played
                self.save_strategies()
                
    def get_strategy_history(self, player_name: str) -> List[StrategyEntry]:
        """Get the strategy history for a player"""
        if player_name in self.strategies:
            return self.strategies[player_name].history
        return []
        
    def print_player_strategies(self, player_name: str = None):
        """Print strategies for one or all players"""
        print("\n" + "="*60)
        print("PLAYER STRATEGIES")
        print("="*60)
        
        players = [player_name] if player_name else self.strategies.keys()
        
        for name in players:
            if name not in self.strategies:
                continue
                
            strat = self.strategies[name]
            print(f"\n{name.upper()} (Version {strat.current_version})")
            print("-"*40)
            print(strat.current_strategy)
            
            if strat.history and strat.history[-1].games_played > 0:
                current = strat.history[-1]
                print(f"\nPerformance: {current.win_rate:.1%} win rate ({current.games_played} games)")
                
    def export_strategy_evolution(self, player_name: str, output_file: str = None):
        """Export a player's strategy evolution to a file"""
        if player_name not in self.strategies:
            print(f"No strategy found for {player_name}")
            return
            
        if not output_file:
            output_file = f"{player_name}_strategy_evolution.txt"
            
        with open(output_file, 'w') as f:
            f.write(f"STRATEGY EVOLUTION FOR {player_name.upper()}\n")
            f.write("="*60 + "\n\n")
            
            for entry in self.strategies[player_name].history:
                f.write(f"Version {entry.version} - {entry.timestamp}\n")
                f.write("-"*40 + "\n")
                f.write(entry.strategy_text + "\n")
                if entry.games_played > 0:
                    f.write(f"\nPerformance: {entry.win_rate:.1%} win rate ({entry.games_played} games)\n")
                if entry.metadata:
                    f.write(f"Metadata: {json.dumps(entry.metadata, indent=2)}\n")
                f.write("\n" + "="*60 + "\n\n")
                
        print(f"📄 Exported strategy evolution to {output_file}")

# Convenience functions
def get_player_strategy(player_name: str, role: str = None) -> str:
    """Get a player's current strategy"""
    manager = StrategyManager()
    return manager.get_strategy(player_name, role)
    
def update_player_strategy(player_name: str, new_strategy: str, metadata: Dict = None):
    """Update a player's strategy"""
    manager = StrategyManager()
    manager.update_strategy(player_name, new_strategy, metadata)
    
if __name__ == "__main__":
    # Test the strategy manager
    manager = StrategyManager("test_strategies.json")
    
    # Print current strategies
    manager.print_player_strategies()
    
    # Test updating a strategy
    new_alex_strategy = """Good role: As a good player, I've learned to be more subtle in my analysis. I track patterns but don't always voice my suspicions immediately, waiting for the right moment to reveal key insights.

Bad role: As the bad player, I've developed a technique of controlled confusion - occasionally making 'mistakes' that seem genuine, while subtly steering discussions away from real evidence."""
    
    manager.update_strategy("Alex", new_alex_strategy, {"reason": "improved after 10 games"})
    
    # Record some game results
    manager.record_game_result("Alex", won=True)
    manager.record_game_result("Alex", won=False)
    manager.record_game_result("Alex", won=True)
    
    # Export evolution
    manager.export_strategy_evolution("Alex")
    
    print("\n✅ Strategy manager test complete!")