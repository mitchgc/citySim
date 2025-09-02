#!/usr/bin/env python3
"""
Script to view scoresheet statistics without running a game
"""

import sys
from scoresheet import Scoresheet

def main():
    """View scoresheet statistics"""
    filename = sys.argv[1] if len(sys.argv) > 1 else "game_results.json"
    
    scoresheet = Scoresheet(filename)
    
    if len(sys.argv) > 2:
        # Show detailed stats for specific player
        player_name = sys.argv[2]
        scoresheet.print_detailed_player_stats(player_name)
    else:
        # Show summary
        scoresheet.print_summary()

if __name__ == "__main__":
    main()