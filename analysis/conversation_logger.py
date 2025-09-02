#!/usr/bin/env python3
"""
Conversation Logger for AI Strategy Evaluation
Tracks game conversations, hands, and decisions round by round
"""

import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict, field

@dataclass
class PlayerInfo:
    """Information about a player"""
    name: str
    role: str  # 'good' or 'bad'
    
@dataclass
class HandInfo:
    """Information about a player's hand"""
    player_name: str
    cards: List[str]  # e.g., ['good', 'bad']
    played_card: Optional[str] = None
    excluded: bool = False
    
@dataclass
class RoundData:
    """Data for a single round"""
    round_number: int
    conversations: List[Dict[str, str]]  # List of {speaker: message} dicts
    hands: List[HandInfo]
    votes: Dict[str, str]  # voter -> target
    excluded_player: str
    cards_played: Dict[str, str]  # player -> card type
    round_score: Dict[str, int]  # {'good': X, 'bad': Y}
    
@dataclass 
class GameLog:
    """Complete game log"""
    game_id: str
    timestamp: str
    players: List[PlayerInfo]
    rounds: List[RoundData] = field(default_factory=list)
    final_winner: Optional[str] = None
    final_score: Optional[Dict[str, int]] = None

class ConversationLogger:
    """Logs game conversations and states for AI analysis"""
    
    def __init__(self, filename: str = "analysis/conversation_log.txt"):
        self.filename = filename
        self.json_filename = filename.replace('.txt', '.json')
        self.current_game: Optional[GameLog] = None
        self.current_round: Optional[RoundData] = None
        
    def start_game(self, players: List[PlayerInfo]):
        """Start logging a new game"""
        self.current_game = GameLog(
            game_id=f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now().isoformat(),
            players=players
        )
        self.current_round = None
        self._write_header()
        
    def start_round(self, round_number: int):
        """Start logging a new round"""
        if not self.current_game:
            raise ValueError("Must call start_game before start_round")
            
        self.current_round = RoundData(
            round_number=round_number,
            conversations=[],
            hands=[],
            votes={},
            excluded_player="",
            cards_played={},
            round_score={"good": 0, "bad": 0}
        )
        
    def log_conversation(self, speaker: str, message: str):
        """Log a conversation turn"""
        if not self.current_round:
            raise ValueError("Must call start_round before logging conversations")
            
        self.current_round.conversations.append({
            "speaker": speaker,
            "message": message
        })
        
    def log_hands(self, hands: List[HandInfo]):
        """Log all player hands for the round"""
        if not self.current_round:
            raise ValueError("Must call start_round before logging hands")
            
        self.current_round.hands = hands
        
    def log_vote(self, voter: str, target: str):
        """Log a vote"""
        if not self.current_round:
            raise ValueError("Must call start_round before logging votes")
            
        self.current_round.votes[voter] = target
        
    def log_exclusion(self, excluded_player: str):
        """Log who was excluded"""
        if not self.current_round:
            raise ValueError("Must call start_round before logging exclusion")
            
        self.current_round.excluded_player = excluded_player
        
    def log_card_played(self, player: str, card: str, excluded: bool = False):
        """Log a card played by a player"""
        if not self.current_round:
            raise ValueError("Must call start_round before logging cards")
            
        self.current_round.cards_played[player] = card
        
        # Update hand info with played card
        for hand in self.current_round.hands:
            if hand.player_name == player:
                hand.played_card = card
                hand.excluded = excluded
                break
                
    def log_round_score(self, good_score: int, bad_score: int):
        """Log the score at end of round"""
        if not self.current_round:
            raise ValueError("Must call start_round before logging score")
            
        self.current_round.round_score = {"good": good_score, "bad": bad_score}
        
    def end_round(self):
        """Finish logging the current round"""
        if not self.current_game or not self.current_round:
            raise ValueError("No active round to end")
            
        self.current_game.rounds.append(self.current_round)
        self._write_round(self.current_round)
        self.current_round = None
        
    def end_game(self, winner: str, final_score: Dict[str, int]):
        """Finish logging the game"""
        if not self.current_game:
            raise ValueError("No active game to end")
            
        self.current_game.final_winner = winner
        self.current_game.final_score = final_score
        
        self._write_summary()
        self._save_json()
        self.current_game = None
        
    def _write_header(self):
        """Write game header to text file"""
        with open(self.filename, 'w') as f:
            f.write("="*60 + "\n")
            f.write(f"GAME LOG: {self.current_game.game_id}\n")
            f.write(f"Timestamp: {self.current_game.timestamp}\n")
            f.write("="*60 + "\n\n")
            
            f.write("-"*40 + "\n")
            f.write("PLAYER ROLES:\n")
            f.write("-"*40 + "\n")
            for player in self.current_game.players:
                f.write(f"{player.name}: {player.role.upper()}\n")
            f.write("-"*40 + "\n\n")
            
    def _write_round(self, round_data: RoundData):
        """Write round data to text file"""
        with open(self.filename, 'a') as f:
            f.write("="*60 + "\n")
            f.write(f"ROUND {round_data.round_number}\n")
            f.write("="*60 + "\n\n")
            
            # Conversations
            f.write("CONVERSATION:\n")
            f.write("-"*40 + "\n")
            for conv in round_data.conversations:
                f.write(f'{conv["speaker"]}: "{conv["message"]}"\n')
            f.write("\n")
            
            # Hands and cards played
            f.write("HANDS:\n")
            f.write("-"*40 + "\n")
            for hand in round_data.hands:
                cards_str = ", ".join(hand.cards)
                played_str = f" <- played {hand.played_card}" if hand.played_card else ""
                excluded_str = " (EXCLUDED)" if hand.excluded else ""
                f.write(f"{hand.player_name}: [{cards_str}]{played_str}{excluded_str}\n")
            f.write("\n")
            
            # Voting
            f.write("VOTING:\n")
            f.write("-"*40 + "\n")
            for voter, target in round_data.votes.items():
                f.write(f"{voter} -> {target}\n")
            f.write(f"Excluded: {round_data.excluded_player}\n\n")
            
            # Round score
            f.write("ROUND SCORE:\n")
            f.write("-"*40 + "\n")
            f.write(f"Good: {round_data.round_score['good']}/5\n")
            f.write(f"Bad: {round_data.round_score['bad']}/5\n")
            f.write("\n")
            
    def _write_summary(self):
        """Write game summary to text file"""
        with open(self.filename, 'a') as f:
            f.write("="*60 + "\n")
            f.write("GAME SUMMARY\n")
            f.write("="*60 + "\n")
            f.write(f"Winner: {self.current_game.final_winner.upper()} TEAM\n")
            f.write(f"Final Score: Good {self.current_game.final_score['good']}/5, ")
            f.write(f"Bad {self.current_game.final_score['bad']}/5\n")
            f.write(f"Total Rounds: {len(self.current_game.rounds)}\n")
            f.write("="*60 + "\n")
            
    def _save_json(self):
        """Save structured data as JSON for programmatic analysis"""
        game_dict = asdict(self.current_game)
        
        # Load existing games if file exists
        try:
            with open(self.json_filename, 'r') as f:
                all_games = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            all_games = []
            
        all_games.append(game_dict)
        
        with open(self.json_filename, 'w') as f:
            json.dump(all_games, f, indent=2)
            
        print(f"📝 Game log saved to {self.filename}")
        print(f"📊 JSON data saved to {self.json_filename}")

