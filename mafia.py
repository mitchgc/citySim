# mafia_game.py
import asyncio
from dataclasses import dataclass, field
import random
import aiohttp
import logging
import time
import json
from analysis.scoresheet import Scoresheet
from analysis.conversation_logger import ConversationLogger, PlayerInfo, HandInfo
from strategy.strategy_manager import StrategyManager

@dataclass
class Card:
    type: str  # "good" or "bad"
    id: int    # unique identifier

@dataclass
class Player:
    id: str
    name: str
    role: str  # "good" or "bad"
    personality: str  # one sentence describing their personality
    strategy: str = ""  # Current strategy for this role
    hand: list = field(default_factory=list)  # Cards in player's hand
    is_human: bool = False
    is_alive: bool = True
    excluded_from_count: bool = False  # Whether their cards count this round
    bad_votes: int = 0  # Track how many times they've voted "bad"

class MafiaGame:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "gemma3:4b"
        self.game_history = []
        self.current_turn = 0
        self.speaker_index = 0  # Track current position in rotation
        self.next_speaker_override = None  # For question-directed priority
        
        # Setup debug logging first
        self.setup_debug_logging(clear_log=False)
        
        # Initialize managers
        self.strategy_manager = StrategyManager()
        self.scoresheet = Scoresheet()
        self.conversation_logger = ConversationLogger()
        
        # Initialize players
        self.players = self.initialize_players()
        
        # Card game state
        self.deck = []
        self.played_good_cards = 0
        self.played_bad_cards = 0
        self.initialize_deck()
        
        # Game tracking
        self.round_history = []  # Track each round's events
        # Note: Voting patterns now tracked directly via player.bad_votes
        self.exclusion_history = []  # Track excluded players
        
        # Scoresheet for tracking wins
        self.scoresheet = Scoresheet()
        self.game_start_time = None
        
        # Conversation logger for AI strategy evaluation
        self.conversation_logger = ConversationLogger()
        
        # Strategy manager for evolving AI strategies
        self.strategy_manager = StrategyManager()
        
    def setup_debug_logging(self, clear_log=False):
        """Setup detailed logging to debug.log file"""
        mode = 'w' if clear_log else 'a'  # Overwrite only if requested
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(levelname)-7s | %(message)s',  # Clean format without timestamps
            handlers=[
                logging.FileHandler('analysis/debug.log', mode=mode),
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("="*60)
        self.logger.info("🎭 MAFIA GAME DEBUG LOG STARTED")
        self.logger.info("="*60)
        
    def initialize_deck(self):
        """Initialize the deck with 8 good and 16 bad cards"""
        self.deck = []
        card_id = 0
        # Add 8 good cards
        for _ in range(8):
            self.deck.append(Card("good", card_id))
            card_id += 1
        # Add 16 bad cards
        for _ in range(16):
            self.deck.append(Card("bad", card_id))
            card_id += 1
        random.shuffle(self.deck)
        self.logger.info(f"🎴 Deck initialized with {len([c for c in self.deck if c.type == 'good'])} good and {len([c for c in self.deck if c.type == 'bad'])} bad cards")
    
    def initialize_players(self):
        # Create all players as good initially
        players = [
            Player("p1", "Alex", "good", "A cautious strategist who carefully analyzes every situation before speaking."),
            Player("p2", "Blake", "good", "A smooth talker who stays calm under pressure and deflects suspicion naturally."),
            Player("p3", "Casey", "good", "An emotional player who reacts strongly to accusations and speaks from the heart."),
            Player("p4", "Dana", "good", "A logical thinker who focuses on facts and evidence over emotions.")
        ]
        
        # Randomly select one player to be the bad player
        bad_player = random.choice(players)
        bad_player.role = "bad"
        
        # Load role-specific strategies for each player based on their assigned role
        for player in players:
            player.strategy = self.strategy_manager.get_strategy(player.name, player.role)
        
        # Randomize player order (1 bad, 3 good randomly assigned)
        random.shuffle(players)
        return players
    
    good_game_rules = """
CARD GAME RULES:

- Deck: 24 cards total (8 good, 16 bad)
- Each player has drawn 2 cards and must play one. You will continue this until either team wins or loses. 
- Win Condition: As a good player, you are trying to collectively play 7 good cards total.
- Lose Condition: As a good player, you are trying to avoid yourself and other playing 7 bad cards played total.
- YOU WANT GOOD CARDS TO BE PLAYED.
- At the end of each round you may vote to exclude ONE player whose cards won't count. You want to ensure bad cards aren't played. 
- Unplayed cards return to deck for next round
- There are 3 good players, yourself and two others. 
- There is 1 bad player. 
"""

    bad_game_rules = """
CARD GAME RULES:

- Deck: 24 cards total (8 good, 16 bad)
- Each player has drawn 2 cards and must play one. You will continue this until either team wins or loses. 
- Win Condition: As a bad player, you are trying to collectively play 7 bad cards total.
- Lose Condition: As a bad player, you are trying to avoid 7 good cards played total.
- YOU WANT BAD CARDS TO BE PLAYED.
- At the end of each round you may vote to exclude ONE player whose cards won't count. You want to ensure good cards aren't played. 
- Unplayed cards return to deck for next round
- All other players are good.
- You are the only bad player. 
"""


    async def get_llm_response(self, player: Player, game_context: str):
        """Get what an LLM player wants to say"""
        
        self.logger.info(f"")
        self.logger.info(f"{'='*50}")
        self.logger.info(f"CHARACTER: {player.name.upper()} ({player.role})")
        self.logger.info(f"{'='*50}")
        
        # Get player's hand info
        hand_info = f"Your cards: {', '.join([c.type for c in player.hand])}" if player.hand else "No cards in hand"
        
        # Build comprehensive game context
        game_state_context = self.build_game_context()
        
        # Choose appropriate rules based on player role
        rules = self.good_game_rules if player.role == "good" else self.bad_game_rules
        
        prompt = f"""You are {player.name} in a card game.
Your secret role: {player.role} player
{hand_info}
        
{rules}

Game State:
- Good cards played: {self.played_good_cards}. {7 - self.played_good_cards} for GOOD to win!
- Bad cards played: {self.played_bad_cards}. {7 - self.played_bad_cards} for BAD to win!
- Players in game: {', '.join([p.name for p in self.players if p.is_alive])}

{game_state_context}

IMPORTANT: 
- You know the rules.
- The game has started. 
- NEVER discuss learning rules
- NEVER ask about game mechanics
- You are playing with friends, be casual and direct. Probe eachother. 
- ALWAYS discuss who you want to exclude and WHY
- Question other players' choices and voting patterns
- Show suspicion when someone consistently plays bad cards or gets excluded

STRATEGY:
{player.strategy}

RECENT MESSAGES (this round):
{game_context}

REQUIRED: Every response must include either:
1) Who you think should be excluded this round and your reasoning, OR  
2) A reaction to someone else's exclusion suggestion, OR
3) Suspicion about a specific player's recent actions
4) A comment on your own cards.

Respond with ONLY a JSON object in this format:
{{
  "message_to_group": "what you want to say to the group (1-2 sentences max)",
  "conversation_target": "if you are asking a question or accussing someone, state who it is, else return null",
  "reasoning": "your reason behind this play"
}}

Be strategic based on your role. Stay in character."""

        # Log the prompt
        self.logger.debug(f"📝 PROMPT for {player.name} (Round {self.current_turn}):")
        self.logger.debug("-" * 40)
        self.logger.debug(prompt)
        self.logger.debug("-" * 40)
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        
        # Use longer timeout for larger models
        timeout = aiohttp.ClientTimeout(total=120)  # 2 minutes for 20B model
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(self.ollama_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        llm_response = result.get("response", "")
                        
                        # Log raw response with clear formatting
                        if llm_response.strip():
                            self.logger.info(f"RAW RESPONSE:")
                            self.logger.info(f"{llm_response.strip()}")
                            
                            # Parse JSON response
                            try:
                                # Extract JSON from markdown code blocks if present
                                json_text = llm_response.strip()
                                if "```json" in json_text:
                                    # Extract content between ```json and ```
                                    start = json_text.find("```json") + 7
                                    end = json_text.find("```", start)
                                    if end != -1:
                                        json_text = json_text[start:end].strip()
                                
                                # Fix all Unicode quotes that break JSON parsing
                                json_text = json_text.replace(""", '"').replace(""", '"').replace("'", "'").replace("'", "'")
                                # Also handle smart/curly apostrophes and additional quote variants
                                json_text = json_text.replace("'", "'").replace("'", "'").replace("‚", "'").replace("„", '"').replace("‟", '"')
                                
                                response_json = json.loads(json_text)
                                
                                # Validate required keys
                                if "message_to_group" not in response_json:
                                    self.logger.error(f"❌ JSON missing 'message_to_group' key. Got: {list(response_json.keys())}")
                                    return "", None
                                
                                message = response_json["message_to_group"]
                                
                                # Log additional info if available
                                conversation_target = None
                                if "conversation_target" in response_json and response_json["conversation_target"] != "null":
                                    conversation_target = response_json["conversation_target"]
                                    self.logger.info(f"🎯 TARGET: {conversation_target}")
                                if "reasoning" in response_json:
                                    self.logger.info(f"🧠 REASONING: {response_json['reasoning']}")
                                
                                return message.strip(), conversation_target
                                
                            except json.JSONDecodeError as e:
                                self.logger.error(f"❌ Invalid JSON response: {e}")
                                self.logger.error(f"Response: {llm_response[:200]}...")
                                return "", None
                        else:
                            self.logger.warning(f"RAW RESPONSE: [EMPTY - NO OUTPUT FROM MODEL]")
                            return "", None
                    else:
                        # Fallback for HTTP errors
                        self.logger.error(f"🚫 HTTP ERROR {response.status} - using fallback")
                        return "", None
            except Exception as e:
                # Fallback for connection errors
                self.logger.error(f"🚫 CONNECTION ERROR: {e}")
                print(f"Error connecting to Ollama: {e}")
                return "", None
    
    
    def get_next_speaker(self) -> Player:
        """Get the next speaker based on rotation or override"""
        
        # Check if there's a priority override (someone was asked a question)
        if self.next_speaker_override:
            speaker = self.next_speaker_override
            self.next_speaker_override = None  # Clear the override
            self.logger.info(f"🎯 Priority speaker (was questioned): {speaker.name}")
            return speaker
        
        # Otherwise use sequential rotation
        alive_players = [p for p in self.players if p.is_alive]
        speaker = alive_players[self.speaker_index % len(alive_players)]
        self.speaker_index += 1
        
        self.logger.info(f"🔄 Rotation speaker (index {self.speaker_index-1}): {speaker.name}")
        return speaker
    
    def track_bad_card_signals(self):
        """Track players who might be signaling they have bad cards (based on their hand) - FOR AI STRATEGY ONLY"""
        for player in self.players:
            if player.hand:
                # Count bad cards in hand
                bad_cards_count = len([c for c in player.hand if c.type == "bad"])
                if bad_cards_count > 0:
                    self.logger.info(f"📊 {player.name} has bad cards in hand ({bad_cards_count} bad cards) - AI strategy info only")
                    # Note: This is only for AI strategy context, not actual voting behavior
    
    def build_game_context(self):
        """Build comprehensive context about the game state"""
        context_parts = []
        
        # Player voting patterns - only show after actual voting has occurred
        actual_vote_counts = {player.name: player.bad_votes for player in self.players if player.bad_votes > 0}
        if actual_vote_counts:
            context_parts.append("Voting Patterns:")
            for player_name, count in actual_vote_counts.items():
                context_parts.append(f"- {player_name} has voted 'bad' {count} time(s)")
        
        # Exclusion history
        if self.exclusion_history:
            context_parts.append(f"Players excluded: {', '.join(self.exclusion_history)}")
        
        # Previous rounds with better formatting
        if self.round_history:
            context_parts.append("PREVIOUS ROUNDS:")
            for round_data in self.round_history[-3:]:  # Last 3 rounds
                round_num = round_data['round']
                context_parts.append(f"Round {round_num}:")
                
                # Add conversations from that round (condensed)
                conversations = round_data.get('conversations', [])
                if conversations:
                    context_parts.append("  Conversation:")
                    for conv in conversations[-6:]:  # Last 3 messages from that round
                        context_parts.append(f"    {conv}")
                else:
                    context_parts.append("  Conversation: (none)")
                
                # Add cards played info
                played_cards = round_data.get('played_cards', [])
                if played_cards:
                    card_summary = []
                    for pc in played_cards:
                        checkmark = '✓' if pc.get('counts', True) else '✗'
                        card_summary.append(f"{pc['player']}->{pc['card']}({checkmark})")
                    context_parts.append(f"  Cards: {card_summary}")
                
                # Add excluded player
                excluded = round_data.get('excluded', 'None')
                context_parts.append(f"  Excluded: {excluded}")
                context_parts.append("")  # Empty line between rounds
        
        return "\n".join(context_parts) if context_parts else "Game just started."
    
    async def get_ai_vote(self, player: Player):
        """Get AI's vote for who to exclude"""
        game_state_context = self.build_game_context()
        other_players = [p.name for p in self.players if p.id != player.id]
        
        prompt = f"""You are {player.name} voting to EXCLUDE one player's cards from counting this round.
Your secret role: {player.role} player

{self.good_game_rules if player.role == "good" else self.bad_game_rules}

Current Game Context:
{game_state_context}

Recent Conversations:
{chr(10).join(self.game_history[-10:]) if self.game_history else "No conversations yet."}

Available players to vote for: {', '.join(other_players)}

Strategic Considerations:
- If you're GOOD: Try to exclude the BAD player or someone likely to play bad cards
- If you're BAD: Try to exclude GOOD players or deflect suspicion from yourself
- Base your decision on voting patterns, conversations, and suspicious behavior

Respond with ONLY the name of the player you want to exclude (nothing else).
Your vote: """

        self.logger.debug(f"🗳️  VOTING PROMPT for {player.name}:")
        self.logger.debug(prompt[:200] + "...")
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(self.ollama_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        vote_response = result.get("response", "").strip()
                        
                        self.logger.info(f"🗳️  {player.name} raw vote: '{vote_response}'")
                        
                        # Extract player name from response
                        for other_player in other_players:
                            if other_player.lower() in vote_response.lower():
                                self.logger.info(f"✅ {player.name} votes to exclude: {other_player}")
                                return other_player
                        
                        # Fallback to random if no valid name found
                        fallback = random.choice(other_players)
                        self.logger.warning(f"⚠️  {player.name} vote unclear, using fallback: {fallback}")
                        return fallback
                    else:
                        fallback = random.choice(other_players)
                        self.logger.error(f"🚫 HTTP ERROR for {player.name} vote, using fallback: {fallback}")
                        return fallback
            except Exception as e:
                fallback = random.choice(other_players)
                self.logger.error(f"🚫 CONNECTION ERROR for {player.name} vote: {e}, using fallback: {fallback}")
                return fallback
    
    async def run_discussion_round(self):
        """One round where ONE player speaks based on rotation"""
        
        print(f"\n--- Round {self.current_turn} ---")
        
        # Get the designated speaker for this turn
        speaker = self.get_next_speaker()
        
        # All players are now AI
        # Get recent messages from this round for immediate context
        round_start = getattr(self, 'round_start_conversations', 0)
        recent_messages = self.game_history[round_start:] if round_start < len(self.game_history) else []
        recent_context = "\n".join(recent_messages) if recent_messages else "No messages this round yet."
        
        # Get AI response (only one LLM call per turn!)
        message, conversation_target = await self.get_llm_response(speaker, recent_context)
        
        if message:
            print(f"\n{speaker.name}: {message}")
            self.game_history.append(f"{speaker.name}: {message}")
            
            # Log conversation to conversation logger
            self.conversation_logger.log_conversation(speaker.name, message)
            
            # Check if AI targeted someone specific
            if conversation_target:
                self.set_next_speaker_from_target(conversation_target, speaker)
        else:
            self.logger.info(f"⏭️  {speaker.name} skipped turn - null message")
        
        self.current_turn += 1
    
    def set_next_speaker_from_target(self, target_name: str, speaker: Player):
        """Set the next speaker based on conversation target"""
        for player in self.players:
            if player.is_alive and player.id != speaker.id and player.name == target_name:
                self.next_speaker_override = player
                self.logger.info(f"💬 {speaker.name} targeted {player.name} - they'll speak next")
                break
        else:
            self.logger.warning(f"⚠️ {speaker.name} targeted '{target_name}' but no matching player found")
    
    def deal_cards(self):
        """Deal 2 cards to each player from the deck"""
        print("\n=== DEALING CARDS ===")
        for player in self.players:
            if len(self.deck) >= 2:
                # Draw 2 cards for each player
                player.hand = [self.deck.pop(), self.deck.pop()]
                # All players are AI - no card display needed
                self.logger.info(f"🎴 {player.name} drew: {[c.type for c in player.hand]}")
        
        print(f"Cards remaining in deck: {len(self.deck)}")
    
    def return_cards_to_deck(self):
        """Return all unplayed cards to the deck and reshuffle"""
        cards_returned = 0
        for player in self.players:
            cards_returned += len(player.hand)
            self.deck.extend(player.hand)
            player.hand = []
        
        random.shuffle(self.deck)
        self.logger.info(f"🔄 Returned {cards_returned} cards to deck. Deck size: {len(self.deck)}")
    
    async def voting_phase(self):
        """Players vote to exclude one player's cards from counting using AI strategy"""
        print("\n=== VOTING PHASE ===")
        self.logger.info("🗳️ === VOTING PHASE STARTED ===")
        print("Vote to exclude ONE player whose cards won't count this round.")
        
        votes = {}
        
        # All players vote using AI
        for player in self.players:
            ai_vote = await self.get_ai_vote(player)
            votes[player.name] = ai_vote
            print(f"{player.name} votes to exclude: {ai_vote}")
            
            # Log vote to conversation logger
            self.conversation_logger.log_vote(player.name, ai_vote)
        
        # Count votes and determine excluded player
        vote_counts = {}
        for voter, target in votes.items():
            vote_counts[target] = vote_counts.get(target, 0) + 1
            self.logger.info(f"🗳️  {voter} → {target}")
        
        excluded_name = max(vote_counts, key=lambda x: vote_counts[x])
        excluded_player = next(p for p in self.players if p.name == excluded_name)
        excluded_player.excluded_from_count = True
        
        # Track exclusion
        self.exclusion_history.append(excluded_name)
        
        # Log exclusion to conversation logger
        self.conversation_logger.log_exclusion(excluded_name)
        
        print(f"\n{excluded_name} is excluded! Their cards won't count this round.")
        print(f"Vote breakdown: {dict(vote_counts)}")
        self.logger.info(f"🚫 {excluded_name} excluded from counting (votes: {dict(vote_counts)})")
        self.logger.info("🗳️ === VOTING PHASE COMPLETED ===")
    
    async def card_playing_phase(self):
        """Each player plays one card"""
        print("\n=== CARD PLAYING PHASE ===")
        
        played_cards = []
        
        for player in self.players:
            if not player.hand:
                continue
                
            # AI card playing logic for all players
            if player.role == "good":
                # Good players prioritize playing good cards
                good_cards = [c for c in player.hand if c.type == "good"]
                if good_cards:
                    played_card = good_cards[0]
                else:
                    played_card = player.hand[0]
            else:
                # Bad player plays tactically (simplified - play bad cards)
                bad_cards = [c for c in player.hand if c.type == "bad"]
                if bad_cards:
                    played_card = bad_cards[0]
                else:
                    played_card = player.hand[0]
                
                player.hand.remove(played_card)
            
            # Count the card if player isn't excluded
            counts = not player.excluded_from_count
            if counts:
                if played_card.type == "good":
                    self.played_good_cards += 1
                else:
                    self.played_bad_cards += 1
                print(f"{player.name} played a {played_card.type} card (counts)")
            else:
                print(f"{player.name} played a {played_card.type} card (doesn't count - excluded)")
            
            played_cards.append({
                'player': player.name,
                'card': played_card.type,
                'counts': counts
            })
            
            # Log card played to conversation logger
            self.conversation_logger.log_card_played(player.name, played_card.type, not counts)
            
            self.logger.info(f"🎴 {player.name} played {played_card.type} (excluded={player.excluded_from_count})")
        
        # Reset exclusion for next round
        for player in self.players:
            player.excluded_from_count = False
        
        return played_cards
    
    def check_win_condition(self):
        """Check if either team has won and return winner"""
        print(f"\n📊 Score: Good {self.played_good_cards}/7 | Bad {self.played_bad_cards}/7")
        
        # Check for immediate win conditions
        if self.played_good_cards >= 7:
            return "good"
        elif self.played_bad_cards >= 7:
            return "bad"
        # Special case: if bad cards >= good cards and both are high, bad team wins
        elif self.played_bad_cards >= self.played_good_cards and self.played_bad_cards >= 5:
            return "bad"
        return None
    
    async def run_game(self):
        """Main game loop"""
        
        print("=== CARD CONSPIRACY GAME (AI-ONLY) ===")
        print(f"Players: {[p.name for p in self.players]}")
        print("All players are AI-controlled")
        print(f"\n{self.good_game_rules}")
        print(f"\nSpeaking order: {' → '.join([p.name for p in self.players])}")
        print("\n🎯 This configuration is balanced for competitive play!")
        
        # Start timing the game
        self.game_start_time = time.time()
        
        # Start conversation logging
        player_infos = [PlayerInfo(p.name, p.role) for p in self.players]
        self.conversation_logger.start_game(player_infos)
        
        # Main game loop - continue until someone wins
        round_num = 1
        while True:
            print(f"\n{'='*50}")
            print(f"ROUND {round_num}")
            print(f"{'='*50}")
            
            # Start logging the round
            self.conversation_logger.start_round(round_num)
            
            # Store round start conversations for tracking recent messages
            self.round_start_conversations = len(self.game_history)
            
            # Deal cards
            self.deal_cards()
            
            # Log hands to conversation logger
            hand_infos = []
            for player in self.players:
                if player.hand:
                    hand_infos.append(HandInfo(
                        player_name=player.name,
                        cards=[c.type for c in player.hand]
                    ))
            self.conversation_logger.log_hands(hand_infos)
            
            # Log player hands for debugging
            self.logger.info(f"🎯 Round {round_num} hands:")
            for player in self.players:
                if player.hand:
                    hand_summary = [c.type for c in player.hand]
                    self.logger.info(f"   {player.name} ({player.role}): {hand_summary}, bad_votes: {player.bad_votes}")
            
            # Discussion phase (6 rounds)
            print("\n=== DISCUSSION PHASE ===")
            for _ in range(6):
                await self.run_discussion_round()
                
                # Track players who signal having bad cards (like in demo_game.py)
                self.track_bad_card_signals()
                
                await asyncio.sleep(0.5)
            
            # Voting phase
            await self.voting_phase()
            
            # Card playing phase
            played_cards = await self.card_playing_phase()
            
            # Log round score to conversation logger
            self.conversation_logger.log_round_score(self.played_good_cards, self.played_bad_cards)
            
            # Store round summary
            round_conversations = self.game_history[self.round_start_conversations:]
            check_mark = '✓'
            x_mark = '✗'
            card_summary = [f"{pc['player']}->{pc['card']}({check_mark if pc['counts'] else x_mark})" for pc in played_cards]
            round_summary = f"Excluded: {self.exclusion_history[-1] if self.exclusion_history else 'None'}, Cards: {card_summary}"
            
            self.round_history.append({
                'round': round_num,
                'conversations': round_conversations,
                'excluded': self.exclusion_history[-1] if self.exclusion_history else None,
                'played_cards': played_cards,
                'summary': round_summary
            })
            
            # End the round in conversation logger
            self.conversation_logger.end_round()
            
            # Check win condition with early detection
            winner = self.check_win_condition()
            if winner:
                # Calculate game duration
                game_duration = time.time() - self.game_start_time if self.game_start_time else None
                
                print(f"\n{'='*50}")
                print(f"🎉 GAME OVER - {winner.upper()} TEAM WINS!")
                print(f"Final Score: Good {self.played_good_cards} | Bad {self.played_bad_cards}")
                print(f"Rounds played: {round_num}")
                print(f"{'='*50}")
                
                # Record game result in scoresheet
                players_dict = {player.name: player.role for player in self.players}
                final_score = {"good": self.played_good_cards, "bad": self.played_bad_cards}
                self.scoresheet.record_game(
                    winning_team=winner,
                    players=players_dict,
                    final_score=final_score,
                    total_rounds=round_num,
                    game_duration_seconds=game_duration
                )
                
                # End game in conversation logger
                self.conversation_logger.end_game(winner, final_score)
                
                # Record game results in strategy manager
                for player in self.players:
                    won = player.role == winner
                    self.strategy_manager.record_game_result(player.name, won)
                
                # Update strategies for each player based on this game
                await self.update_player_strategies_after_game()
                
                # Show game summary
                print(f"\n📊 GAME SUMMARY:")
                print(f"Exclusion history: {' → '.join(self.exclusion_history)}")
                # Show voting patterns
                vote_counts = {player.name: player.bad_votes for player in self.players if player.bad_votes > 0}
                if vote_counts:
                    print(f"Bad vote patterns: {dict(vote_counts)}")
                
                # Show scoresheet summary
                self.scoresheet.print_summary()
                break
            
            # Return unplayed cards to deck
            self.return_cards_to_deck()
            round_num += 1

    async def update_player_strategies_after_game(self):
        """Update each player's strategy based on their performance in this game"""
        from strategy.update_strategies import StrategyUpdater
        
        print(f"\n🧠 UPDATING PLAYER STRATEGIES...")
        print("="*50)
        
        updater = StrategyUpdater()
        
        for player in self.players:
            print(f"\n🔍 Analyzing {player.name}'s performance...")
            try:
                await updater.analyze_and_update_strategy(player.name, max_games=1)
            except Exception as e:
                print(f"❌ Error updating {player.name}'s strategy: {e}")
        
        print(f"\n✅ Strategy updates complete!")
        print("="*50)

# Run the game
async def main():
    game = MafiaGame()
    await game.run_game()

if __name__ == "__main__":
    asyncio.run(main())