#!/usr/bin/env python3
"""
NPC Manager - Combines personality and relationship management

Central manager for NPC state including personality, relationships,
memory, and interaction with the conversation system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import logging

from .personality import PersonalityManager, PersonalityGenerator
from .relationships import RelationshipMatrix

@dataclass
class NPCState:
    """Current state of an NPC"""
    name: str
    current_complication: Optional[str] = None  # Secret for current beat
    emotional_intensity: int = 5  # 0-10 scale for interjection triggers
    wants_to_exit: bool = False
    last_action: Optional[str] = None
    last_tone: Optional[str] = None

class NPCManager:
    """Manages all NPCs and their interactions"""
    
    def __init__(self, characters: List[str] = None):
        if characters is None:
            characters = ["Alice", "Bob", "Charlie"]
            
        self.characters = characters
        self.personalities: Dict[str, PersonalityManager] = {}
        self.relationships = RelationshipMatrix(characters)
        self.states: Dict[str, NPCState] = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize NPCs
        self._initialize_npcs()
        
    def _initialize_npcs(self):
        """Initialize all NPCs with default personalities"""
        default_natures = PersonalityGenerator.create_default_npcs()
        
        for char in self.characters:
            # Create personality manager
            nature = default_natures.get(char, PersonalityGenerator.generate_nature("balanced"))
            self.personalities[char] = PersonalityManager(char, nature)
            
            # Create state
            self.states[char] = NPCState(char)
            
        self.logger.info(f"Initialized {len(self.characters)} NPCs: {', '.join(self.characters)}")
        
    def establish_first_meetings(self):
        """Establish initial relationships between all characters"""
        for i, char1 in enumerate(self.characters):
            for char2 in self.characters[i+1:]:
                # Establish mutual first meeting with neutral scores
                self.relationships.establish_first_meeting(char1, char2, 5, 5, 5, 5)
                
        self.logger.info("Established first meetings between all characters")
        
    def set_beat_complications(self, complications: Dict[str, str]):
        """Set secret complications for current beat"""
        for char, complication in complications.items():
            if char in self.states:
                self.states[char].current_complication = complication
                self.logger.debug(f"Set complication for {char}: {complication}")
                
    def get_npc_context(self, character: str, speaking_to: str, 
                       conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get complete context for NPC prompt generation"""
        
        if character not in self.personalities:
            raise ValueError(f"Unknown character: {character}")
            
        personality = self.personalities[character]
        state = self.states[character]
        
        # Get relationship context
        relationship_context = self.relationships.get_relationship_context(character, speaking_to)
        
        # Get other present relationships for context
        other_relationships = {}
        present_chars = conversation_context.get("present_characters", [])
        for other_char in present_chars:
            if other_char not in [character, speaking_to]:
                other_relationships[other_char] = self.relationships.get_relationship_context(character, other_char)
                
        return {
            "personal": {
                "name": character,
                "nature": personality.nature,
                "nurture": personality.nurture,
                "primary_trait": personality.get_primary_trait(),
                "unified_personality": personality.get_unified_personality_context()
            },
            "scenario": {
                "complication": state.current_complication,
                "emotional_intensity": state.emotional_intensity
            },
            "relationship": {
                "speaking_to": speaking_to,
                "context": relationship_context,
                "other_relationships": other_relationships
            },
            "state": {
                "wants_to_exit": state.wants_to_exit,
                "last_action": state.last_action,
                "last_tone": state.last_tone
            }
        }
        
    def process_turn_result(self, character: str, turn_result: Dict[str, Any]):
        """Process the result of an NPC's turn"""
        state = self.states[character]
        
        # Update NPC state from turn result
        if "action" in turn_result:
            action = turn_result["action"]
            state.last_action = action.get("does")
            state.last_tone = action.get("tone")
            
        if "internal" in turn_result:
            internal = turn_result["internal"]
            emotional_state = internal.get("emotional_state", "neutral")
            self.personalities[character].set_emotional_state(emotional_state)
            
            state.wants_to_exit = internal.get("wants_to_exit", False)
            
        self.logger.debug(f"Processed turn result for {character}: {emotional_state}")
        
    def process_beat_reflection(self, character: str, reflection: Dict[str, Any]):
        """Process relationship changes from beat reflection"""
        
        if "relationships" in reflection:
            for other_char, changes in reflection["relationships"].items():
                if other_char in self.characters:
                    # Establish first meeting if relationship is still unknown
                    rel = self.relationships.get_relationship(character, other_char)
                    if rel and rel.status.value == "unknown":
                        rel.establish_first_meeting(5, 5)  # Default neutral meeting
                        self.logger.info(f"🤝 Established first meeting: {character} -> {other_char}")
                    
                    trust_delta = changes.get("trust_delta", 0)
                    affection_delta = changes.get("affection_delta", 0)
                    memory = changes.get("memory")
                    
                    self.relationships.update_relationship(
                        character, other_char, trust_delta, affection_delta, memory
                    )
                    
        if "knowledge_gained" in reflection:
            knowledge = reflection["knowledge_gained"]
            
            # Add gossip to relationships
            for gossip in knowledge.get("gossip_worthy", []):
                # Parse gossip to find who it's about
                for other_char in self.characters:
                    if other_char != character and other_char.lower() in gossip.lower():
                        self.relationships.add_gossip(character, other_char, gossip)
                        break
                        
        self.logger.info(f"Processed beat reflection for {character}")
        
    def check_interjection_triggers(self, observer: str, speaker: str, 
                                  statement: str, tone: str) -> Dict[str, Any]:
        """Check if observer should interject based on statement"""
        
        observer_state = self.states[observer]
        observer_personality = self.personalities[observer]
        
        # Get relationship with speaker
        speaker_relationship = self.relationships.get_relationship_context(observer, speaker)
        
        triggers = []
        
        # High emotional intensity trigger
        if observer_state.emotional_intensity >= 8:
            triggers.append("emotional_trigger")
            
        # Defend high-trust allies  
        if speaker_relationship.get("trust", 0) >= 7 and tone in ["accusatory", "hostile"]:
            triggers.append("relationship_defense")
            
        # Stress response trigger
        stress_keywords = ["liar", "thief", "betrayer", observer.lower()]
        if any(word in statement.lower() for word in stress_keywords):
            if observer_personality.should_stress_response_trigger(observer_state.emotional_intensity):
                triggers.append("stress_response")
                
        # Information correction (if they know the truth)
        if observer_state.current_complication:
            # Simple check for contradictions
            if "never" in statement.lower() or "didn't" in statement.lower():
                triggers.append("information_correction")
                
        should_interject = len(triggers) > 0
        primary_reason = triggers[0] if triggers else None
        
        return {
            "should_interject": should_interject,
            "triggers": triggers,
            "primary_reason": primary_reason,
            "emotional_intensity": observer_state.emotional_intensity
        }
        
    def update_emotional_intensity(self, character: str, change: int):
        """Update emotional intensity for interjection triggers"""
        state = self.states[character]
        state.emotional_intensity = max(0, min(10, state.emotional_intensity + change))
        
    def advance_time(self, days: int = 1):
        """Advance time and decay relationships"""
        self.relationships.decay_relationships(days)
        
        # Reset some temporary states
        for state in self.states.values():
            state.emotional_intensity = max(1, state.emotional_intensity - 1)  # Emotions cool down
            
    def get_relationship_summary(self) -> Dict[str, Any]:
        """Get summary of all relationships"""
        return self.relationships.get_relationship_summary()
        
    def get_relationship_asymmetries(self) -> List[Dict[str, Any]]:
        """Get interesting relationship asymmetries"""
        return self.relationships.detect_asymmetries()
        
    def get_npc_status_summary(self) -> Dict[str, Any]:
        """Get summary of all NPC states"""
        summary = {}
        for char in self.characters:
            personality = self.personalities[char]
            state = self.states[char]
            
            summary[char] = {
                "primary_trait": personality.get_primary_trait(),
                "confidence": personality.nurture.current_confidence,
                "emotional_state": personality.nurture.emotional_state,
                "emotional_intensity": state.emotional_intensity,
                "wants_to_exit": state.wants_to_exit,
                "current_complication": bool(state.current_complication)  # Don't reveal the secret
            }
            
        return summary
        
    def to_dict(self) -> Dict[str, Any]:
        """Export all NPC data to dictionary"""
        return {
            "characters": self.characters,
            "personalities": {char: p.to_dict() for char, p in self.personalities.items()},
            "relationships": self.relationships.to_dict(),
            "states": {char: {
                "name": s.name,
                "current_complication": s.current_complication,
                "emotional_intensity": s.emotional_intensity,
                "wants_to_exit": s.wants_to_exit,
                "last_action": s.last_action,
                "last_tone": s.last_tone
            } for char, s in self.states.items()}
        }
        
    def save_to_file(self, filepath: str):
        """Save all NPC data to file"""
        import json
        import os
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
            
    @classmethod
    def load_from_file(cls, filepath: str, characters: List[str]) -> "NPCManager":
        """Load NPC data from file, or create new if file doesn't exist"""
        import json
        import os
        
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    
                # Create new NPCManager with loaded data
                manager = cls.__new__(cls)
                manager.characters = data["characters"]
                manager.logger = logging.getLogger(__name__)
                
                # Reconstruct personalities
                manager.personalities = {}
                for char, personality_data in data["personalities"].items():
                    manager.personalities[char] = PersonalityManager.from_dict(personality_data)
                    
                # Reconstruct relationships
                manager.relationships = RelationshipMatrix.from_dict(data["relationships"])
                
                # Reconstruct states
                manager.states = {}
                for char, state_data in data["states"].items():
                    manager.states[char] = NPCState(
                        name=state_data["name"],
                        current_complication=state_data.get("current_complication"),
                        emotional_intensity=state_data.get("emotional_intensity", 5),
                        wants_to_exit=state_data.get("wants_to_exit", False),
                        last_action=state_data.get("last_action"),
                        last_tone=state_data.get("last_tone")
                    )
                    
                logging.getLogger(__name__).info(f"Loaded NPC data from {filepath}")
                return manager
                
            except Exception as e:
                logging.getLogger(__name__).warning(f"Failed to load NPC data from {filepath}: {e}")
                logging.getLogger(__name__).info("Creating new NPC data instead")
                
        # Create new NPCManager if file doesn't exist or loading failed
        return cls(characters)