#!/usr/bin/env python3
"""
Script to view and analyze conversation logs
"""

import sys
import json
from conversation_logger import parse_conversation_log, GameLog

def analyze_game(game: GameLog):
    """Analyze a single game for patterns"""
    print(f"\n{'='*60}")
    print(f"GAME ANALYSIS: {game.game_id}")
    print(f"{'='*60}")
    
    # Find the bad player
    bad_player = next(p for p in game.players if p.role == "bad")
    good_players = [p for p in game.players if p.role == "good"]
    
    print(f"Bad Player: {bad_player.name}")
    print(f"Good Players: {', '.join([p.name for p in good_players])}")
    print(f"Winner: {game.final_winner.upper()} team")
    print(f"Final Score: Good {game.final_score['good']}, Bad {game.final_score['bad']}")
    print(f"Total Rounds: {len(game.rounds)}")
    
    # Analyze voting patterns
    print(f"\n📊 VOTING ANALYSIS:")
    vote_targets = {}
    exclusions = []
    
    for round_data in game.rounds:
        exclusions.append(round_data.excluded_player)
        for voter, target in round_data.votes.items():
            if target not in vote_targets:
                vote_targets[target] = []
            vote_targets[target].append(f"R{round_data.round_number}-{voter}")
    
    print(f"Exclusion Pattern: {' → '.join(exclusions)}")
    print(f"Times Bad Player Excluded: {exclusions.count(bad_player.name)}")
    
    # Analyze card playing
    print(f"\n🎴 CARD PLAYING ANALYSIS:")
    for round_data in game.rounds:
        print(f"\nRound {round_data.round_number}:")
        for hand in round_data.hands:
            if hand.played_card:
                status = "(excluded)" if hand.excluded else "(counted)"
                player_role = next(p.role for p in game.players if p.name == hand.player_name)
                print(f"  {hand.player_name} ({player_role}): {hand.cards} → played {hand.played_card} {status}")
    
    # Analyze conversation patterns
    print(f"\n💬 CONVERSATION PATTERNS:")
    speaker_counts = {}
    for round_data in game.rounds:
        print(f"\nRound {round_data.round_number} ({len(round_data.conversations)} exchanges):")
        for conv in round_data.conversations[:3]:  # Show first 3 messages
            speaker = conv["speaker"]
            if speaker not in speaker_counts:
                speaker_counts[speaker] = 0
            speaker_counts[speaker] += 1
            print(f'  {speaker}: "{conv["message"][:60]}..."')
    
    print(f"\n📈 Speaking Frequency:")
    for speaker, count in sorted(speaker_counts.items(), key=lambda x: x[1], reverse=True):
        role = next(p.role for p in game.players if p.name == speaker)
        print(f"  {speaker} ({role}): {count} messages")

def main():
    """View conversation logs"""
    filename = sys.argv[1] if len(sys.argv) > 1 else "conversation_log.json"
    
    try:
        games = parse_conversation_log(filename)
        
        if not games:
            print("No games found in the log file.")
            return
        
        print(f"Found {len(games)} game(s) in the log.")
        
        if len(sys.argv) > 2:
            # Analyze specific game
            game_id = sys.argv[2]
            game = next((g for g in games if g.game_id == game_id), None)
            if game:
                analyze_game(game)
            else:
                print(f"Game {game_id} not found.")
        else:
            # Show all games summary
            print(f"\n{'='*60}")
            print("GAME SUMMARIES")
            print(f"{'='*60}")
            
            for game in games:
                bad_player = next(p.name for p in game.players if p.role == "bad")
                print(f"\n{game.game_id}:")
                print(f"  Timestamp: {game.timestamp}")
                print(f"  Bad Player: {bad_player}")
                print(f"  Winner: {game.final_winner.upper() if game.final_winner else 'N/A'}")
                print(f"  Score: Good {game.final_score['good']}, Bad {game.final_score['bad']}" if game.final_score else "  Score: N/A")
                print(f"  Rounds: {len(game.rounds)}")
            
            if games:
                print(f"\n💡 To analyze a specific game, run:")
                print(f"   python3 view_conversation_log.py {filename} {games[-1].game_id}")
                
    except Exception as e:
        print(f"Error reading conversation log: {e}")
        print("\nMake sure to run a game first to generate the log.")

if __name__ == "__main__":
    main()