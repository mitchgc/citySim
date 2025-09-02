#!/usr/bin/env python3
"""
Scoresheet module for tracking team and player wins across multiple games
"""

import json
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import os

@dataclass
class GameResult:
    """Record of a single game result"""
    game_id: str
    timestamp: str
    winning_team: str  # 'good' or 'bad'
    players: Dict[str, str]  # player_name -> role
    winner_names: List[str]  # names of players on winning team
    final_score: Dict[str, int]  # {'good': X, 'bad': Y}
    total_rounds: int
    game_duration_seconds: Optional[float] = None

@dataclass 
class PlayerStats:
    """Statistics for an individual player"""
    name: str
    games_played: int = 0
    games_won: int = 0
    times_good: int = 0
    times_bad: int = 0
    wins_as_good: int = 0
    wins_as_bad: int = 0
    
    @property
    def win_rate(self) -> float:
        return self.games_won / self.games_played if self.games_played > 0 else 0.0
    
    @property
    def good_win_rate(self) -> float:
        return self.wins_as_good / self.times_good if self.times_good > 0 else 0.0
    
    @property
    def bad_win_rate(self) -> float:
        return self.wins_as_bad / self.times_bad if self.times_bad > 0 else 0.0

@dataclass
class TeamStats:
    """Statistics for teams"""
    good_wins: int = 0
    bad_wins: int = 0
    total_games: int = 0
    
    @property
    def good_win_rate(self) -> float:
        return self.good_wins / self.total_games if self.total_games > 0 else 0.0
    
    @property
    def bad_win_rate(self) -> float:
        return self.bad_wins / self.total_games if self.total_games > 0 else 0.0

