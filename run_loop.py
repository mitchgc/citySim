#!/usr/bin/env python3
"""
Full Automation Loop for Mafia Game
Runs: mafia game -> show results -> update strategies -> repeat
"""

import asyncio
import subprocess
import sys
import os
from analysis.scoresheet import Scoresheet
from strategy.update_strategies import update_all_strategies

class GameLoop:
    """Manages the full game automation loop"""
    
    def __init__(self, max_games: int = None, show_detailed_results: bool = True):
        self.max_games = max_games  # None = infinite loop
        self.show_detailed_results = show_detailed_results
        self.games_completed = 0
        
    async def run_single_game(self) -> bool:
        """Run a single mafia game. Returns True if successful."""
        print(f"🎮 Starting Game #{self.games_completed + 1}")
        print("="*60)
        
        try:
            # Run the mafia game
            result = subprocess.run([sys.executable, "mafia.py"], 
                                  capture_output=False, 
                                  text=True, 
                                  cwd=os.getcwd())
            
            if result.returncode == 0:
                self.games_completed += 1
                print(f"\n✅ Game #{self.games_completed} completed successfully!")
                return True
            else:
                print(f"\n❌ Game #{self.games_completed + 1} failed with return code {result.returncode}")
                return False
                
        except Exception as e:
            print(f"❌ Error running game: {e}")
            return False
    
    def show_results(self):
        """Display current scoresheet results"""
        print(f"\n📊 RESULTS AFTER {self.games_completed} GAMES")
        print("="*60)
        
        try:
            scoresheet = Scoresheet()
            scoresheet.print_summary()
            if self.show_detailed_results:
                # Show detailed stats for each player
                players = ["Alex", "Blake", "Casey", "Dana"]
                print("\n📈 DETAILED PLAYER STATISTICS:")
                for player in players:
                    scoresheet.print_detailed_player_stats(player)
        except Exception as e:
            print(f"❌ Error showing results: {e}")
    
    async def update_strategies(self):
        """Update AI player strategies based on recent games"""
        print(f"\n🧠 UPDATING AI STRATEGIES")
        print("="*60)
        
        try:
            await update_all_strategies()
        except Exception as e:
            print(f"❌ Error updating strategies: {e}")
    
    async def run_loop(self):
        """Run the complete automation loop"""
        
        # Clear debug log at start of loop
        with open('analysis/debug.log', 'w') as f:
            f.write('')
        print("🗑️ Cleared debug log")
        
        print("🚀 Starting Mafia Game Automation Loop")
        print("="*80)
        
        if self.max_games:
            print(f"Target: {self.max_games} games")
        else:
            print("Running continuously (Ctrl+C to stop)")
        print()
        
        try:
            while True:
                # Check if we've reached the max games limit
                if self.max_games and self.games_completed >= self.max_games:
                    print(f"\n🏁 Completed {self.games_completed} games. Loop finished!")
                    break
                
                # Run a single game
                success = await self.run_single_game()
                
                if success:
                    # Show results after the game
                    self.show_results()
                    
                    # Update strategies every few games
                    if self.games_completed % 3 == 0:  # Update every 3 games
                        await self.update_strategies()
                    
                    print(f"\n⏭️  Moving to next game...")
                    print("="*60)
                    
                    # Small pause between games
                    await asyncio.sleep(2)
                else:
                    print("❌ Game failed. Stopping loop.")
                    break
                    
        except KeyboardInterrupt:
            print(f"\n\n⏹️  Loop interrupted by user after {self.games_completed} games")
            if self.games_completed > 0:
                print("Final results:")
                self.show_results()
        except Exception as e:
            print(f"\n❌ Unexpected error in loop: {e}")

async def main():
    """Main entry point with command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run automated Mafia game loop")
    parser.add_argument("--games", "-g", type=int, help="Maximum number of games to run (default: infinite)")
    parser.add_argument("--quick", "-q", action="store_true", help="Show summary results only")
    parser.add_argument("--strategy-frequency", "-s", type=int, default=3, 
                       help="Update strategies every N games (default: 3)")
    
    args = parser.parse_args()
    
    # Create and run the game loop
    loop = GameLoop(
        max_games=args.games,
        show_detailed_results=not args.quick
    )
    
    await loop.run_loop()

if __name__ == "__main__":
    asyncio.run(main())