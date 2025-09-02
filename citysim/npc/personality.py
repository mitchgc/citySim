#!/usr/bin/env python3
"""
NPC Personality System - Nature vs Nurture personality architecture

Nature: Permanent core traits that define the character
Nurture: Scene-influenced behaviors and learned patterns
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
import json
import random

@dataclass
class Nature:
    """Permanent personality core - never changes"""
    core_traits: List[str]  # ["generous", "anxious", "hardworking"]
    cognitive_style: str    # "overthinking", "impulsive", "analytical"
    stress_response: str    # "people-pleasing", "aggressive", "withdrawal"
    moral_compass: str      # "fairness-first", "loyalty-first", "pragmatic"
    
@dataclass 
class Nurture:
    """Evolving personality influenced by recent events"""
    recent_treatment: str = "neutral"     # "appreciated", "dismissed", "trusted"
    current_confidence: int = 5           # 0-10 scale
    learned_behaviors: List[str] = field(default_factory=list)  # ["Bob responds to guilt"]
    temporary_beliefs: List[str] = field(default_factory=list)  # ["We might survive"]
    social_mask: str = "authentic"        # "competent leader", "helpful friend"
    emotional_state: str = "neutral"      # Current emotional state
    
    def update_confidence(self, change: int):
        """Update confidence within bounds"""
        self.current_confidence = max(0, min(10, self.current_confidence + change))
        
    def learn_behavior(self, behavior: str):
        """Learn a new behavior pattern"""
        if behavior not in self.learned_behaviors:
            self.learned_behaviors.append(behavior)
            # Keep only recent 5 behaviors
            if len(self.learned_behaviors) > 5:
                self.learned_behaviors.pop(0)
                
    def adopt_belief(self, belief: str):
        """Adopt a temporary belief"""
        if belief not in self.temporary_beliefs:
            self.temporary_beliefs.append(belief)
            # Keep only recent 3 beliefs
            if len(self.temporary_beliefs) > 3:
                self.temporary_beliefs.pop(0)

class PersonalityGenerator:
    """Generate personalities for NPCs"""
    
    TRAIT_POOLS = {
        "positive": ["generous", "brave", "hardworking", "optimistic", "loyal", "honest", "patient"],
        "negative": ["selfish", "cowardly", "lazy", "pessimistic", "disloyal", "deceptive", "impatient"],
        "neutral": ["analytical", "quiet", "talkative", "curious", "cautious", "practical", "creative"]
    }
    
    COGNITIVE_STYLES = ["overthinking", "impulsive", "analytical", "intuitive", "methodical"]
    STRESS_RESPONSES = ["people-pleasing", "aggressive", "withdrawal", "denial", "hypervigilance"]
    MORAL_COMPASSES = ["fairness-first", "loyalty-first", "pragmatic", "rule-following", "compassionate"]
    
    @classmethod
    def generate_nature(cls, archetype: str = "balanced") -> Nature:
        """Generate a Nature based on archetype"""
        
        if archetype == "generous_anxious":
            return Nature(
                core_traits=["generous", "anxious", "hardworking"],
                cognitive_style="overthinking",
                stress_response="people-pleasing", 
                moral_compass="fairness-first"
            )
        elif archetype == "selfish_cunning":
            return Nature(
                core_traits=["selfish", "cunning", "charismatic"],
                cognitive_style="analytical",
                stress_response="aggressive",
                moral_compass="pragmatic"
            )
        elif archetype == "loyal_quiet":
            return Nature(
                core_traits=["loyal", "quiet", "observant"],
                cognitive_style="intuitive",
                stress_response="withdrawal",
                moral_compass="loyalty-first"
            )
        else:  # balanced random
            traits = []
            traits.append(random.choice(cls.TRAIT_POOLS["positive"]))
            traits.append(random.choice(cls.TRAIT_POOLS["negative"]))
            traits.append(random.choice(cls.TRAIT_POOLS["neutral"]))
            
            return Nature(
                core_traits=traits,
                cognitive_style=random.choice(cls.COGNITIVE_STYLES),
                stress_response=random.choice(cls.STRESS_RESPONSES),
                moral_compass=random.choice(cls.MORAL_COMPASSES)
            )
    
    @classmethod
    def create_default_npcs(cls) -> Dict[str, Nature]:
        """Create the default 3 NPCs for testing"""
        return {
            "Alice": cls.generate_nature("generous_anxious"),
            "Bob": cls.generate_nature("selfish_cunning"), 
            "Charlie": cls.generate_nature("loyal_quiet")
        }

class PersonalityManager:
    """Manages personality state for an NPC"""
    
    def __init__(self, name: str, nature: Nature):
        self.name = name
        self.nature = nature
        self.nurture = Nurture()
        
    def get_unified_personality_context(self) -> str:
        """Generate unified personality context for prompts"""
        context_parts = []
        
        # Core nature
        context_parts.append(f"Core traits: {', '.join(self.nature.core_traits)}")
        context_parts.append(f"Stress response: {self.nature.stress_response}")
        context_parts.append(f"Moral compass: {self.nature.moral_compass}")
        
        # Current state
        context_parts.append(f"Confidence: {self.nurture.current_confidence}/10")
        context_parts.append(f"Emotional state: {self.nurture.emotional_state}")
        
        if self.nurture.learned_behaviors:
            behaviors = self.nurture.learned_behaviors[-2:]  # Most recent 2
            context_parts.append(f"Learned: {', '.join(behaviors)}")
            
        return " | ".join(context_parts)
        
    def update_from_experience(self, experience_type: str, details: Dict[str, Any]):
        """Update nurture based on experience"""
        
        if experience_type == "positive_interaction":
            self.nurture.update_confidence(1)
            self.nurture.recent_treatment = "appreciated"
            
        elif experience_type == "negative_interaction":
            self.nurture.update_confidence(-1)
            self.nurture.recent_treatment = "dismissed"
            
        elif experience_type == "betrayal":
            self.nurture.update_confidence(-2)
            self.nurture.recent_treatment = "betrayed"
            if "betrayer" in details:
                self.nurture.learn_behavior(f"{details['betrayer']} is untrustworthy")
                
        elif experience_type == "success":
            self.nurture.update_confidence(2)
            self.nurture.recent_treatment = "successful"
            
        elif experience_type == "failure":
            self.nurture.update_confidence(-1)
            self.nurture.emotional_state = "disappointed"
            
    def set_emotional_state(self, emotion: str):
        """Set current emotional state"""
        self.nurture.emotional_state = emotion
        
    def set_social_mask(self, mask: str):
        """Set the social mask they're trying to project"""
        self.nurture.social_mask = mask
        
    def get_primary_trait(self) -> str:
        """Get the most prominent trait for prompt contexts"""
        return self.nature.core_traits[0] if self.nature.core_traits else "neutral"
        
    def should_stress_response_trigger(self, stress_level: int) -> bool:
        """Check if stress response should be triggered (8+ stress)"""
        return stress_level >= 8
        
    def to_dict(self) -> Dict[str, Any]:
        """Export personality to dictionary"""
        return {
            "name": self.name,
            "nature": asdict(self.nature),
            "nurture": asdict(self.nurture)
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersonalityManager":
        """Import personality from dictionary"""
        nature = Nature(**data["nature"])
        manager = cls(data["name"], nature)
        manager.nurture = Nurture(**data["nurture"])
        return manager
        
    def save_to_file(self, filepath: str):
        """Save personality to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
            
    @classmethod
    def load_from_file(cls, filepath: str) -> "PersonalityManager":
        """Load personality from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)