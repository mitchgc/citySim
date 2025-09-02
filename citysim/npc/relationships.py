#!/usr/bin/env python3
"""
Relationship System - Bidirectional trust/affection matrices

Manages complex relationship dynamics where A's feelings toward B
may be completely different from B's feelings toward A.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
import json
from enum import Enum

class RelationshipStatus(Enum):
    UNKNOWN = "unknown"      # Never met
    KNOWN = "known"          # Have interacted
    FORGOTTEN = "forgotten"  # Time has passed, memories faded

@dataclass
class Relationship:
    """A one-directional relationship (A -> B)"""
    from_char: str
    to_char: str
    status: RelationshipStatus = RelationshipStatus.UNKNOWN
    trust: Optional[int] = None        # 0-10: Will they do what they say?
    affection: Optional[int] = None    # 0-10: Do I enjoy their company?
    label: Optional[str] = None        # 2-word summary: "cautious ally"
    last_interaction: Optional[str] = None
    historical_events: List[str] = field(default_factory=list)
    gossip_knowledge: List[str] = field(default_factory=list)
    
    def derive_label(self) -> str:
        """Derive 2-word relationship label from trust/affection"""
        if self.trust is None or self.affection is None:
            return "unknown person"
            
        if self.trust >= 8 and self.affection >= 8:
            return "beloved friend"
        elif self.trust >= 7 and self.affection >= 7:
            return "trusted ally"
        elif self.trust >= 7 and self.affection <= 3:
            return "reliable stranger"
        elif self.trust <= 3 and self.affection >= 7:
            return "charming liar"
        elif self.trust <= 3 and self.affection <= 3:
            return "dangerous enemy"
        elif self.trust >= 6 and 4 <= self.affection <= 6:
            return "cautious ally"
        elif 4 <= self.trust <= 6 and self.affection >= 7:
            return "likeable acquaintance"
        else:
            return "complicated person"
    
    def update_scores(self, trust_delta: int = 0, affection_delta: int = 0):
        """Update relationship scores within bounds"""
        if self.trust is not None:
            self.trust = max(0, min(10, self.trust + trust_delta))
        if self.affection is not None:
            self.affection = max(0, min(10, self.affection + affection_delta))
        self.label = self.derive_label()
        
    def add_memory(self, memory: str):
        """Add a memory of interaction"""
        self.historical_events.append(memory)
        # Keep only recent 5 memories
        if len(self.historical_events) > 5:
            self.historical_events.pop(0)
            
    def add_gossip(self, gossip: str):
        """Add gossip knowledge about this person"""
        if gossip not in self.gossip_knowledge:
            self.gossip_knowledge.append(gossip)
        # Keep only recent 3 gossip items
        if len(self.gossip_knowledge) > 3:
            self.gossip_knowledge.pop(0)
            
    def establish_first_meeting(self, initial_trust: int = 5, initial_affection: int = 5):
        """Establish relationship on first meeting"""
        self.status = RelationshipStatus.KNOWN
        self.trust = initial_trust
        self.affection = initial_affection
        self.label = self.derive_label()

class RelationshipMatrix:
    """Manages bidirectional relationships between all characters"""
    
    def __init__(self, characters: List[str]):
        self.characters = characters
        self.relationships: Dict[str, Relationship] = {}
        self._initialize_relationships()
        
    def _get_key(self, from_char: str, to_char: str) -> str:
        """Get relationship key"""
        return f"{from_char}->{to_char}"
        
    def _initialize_relationships(self):
        """Initialize all possible relationships"""
        for from_char in self.characters:
            for to_char in self.characters:
                if from_char != to_char:
                    key = self._get_key(from_char, to_char)
                    self.relationships[key] = Relationship(from_char, to_char)
                    
    def get_relationship(self, from_char: str, to_char: str) -> Optional[Relationship]:
        """Get relationship from A to B"""
        key = self._get_key(from_char, to_char)
        return self.relationships.get(key)
        
    def establish_first_meeting(self, char1: str, char2: str, 
                              char1_to_char2_trust: int = 5, char1_to_char2_affection: int = 5,
                              char2_to_char1_trust: int = 5, char2_to_char1_affection: int = 5):
        """Establish mutual first meeting with potentially different feelings"""
        rel1 = self.get_relationship(char1, char2)
        rel2 = self.get_relationship(char2, char1)
        
        if rel1:
            rel1.establish_first_meeting(char1_to_char2_trust, char1_to_char2_affection)
        if rel2:
            rel2.establish_first_meeting(char2_to_char1_trust, char2_to_char1_affection)
            
    def update_relationship(self, from_char: str, to_char: str, 
                          trust_delta: int = 0, affection_delta: int = 0,
                          memory: Optional[str] = None):
        """Update a relationship and add memory"""
        rel = self.get_relationship(from_char, to_char)
        if rel and rel.status == RelationshipStatus.KNOWN:
            rel.update_scores(trust_delta, affection_delta)
            if memory:
                rel.add_memory(memory)
                rel.last_interaction = memory
                
    def add_gossip(self, listener: str, about: str, gossip: str):
        """Add gossip knowledge"""
        rel = self.get_relationship(listener, about)
        if rel:
            rel.add_gossip(gossip)
            
    def get_relationship_context(self, from_char: str, to_char: str) -> Dict[str, Any]:
        """Get relationship context for prompts"""
        rel = self.get_relationship(from_char, to_char)
        if not rel:
            return {"status": "error", "message": "relationship not found"}
            
        if rel.status == RelationshipStatus.UNKNOWN:
            return {
                "status": "unknown",
                "label": "stranger",
                "gossip": rel.gossip_knowledge[-2:] if rel.gossip_knowledge else []
            }
            
        return {
            "status": rel.status.value,
            "trust": rel.trust,
            "affection": rel.affection,
            "label": rel.label,
            "last_interaction": rel.last_interaction,
            "recent_memories": rel.historical_events[-3:],
            "gossip": rel.gossip_knowledge[-2:]
        }
        
    def get_all_relationships_for(self, character: str) -> Dict[str, Dict[str, Any]]:
        """Get all relationships for a character"""
        relationships = {}
        for other_char in self.characters:
            if other_char != character:
                relationships[other_char] = self.get_relationship_context(character, other_char)
        return relationships
        
    def decay_relationships(self, days_passed: int = 1):
        """Decay relationships toward neutral over time"""
        decay_rate = 0.1 * days_passed  # Small decay per day
        
        for rel in self.relationships.values():
            if rel.status == RelationshipStatus.KNOWN:
                # Decay toward neutral (5)
                if rel.trust is not None:
                    if rel.trust > 5:
                        rel.trust = max(5, rel.trust - decay_rate)
                    elif rel.trust < 5:
                        rel.trust = min(5, rel.trust + decay_rate)
                        
                if rel.affection is not None:
                    if rel.affection > 5:
                        rel.affection = max(5, rel.affection - decay_rate)
                    elif rel.affection < 5:
                        rel.affection = min(5, rel.affection + decay_rate)
                        
                rel.label = rel.derive_label()
                
                # After many days without interaction, relationships can fade
                if days_passed >= 10 and not rel.historical_events:
                    rel.status = RelationshipStatus.FORGOTTEN
                    
    def get_relationship_summary(self) -> Dict[str, Any]:
        """Get summary of all relationships"""
        summary = {}
        for from_char in self.characters:
            summary[from_char] = {}
            for to_char in self.characters:
                if from_char != to_char:
                    rel = self.get_relationship(from_char, to_char)
                    if rel and rel.status == RelationshipStatus.KNOWN:
                        summary[from_char][to_char] = {
                            "trust": rel.trust,
                            "affection": rel.affection,
                            "label": rel.label
                        }
        return summary
        
    def detect_asymmetries(self) -> List[Dict[str, Any]]:
        """Find interesting relationship asymmetries"""
        asymmetries = []
        
        for char1 in self.characters:
            for char2 in self.characters:
                if char1 < char2:  # Check each pair only once
                    rel1 = self.get_relationship(char1, char2)
                    rel2 = self.get_relationship(char2, char1)
                    
                    if (rel1 and rel2 and 
                        rel1.status == RelationshipStatus.KNOWN and
                        rel2.status == RelationshipStatus.KNOWN):
                        
                        trust_diff = abs(rel1.trust - rel2.trust)
                        affection_diff = abs(rel1.affection - rel2.affection)
                        
                        if trust_diff >= 3 or affection_diff >= 3:
                            asymmetries.append({
                                "char1": char1,
                                "char2": char2,
                                "char1_to_char2": {"trust": rel1.trust, "affection": rel1.affection, "label": rel1.label},
                                "char2_to_char1": {"trust": rel2.trust, "affection": rel2.affection, "label": rel2.label},
                                "trust_gap": trust_diff,
                                "affection_gap": affection_diff
                            })
                            
        return asymmetries
        
    def to_dict(self) -> Dict[str, Any]:
        """Export relationships to dictionary"""
        relationships_dict = {}
        for key, rel in self.relationships.items():
            rel_dict = asdict(rel)
            # Convert enum to string for JSON serialization
            rel_dict["status"] = rel.status.value
            relationships_dict[key] = rel_dict
            
        return {
            "characters": self.characters,
            "relationships": relationships_dict
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RelationshipMatrix":
        """Import relationships from dictionary"""
        matrix = cls(data["characters"])
        for key, rel_data in data["relationships"].items():
            # Convert status string back to enum
            rel_data["status"] = RelationshipStatus(rel_data["status"])
            matrix.relationships[key] = Relationship(**rel_data)
        return matrix