class Scoresheet:
    """Manages game results and statistics"""
    
    def __init__(self, filename: str = "analysis/game_results.json"):
        self.filename = filename
        self.games: List[GameResult] = []
        self.player_stats: Dict[str, PlayerStats] = {}
        self.team_stats = TeamStats()
        self.load_data()
    
    def load_data(self):
        """Load existing data from file"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    
                # Load games
                self.games = [GameResult(**game) for game in data.get('games', [])]
                
                # Load player stats
                player_data = data.get('player_stats', {})
                self.player_stats = {name: PlayerStats(**stats) for name, stats in player_data.items()}
                
                # Load team stats
                team_data = data.get('team_stats', {})
                self.team_stats = TeamStats(**team_data)
                
                print(f"📊 Loaded {len(self.games)} games from {self.filename}")
                
            except Exception as e:
                print(f"⚠️  Error loading scoresheet: {e}")
                print("Starting with empty scoresheet")
        else:
            print(f"📊 No existing scoresheet found. Starting fresh.")
    
    def save_data(self):
        """Save current data to file"""
        data = {
            'games': [asdict(game) for game in self.games],
            'player_stats': {name: asdict(stats) for name, stats in self.player_stats.items()},
            'team_stats': asdict(self.team_stats)
        }
        
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Saved scoresheet to {self.filename}")
    
    def record_game(self, winning_team: str, players: Dict[str, str], 
                   final_score: Dict[str, int], total_rounds: int,
                   game_duration_seconds: Optional[float] = None):
        """Record the result of a game"""
        
        # Generate game ID
        game_id = f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        timestamp = datetime.now().isoformat()
        
        # Determine winners
        winner_names = [name for name, role in players.items() if role == winning_team]
        
        # Create game result
        game_result = GameResult(
            game_id=game_id,
            timestamp=timestamp,
            winning_team=winning_team,
            players=players,
            winner_names=winner_names,
            final_score=final_score,
            total_rounds=total_rounds,
            game_duration_seconds=game_duration_seconds
        )
        
        self.games.append(game_result)
        
        # Update team stats
        self.team_stats.total_games += 1
        if winning_team == 'good':
            self.team_stats.good_wins += 1
        else:
            self.team_stats.bad_wins += 1
        
        # Update player stats
        for player_name, role in players.items():
            if player_name not in self.player_stats:
                self.player_stats[player_name] = PlayerStats(name=player_name)
            
            stats = self.player_stats[player_name]
            stats.games_played += 1
            
            # Track role frequency
            if role == 'good':
                stats.times_good += 1
            else:
                stats.times_bad += 1
            
            # Track wins
            if role == winning_team:
                stats.games_won += 1
                if role == 'good':
                    stats.wins_as_good += 1
                else:
                    stats.wins_as_bad += 1
        
        self.save_data()
        print(f"📝 Recorded game {game_id}: {winning_team.upper()} team wins!")
    
    def print_summary(self):
        """Print a summary of all statistics"""
        print("\n" + "="*60)
        print("🏆 GAME SCORESHEET SUMMARY")
        print("="*60)
        
        if not self.games:
            print("No games recorded yet.")
            return
        
        # Team Statistics
        print(f"\n📊 TEAM STATISTICS ({self.team_stats.total_games} games)")
        print(f"Good team wins: {self.team_stats.good_wins} ({self.team_stats.good_win_rate:.1%})")
        print(f"Bad team wins:  {self.team_stats.bad_wins} ({self.team_stats.bad_win_rate:.1%})")
        
        # Player Statistics
        print(f"\n👥 PLAYER STATISTICS")
        print(f"{'Player':<10} {'Games':<6} {'Wins':<5} {'W%':<6} {'Good':<5} {'Bad':<4} {'G-W%':<6} {'B-W%':<6}")
        print("-" * 60)
        
        # Sort players by win rate
        sorted_players = sorted(self.player_stats.values(), 
                               key=lambda p: (p.win_rate, p.games_played), reverse=True)
        
        for stats in sorted_players:
            print(f"{stats.name:<10} {stats.games_played:<6} {stats.games_won:<5} "
                  f"{stats.win_rate:<6.1%} {stats.times_good:<5} {stats.times_bad:<4} "
                  f"{stats.good_win_rate:<6.1%} {stats.bad_win_rate:<6.1%}")
        
        # Recent Games
        print(f"\n📅 RECENT GAMES (last 5)")
        print("-" * 60)
        for game in self.games[-5:]:
            winners = ', '.join(game.winner_names)
            timestamp = datetime.fromisoformat(game.timestamp).strftime('%m/%d %H:%M')
            print(f"{timestamp} | {game.winning_team.upper()} wins | {winners} | "
                  f"Score {game.final_score['good']}-{game.final_score['bad']} | {game.total_rounds} rounds")
    
    def print_detailed_player_stats(self, player_name: str):
        """Print detailed stats for a specific player"""
        if player_name not in self.player_stats:
            print(f"No stats found for player: {player_name}")
            return
        
        stats = self.player_stats[player_name]
        player_games = [g for g in self.games if player_name in g.players]
        
        print(f"\n🎯 DETAILED STATS FOR {player_name.upper()}")
        print("="*50)
        print(f"Total games: {stats.games_played}")
        print(f"Overall win rate: {stats.win_rate:.1%} ({stats.games_won} wins)")
        print(f"As good player: {stats.times_good} games, {stats.good_win_rate:.1%} win rate")
        print(f"As bad player: {stats.times_bad} games, {stats.bad_win_rate:.1%} win rate")
        
        print(f"\n📊 Game History:")
        for game in player_games[-10:]:  # Show last 10 games
            role = game.players[player_name]
            won = role == game.winning_team
            status = "WIN" if won else "LOSS"
            timestamp = datetime.fromisoformat(game.timestamp).strftime('%m/%d %H:%M')
            print(f"  {timestamp} | {role.upper()} | {status} | {game.final_score['good']}-{game.final_score['bad']}")

# Convenience function for easy import
def create_scoresheet(filename: str = "game_results.json") -> Scoresheet:
    """Create and return a scoresheet instance"""
    return Scoresheet(filename)

if __name__ == "__main__":
    # Demo/test the scoresheet
    scoresheet = Scoresheet("test_results.json")
    
    # Add some sample data
    scoresheet.record_game(
        winning_team="good",
        players={"Alex": "good", "Blake": "bad", "Casey": "good", "Dana": "good"},
        final_score={"good": 5, "bad": 2},
        total_rounds=8
    )
    
    scoresheet.print_summary()