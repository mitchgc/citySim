#!/usr/bin/env python3
"""
Script for AI players to analyze their game logs and update their strategies
"""

import asyncio
import aiohttp
import json
import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis.conversation_logger import parse_conversation_log
from strategy.strategy_manager import StrategyManager
from typing import List, Dict

class StrategyUpdater:
    """Helps AI players analyze games and update their strategies"""
    
    def __init__(self):
        self.strategy_manager = StrategyManager()
        self.ollama_url = "http://localhost:11434/api/generate"
        
        # Setup logging to append to debug log
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.FileHandler('analysis/debug.log', mode='a')
            handler.setFormatter(logging.Formatter('%(levelname)-7s | %(message)s'))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)
        
    async def analyze_and_update_strategy(self, player_name: str, max_games: int = 5):
        """Analyze recent games and generate an updated strategy"""
        
        # Parse conversation logs
        try:
            games = parse_conversation_log("analysis/conversation_log.json")
        except:
            print(f"No game logs found for analysis")
            return
            
        # Filter games with this player
        player_games = []
        for game in games[-max_games:]:  # Look at last N games
            for player in game.players:
                if player.name == player_name:
                    player_games.append({
                        'game': game,
                        'role': player.role
                    })
                    break
                    
        if not player_games:
            print(f"⚠️ No recent games found for {player_name}")
            return
        
        if len(player_games) < 1:
            print(f"⚠️ Not enough games to analyze for {player_name} (found {len(player_games)})")
            return
            
        # Get current strategy info
        current_strategy = self.strategy_manager.get_strategy(player_name)
        current_version = self.strategy_manager.get_current_version(player_name)
        
        # Calculate win rate from recent games
        wins = sum(1 for game_data in player_games if self._player_won(game_data, player_name))
        total_games = len(player_games)
        win_rate = wins / total_games if total_games > 0 else 0.0
        
        # Clean, systematic logging
        self.logger.info(f"")
        self.logger.info(f"🧠 STRATEGY UPDATE CHECK: {player_name}")
        self.logger.info(f"   Current Strategy Version: {current_version}")
        self.logger.info(f"   Games Analyzed: {total_games}")
        self.logger.info(f"   Wins: {wins}")
        self.logger.info(f"   Win Rate: {win_rate:.1%}")
        
        # Decision on whether to update
        should_update = win_rate <= 0.5
        self.logger.info(f"   Update Decision: {'YES (≤50% win rate)' if should_update else 'NO (>50% win rate)'}")
        
        if should_update:
            self.logger.info(f"   LLM Prompt: Generating strategy update...")
            
            # Build analysis prompt
            prompt = await self._build_analysis_prompt(player_name, player_games, current_strategy)
            
            # Get AI's strategy update
            new_strategy = await self._get_llm_strategy_update(prompt)
            
            self.logger.info(f"   LLM Response: {'Generated new strategy' if new_strategy else 'No strategy generated'}")
            
            if new_strategy and new_strategy != current_strategy:
                # Update the strategy
                metadata = {
                    "games_analyzed": total_games,
                    "method": "self-reflection",
                    "win_rate": win_rate
                }
                new_version = self.strategy_manager.update_strategy(player_name, new_strategy, metadata)
                self.logger.info(f"   Strategies.json: UPDATED to version {new_version}")
                print(f"✅ Updated {player_name}'s strategy (v{current_version} → v{new_version}, win rate: {win_rate:.1%})")
            else:
                self.logger.info(f"   Strategies.json: NO CHANGE (same strategy)")
                print(f"❌ No strategy update for {player_name} (win rate: {win_rate:.1%})")
        else:
            self.logger.info(f"   LLM Prompt: SKIPPED")
            self.logger.info(f"   LLM Response: SKIPPED") 
            self.logger.info(f"   Strategies.json: NO CHANGE")
            print(f"🎯 {player_name} performing well (v{current_version}, win rate: {win_rate:.1%}) - keeping current strategy")
        
        self.logger.info(f"")
            
    async def _build_analysis_prompt(self, player_name: str, games: List[Dict], current_strategy: str) -> str:
        """Build a prompt for the AI to analyze its performance"""
        
        # Read the conversation log text file directly
        try:
            with open("analysis/conversation_log.txt", "r") as f:
                conversation_log_text = f.read()
        except:
            conversation_log_text = "No conversation log available."
        
        prompt = f"""You are {player_name}, an AI player in a card conspiracy game. 
You need to analyze your recent game performance and update your strategy.

CURRENT STRATEGY:
{current_strategy}

COMPLETE RECENT GAME LOGS:
{conversation_log_text}

Focus your analysis specifically on YOUR performance as {player_name}. Look for:
- What you said and how other players reacted
- Your voting patterns and card play decisions  
- Whether you were suspected or trusted
- What strategies worked or failed for you
- How you could improve your deception/detection skills
                   
REQUIRED OUTPUT FORMAT:
Respond with ONLY a valid JSON object in this exact format:

{{
  "GoodRoleStrategy": "Your strategy for playing as a good player - what you should do, say, and how to behave to help the good team win and identify the bad player",
  "BadRoleStrategy": "Your strategy for playing as a bad player - how to deceive others, blend in with good players, and help the bad team win"
}}

Make each strategy string concise but specific. Include concrete tactics and behaviors.
Respond with ONLY the JSON object, no other text:"""
        
        return prompt
        
    async def _get_llm_strategy_update(self, prompt: str) -> str:
        """Get strategy update from LLM"""
        
        data = {
            "model": "gpt-oss:20b",
            "prompt": prompt,
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.ollama_url, json=data, timeout=90) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get('response', '').strip()
                        
                        # Log raw response to debug log
                        self.logger.info(f"RAW STRATEGY RESPONSE for LLM:")
                        self.logger.info(f"{response_text}")
                        
                        if not response_text:
                            print("⚠️ LLM returned empty response")
                            return ""
                        
                        # Parse JSON response
                        try:
                            strategy_json = json.loads(response_text)
                            
                            # Validate required keys
                            if "GoodRoleStrategy" not in strategy_json or "BadRoleStrategy" not in strategy_json:
                                print(f"⚠️ JSON missing required keys. Got: {list(strategy_json.keys())}")
                                return ""
                            
                            # Format as text strategy
                            good_strategy = strategy_json["GoodRoleStrategy"]
                            bad_strategy = strategy_json["BadRoleStrategy"]
                            
                            formatted_strategy = f"Good role: {good_strategy}\n\nBad role: {bad_strategy}"
                            return formatted_strategy
                            
                        except json.JSONDecodeError as e:
                            print(f"⚠️ Invalid JSON response: {e}")
                            print(f"Response: {response_text[:200]}...")
                            return ""
                    else:
                        print(f"⚠️ HTTP error {response.status}: {await response.text()}")
                        
        except Exception as e:
            print(f"❌ Error getting strategy update: {e}")
            
        return ""

    def _player_won(self, game_data: Dict, player_name: str) -> bool:
        """Check if a player won their game"""
        game = game_data['game']
        player_role = game_data['role']
        
        # Check if the game has a final winner
        if hasattr(game, 'final_winner') and game.final_winner:
            return game.final_winner == player_role
        
        # Fallback: check final score
        if hasattr(game, 'final_score') and game.final_score:
            good_score = game.final_score.get('good', 0)
            bad_score = game.final_score.get('bad', 0)
            
            if player_role == 'good':
                return good_score >= 7  # Good team wins at 7 points
            else:
                return bad_score >= 7   # Bad team wins at 7 points
        
        return False  # No winner data available

async def update_all_strategies():
    """Update strategies for all players"""
    updater = StrategyUpdater()
    
    players = ["Alex", "Blake", "Casey", "Dana"]
    
    print("🤖 Updating AI Player Strategies...")
    print("="*50)
    
    for player in players:
        print(f"\nAnalyzing {player}'s performance...")
        await updater.analyze_and_update_strategy(player)
        
    print("\n✅ Strategy update complete!")
    
    # Show updated strategies
    updater.strategy_manager.print_player_strategies()

async def update_single_strategy(player_name: str):
    """Update strategy for a single player"""
    updater = StrategyUpdater()
    
    print(f"🤖 Updating strategy for {player_name}...")
    await updater.analyze_and_update_strategy(player_name)
    
    # Show the updated strategy
    updater.strategy_manager.print_player_strategies(player_name)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Update specific player
        player = sys.argv[1]
        asyncio.run(update_single_strategy(player))
    else:
        # Update all players
        asyncio.run(update_all_strategies())