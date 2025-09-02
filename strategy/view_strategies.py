#!/usr/bin/env python3
"""
Script to view and manage player strategies
"""

import sys
import json
from strategy.strategy_manager import StrategyManager

def main():
    """View and manage strategies"""
    manager = StrategyManager()
    
    if len(sys.argv) == 1:
        # Show all current strategies
        manager.print_player_strategies()
        
    elif len(sys.argv) == 2:
        # Show specific player's strategy
        player_name = sys.argv[1]
        
        if player_name == "--history":
            # Show history for all players
            for name in ["Alex", "Blake", "Casey", "Dana"]:
                history = manager.get_strategy_history(name)
                if history:
                    print(f"\n{'='*60}")
                    print(f"{name.upper()} STRATEGY EVOLUTION")
                    print(f"{'='*60}")
                    for entry in history:
                        print(f"\nVersion {entry.version} ({entry.timestamp[:10]})")
                        print(f"Games: {entry.games_played}, Win Rate: {entry.win_rate:.1%}")
                        if entry.metadata:
                            print(f"Metadata: {entry.metadata}")
        else:
            # Show specific player
            manager.print_player_strategies(player_name)
            
            # Show evolution option
            history = manager.get_strategy_history(player_name)
            if len(history) > 1:
                print(f"\n💡 {player_name} has {len(history)} strategy versions.")
                print(f"   To export full evolution: python3 export_strategy.py {player_name}")
                
    elif len(sys.argv) == 3 and sys.argv[1] == "--export":
        # Export player's strategy evolution
        player_name = sys.argv[2]
        manager.export_strategy_evolution(player_name)
        
    else:
        print("Usage:")
        print("  python3 view_strategies.py              # View all current strategies")
        print("  python3 view_strategies.py Alex         # View Alex's current strategy")
        print("  python3 view_strategies.py --history    # View strategy evolution for all")
        print("  python3 view_strategies.py --export Alex # Export Alex's evolution to file")

if __name__ == "__main__":
    main()