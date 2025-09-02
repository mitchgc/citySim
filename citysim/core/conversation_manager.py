#!/usr/bin/env python3
"""
Conversation Manager - Core turn-based conversation system with interjections

Manages the round-based conversation flow where NPCs speak in order,
with the ability to interject once per round for dramatic moments.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import logging

class TurnType(Enum):
    STANDARD = "standard"

@dataclass
class Turn:
    """A single turn in the conversation"""
    speaker: str
    type: TurnType
    round_number: int
    content: Optional[str] = None  # What they said
    action: Optional[str] = None   # Physical action
    tone: Optional[str] = None     # Emotional tone
    target: Optional[str] = None  # Who they're targeting to speak next

@dataclass
class ConversationState:
    """Current state of the conversation"""
    current_round: int = 1
    current_turn: int = 0
    turns_taken: List[Turn] = field(default_factory=list)
    exit_requests: Dict[str, bool] = field(default_factory=dict)
    conversation_energy: str = "high"  # high, medium, low
    forced_exit_round: int = 8  # Must exit by this round
    speakers_this_round: List[str] = field(default_factory=list)  # Track who has spoken this round
    turns_this_round: Dict[str, int] = field(default_factory=dict)  # Track turn count per character this round
    interjections_this_round: Dict[str, bool] = field(default_factory=dict)  # Track who has interjected this round

class ConversationManager:
    """Manages turn-based conversations with targeting system (like mafia.py)"""
    
    def __init__(self, characters: List[str]):
        self.characters = characters
        self.state = ConversationState()
        self.logger = logging.getLogger(__name__)
        
        # Mafia-style turn management
        self.speaker_index = 0
        self.next_speaker_override = None  # For question-directed priority
        
    def get_next_speaker(self) -> str:
        """Get the next speaker based on rotation or override (like mafia.py)"""
        
        # Check if there's a priority override (someone was targeted)
        if self.next_speaker_override:
            speaker = self.next_speaker_override
            self.next_speaker_override = None  # Clear the override
            self.logger.info(f"🎯 Priority speaker (was targeted): {speaker}")
            return speaker
        
        # Otherwise use sequential rotation
        speaker = self.characters[self.speaker_index % len(self.characters)]
        self.speaker_index += 1
        
        self.logger.info(f"🔄 Rotation speaker (index {self.speaker_index-1}): {speaker}")
        return speaker
        
    def set_next_speaker_from_target(self, target_name: str, current_speaker: str):
        """Set the next speaker based on conversation target (like mafia.py)"""
        if target_name and target_name in self.characters and target_name != current_speaker:
            # Check if target has already reached their 2-turn limit this round
            target_turns = self.state.turns_this_round.get(target_name, 0)
            if target_turns >= 2:
                self.logger.info(f"🚫 {current_speaker} targeted {target_name} but they've reached 2-turn limit this round")
                return  # Don't set override, continue with normal rotation
                
            self.next_speaker_override = target_name
            self.logger.info(f"💬 {current_speaker} targeted {target_name} - they'll speak next")
        else:
            if target_name and target_name not in self.characters:
                self.logger.warning(f"⚠️ {current_speaker} targeted '{target_name}' but no matching character found")
                
    def can_exit_conversation(self) -> bool:
        """Check if characters can request to exit (rounds 4-7)"""
        return 4 <= self.state.current_round <= 7
        
    def must_exit_conversation(self) -> bool:
        """Check if conversation must end (round 8+)"""
        return self.state.current_round >= self.state.forced_exit_round
        
    def add_turn(self, speaker: str, content: str, action: Optional[str] = None, 
                tone: Optional[str] = None, target: Optional[str] = None) -> Turn:
        """Add a turn to the conversation history"""
        
        # Log Round 1 on the very first turn
        if self.state.current_turn == 0:
            self.logger.info(f"")
            self.logger.info(f"{'='*50}")
            self.logger.info(f"ROUND {self.state.current_round}")
            self.logger.info(f"{'='*50}")
            
        turn = Turn(
            speaker=speaker,
            type=TurnType.STANDARD,
            round_number=self.state.current_round,
            content=content,
            action=action,
            tone=tone,
            target=target
        )
        self.state.turns_taken.append(turn)
        self.state.current_turn += 1
        
        # Track that this speaker has spoken this round
        if speaker not in self.state.speakers_this_round:
            self.state.speakers_this_round.append(speaker)
            
        # Track turn count per character this round
        self.state.turns_this_round[speaker] = self.state.turns_this_round.get(speaker, 0) + 1
        turns_count = self.state.turns_this_round[speaker]
        
        self.logger.info(f"Turn {self.state.current_turn}: {speaker} in round {self.state.current_round} (turn {turns_count}/2 for this character this round)")
        
        # Handle targeting
        if target:
            self.set_next_speaker_from_target(target, speaker)
            
        # Check if round should end (all characters have spoken)
        if self.should_advance_round():
            self.start_new_round()
            
        return turn
        
    def should_advance_round(self) -> bool:
        """Check if round should advance based on turn limits and participation"""
        # Advance if all characters have reached their 2-turn limit
        all_at_limit = all(
            self.state.turns_this_round.get(char, 0) >= 2 
            for char in self.characters
        )
        if all_at_limit:
            return True
            
        # Also advance if everyone has spoken at least once (traditional rule)
        # This allows shorter rounds if natural conversation lulls
        all_have_spoken = set(self.state.speakers_this_round) == set(self.characters)
        return all_have_spoken
        
    def can_interject(self, character: str) -> bool:
        """Check if character can interject this round"""
        return not self.state.interjections_this_round.get(character, False)
        
    def mark_interjection(self, character: str):
        """Mark that character has used their interjection this round"""
        self.state.interjections_this_round[character] = True
        self.logger.info(f"🎯 {character} has used their interjection for round {self.state.current_round}")
        
    def start_new_round(self):
        """Start a new conversation round"""
        self.state.current_round += 1
        
        # Add prominent round announcement like character announcements
        self.logger.info(f"")
        self.logger.info(f"{'='*50}")
        self.logger.info(f"ROUND {self.state.current_round}")
        self.logger.info(f"{'='*50}")
        
        # Reset round tracking
        self.state.speakers_this_round = []
        self.state.turns_this_round = {}  # Reset turn counts per character
        self.state.interjections_this_round = {}
        
        # Update conversation energy based on round
        if self.state.current_round <= 3:
            self.state.conversation_energy = "high"
        elif self.state.current_round <= 6:
            self.state.conversation_energy = "medium"
        else:
            self.state.conversation_energy = "low"
            
    def get_recent_turns(self, limit: int = 3) -> List[Turn]:
        """Get the most recent turns for context"""
        return self.state.turns_taken[-limit:] if self.state.turns_taken else []
        
    def get_all_beat_turns(self) -> List[Turn]:
        """Get all turns from this beat for conversation context"""
        return self.state.turns_taken
        
    def get_conversation_summary(self) -> Dict:
        """Get summary of conversation state"""
        return {
            "current_round": self.state.current_round,
            "current_turn": self.state.current_turn,
            "total_turns": len(self.state.turns_taken),
            "can_exit": self.can_exit_conversation(),
            "must_exit": self.must_exit_conversation(),
            "conversation_energy": self.state.conversation_energy
        }
        
    def request_exit(self, character: str) -> bool:
        """Character requests to exit conversation"""
        if not self.can_exit_conversation():
            return False
            
        self.state.exit_requests[character] = True
        self.logger.info(f"🚪 {character} requests to exit conversation")
        return True
        
    def should_end_conversation(self) -> Tuple[bool, str]:
        """
        Check if conversation should end
        Returns (should_end, reason)
        """
        # Must exit after round 8
        if self.must_exit_conversation():
            return True, "maximum_rounds_reached"
            
        # Exit if majority want to leave (rounds 4-7)
        if self.can_exit_conversation():
            exit_count = sum(self.state.exit_requests.values())
            majority = len(self.characters) // 2 + 1
            if exit_count >= majority:
                return True, "majority_exit_request"
                
        return False, ""
        
    def get_turn_statistics(self) -> Dict:
        """Get statistics about the conversation"""
        stats = {
            "total_turns": len(self.state.turns_taken),
            "turns_by_character": {},
            "rounds_completed": self.state.current_round - 1
        }
        
        for char in self.characters:
            char_turns = [t for t in self.state.turns_taken if t.speaker == char]
            stats["turns_by_character"][char] = len(char_turns)
            
        return stats