def parse_conversation_log(filename: str = "conversation_log.json") -> List[GameLog]:
    """Parse conversation logs for AI analysis"""
    try:
        with open(filename, 'r') as f:
            games_data = json.load(f)
            
        games = []
        for game_data in games_data:
            # Convert dictionaries back to dataclass instances
            players = [PlayerInfo(**p) for p in game_data['players']]
            
            rounds = []
            for round_data in game_data['rounds']:
                hands = [HandInfo(**h) for h in round_data['hands']]
                round_obj = RoundData(
                    round_number=round_data['round_number'],
                    conversations=round_data['conversations'],
                    hands=hands,
                    votes=round_data['votes'],
                    excluded_player=round_data['excluded_player'],
                    cards_played=round_data['cards_played'],
                    round_score=round_data['round_score']
                )
                rounds.append(round_obj)
                
            game = GameLog(
                game_id=game_data['game_id'],
                timestamp=game_data['timestamp'],
                players=players,
                rounds=rounds,
                final_winner=game_data.get('final_winner'),
                final_score=game_data.get('final_score')
            )
            games.append(game)
            
        return games
        
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error parsing conversation log: {e}")
        return []

if __name__ == "__main__":
    # Demo/test the conversation logger
    logger = ConversationLogger("test_conversation_log.txt")
    
    # Start a game
    players = [
        PlayerInfo("Alex", "good"),
        PlayerInfo("Blake", "bad"),
        PlayerInfo("Casey", "good"),
        PlayerInfo("Dana", "good")
    ]
    logger.start_game(players)
    
    # Log Round 1
    logger.start_round(1)
    
    # Log conversations
    logger.log_conversation("Alex", "I have a good card to play")
    logger.log_conversation("Blake", "Me too, let's do this")
    logger.log_conversation("Casey", "I'm excited!")
    logger.log_conversation("Dana", "Let's be logical about this")
    
    # Log hands
    hands = [
        HandInfo("Alex", ["good", "bad"]),
        HandInfo("Blake", ["bad", "bad"]),
        HandInfo("Casey", ["good", "good"]),
        HandInfo("Dana", ["bad", "good"])
    ]
    logger.log_hands(hands)
    
    # Log votes
    logger.log_vote("Alex", "Blake")
    logger.log_vote("Blake", "Casey")
    logger.log_vote("Casey", "Blake")
    logger.log_vote("Dana", "Blake")
    logger.log_exclusion("Blake")
    
    # Log cards played
    logger.log_card_played("Alex", "good")
    logger.log_card_played("Blake", "bad", excluded=True)
    logger.log_card_played("Casey", "good")
    logger.log_card_played("Dana", "good")
    
    # Log round score
    logger.log_round_score(3, 0)
    logger.end_round()
    
    # End game
    logger.end_game("good", {"good": 5, "bad": 2})
    
    print("\n✅ Test conversation log created successfully!")