#!/usr/bin/env python3
"""
Modular Prompt System - Block-based prompt composition

Builds prompts from modular blocks that can be independently modified and tested.
Each prompt type uses the same 5 core blocks composed differently.
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

class PromptBlock(ABC):
    """Base class for prompt blocks"""
    
    @abstractmethod
    def build(self, context: Dict[str, Any]) -> str:
        """Build the block content from context"""
        pass

class PersonalContextBlock(PromptBlock):
    """Personal context about the NPC's identity and state"""
    
    def build(self, context: Dict[str, Any]) -> str:
        personal = context.get("personal", {})
        nature = personal.get("nature")
        nurture = personal.get("nurture")
        
        if not nature or not nurture:
            return ""
            
        learned_section = ""
        if nurture.learned_behaviors:
            recent_behaviors = nurture.learned_behaviors[-2:]  # Most recent 2
            behaviors_list = "\n".join([f"- {behavior}" for behavior in recent_behaviors])
            learned_section = f"""

What You've Learned:
{behaviors_list}"""

        return f"""=== PERSONAL CONTEXT ===
You are {personal['name']}.

Core Nature (permanent):
- Traits: {', '.join(nature.core_traits)}
- Stress Response: {nature.stress_response}
- Moral Compass: {nature.moral_compass}

Current State (from recent events):
- Emotional State: {nurture.emotional_state}
- Confidence: {nurture.current_confidence}/10
- Social Mask: Trying to appear {nurture.social_mask}
- Recent Treatment: Feeling {nurture.recent_treatment}{learned_section}"""
        
    def build_minimal(self, context: Dict[str, Any]) -> str:
        """Minimal version for compression prompts"""
        personal = context.get("personal", {})
        nature = personal.get("nature")
        
        if not nature:
            return ""
            
        return f"You are {personal['name']} with traits: {', '.join(nature.core_traits)}"

class ScenarioContextBlock(PromptBlock):
    """Context about the current scene and beat"""
    
    def build(self, context: Dict[str, Any]) -> str:
        scene = context.get("scene", {})
        beat = context.get("beat", {})
        scenario = context.get("scenario", {})
        
        scene_section = ""
        if scene:
            scene_section = f"""SCENE: {scene.get('premise', 'Unknown situation')}
Stakes: {scene.get('stakes', 'Unknown consequences')}

"""

        beat_section = ""
        if beat:
            beat_section = f"""BEAT {beat.get('number', '?')}: {beat.get('situation', 'Current situation')}
Location: {beat.get('location', 'Unknown')}
Time: {beat.get('time', 'Unknown')}

"""

        complication_section = ""
        complication = scenario.get("complication")
        if complication:
            complication_section = f"""
{complication} - Others don't know this yet. You may reveal through behavior or words as you see fit.

"""

        characters_section = ""
        present_chars = context.get("present_characters", [])
        if present_chars:
            characters_section = f"Present Characters: {', '.join(present_chars)}"

        return f"""=== SCENARIO CONTEXT ===
{scene_section}{beat_section}{complication_section}{characters_section}"""
        
    def build_beat_summary(self, context: Dict[str, Any]) -> str:
        """Version for beat reflection"""
        beat = context.get("beat", {})
        events = context.get("beat_events", [])
        
        lines = [
            "=== SCENARIO CONTEXT ===",
            f"Beat Summary: {beat.get('situation', 'Unknown situation')}",
            "What Happened:"
        ]
        for event in events:  
            lines.append(f"- {event}")
            
        complication = context.get("scenario", {}).get("complication")
        if complication:
            lines.append(f"\nYour Complication Was: [{complication}]")
            
        return "\n".join(lines)
        
    def build_scene_summary(self, context: Dict[str, Any]) -> str:
        """Version for scene memory compression"""
        scene = context.get("scene", {})
        all_events = context.get("scene_events", [])
        
        lines = [
            "=== SCENARIO CONTEXT ===",
            f"Scene That Just Ended: {scene.get('premise', 'Unknown')}",
            f"Stakes Were: {scene.get('stakes', 'Unknown')}",
            f"Outcome: {scene.get('resolution', 'Unresolved')}",
            "",
            "Complete Event Log:"
        ]
        for event in all_events:
            lines.append(f"- {event}")
            
        return "\n".join(lines)

class RelationshipContextBlock(PromptBlock):
    """Context about relationships with other characters"""
    
    def build(self, context: Dict[str, Any]) -> str:
        relationship = context.get("relationship", {})
        speaking_to = relationship.get("speaking_to")
        rel_context = relationship.get("context", {})
        other_rels = relationship.get("other_relationships", {})
        
        if not speaking_to:
            return ""
            
        lines = ["=== RELATIONSHIP CONTEXT ==="]
        lines.extend([
            f"Speaking To: {speaking_to}",
            ""
        ])
        
        if rel_context.get("status") == "unknown":
            lines.extend([
                f"Your Relationship with {speaking_to}:",
                "- Status: First meeting"
            ])
            gossip = rel_context.get("gossip", [])
            if gossip:
                lines.append("What You've Heard (Gossip):")
                for item in gossip:
                    lines.append(f"- {item}")
        else:
            lines.extend([
                f"Your Relationship with {speaking_to}:",
                f"- Status: {rel_context.get('status', 'known')}",
                f"- Label: {rel_context.get('label', 'acquaintance')}",
                f"- Trust: {rel_context.get('trust', 5)}/10",
                f"- Affection: {rel_context.get('affection', 5)}/10",
                ""
            ])
            
            last_interaction = rel_context.get("last_interaction")
            if last_interaction:
                lines.extend([
                    "Last Direct Interaction:",
                    last_interaction
                ])
            else:
                lines.append("Last Direct Interaction: First meeting")
            lines.append("")
            
            memories = rel_context.get("recent_memories", [])
            if memories:
                lines.append("Historical Context:")
                for memory in memories:
                    lines.append(f"- {memory}")
                lines.append("")
                
            gossip = rel_context.get("gossip", [])
            if gossip:
                lines.append("What You've Heard (Gossip):")
                for item in gossip:
                    lines.append(f"- {item}")
                lines.append("")
        
        if other_rels:
            lines.append("Other Relationships Present:")
            for char, rel in other_rels.items():
                if rel.get("status") != "unknown":
                    lines.append(f"- {char}: {rel.get('label', 'acquaintance')} (Trust:{rel.get('trust', 5)}/10)")
                    
        return "\n".join(lines)
        
    def build_participants(self, context: Dict[str, Any]) -> str:
        """Version for beat reflection"""
        participants = context.get("beat_participants", [])
        full_relationships = context.get("full_relationship_context", {})
        
        lines = ["=== RELATIONSHIP CONTEXT ==="]
        lines.append(f"Characters Involved This Beat: {', '.join(participants)}")
        
        # Show complete relationship context for each participant
        for char in participants:
            rel_data = full_relationships.get(char, {})
            if rel_data:
                lines.extend([
                    "",
                    f"Your Relationship with {char}:"
                ])
                
                # Current scores
                trust = rel_data.get("trust", 5)
                affection = rel_data.get("affection", 5)
                label = rel_data.get("label", "acquaintance")
                lines.append(f"- Current: {label} (Trust:{trust}/10, Affection:{affection}/10)")
                
                # Last interaction
                last_interaction = rel_data.get("last_interaction")
                if last_interaction:
                    lines.append(f"- Last Interaction: {last_interaction}")
                
                # Historical context
                historical = rel_data.get("historical_events", [])
                if historical:
                    lines.append("- Past Events:")
                    for event in historical[-2:]:  # Most recent 2 events
                        lines.append(f"  • {event}")
                
                # Gossip knowledge
                gossip = rel_data.get("gossip_knowledge", [])
                if gossip:
                    lines.append("- What You've Heard:")
                    for item in gossip[-2:]:  # Most recent 2 gossip items
                        lines.append(f"  • {item}")
                
        return "\n".join(lines)

class ConversationContextBlock(PromptBlock):
    """Context about the current conversation flow"""
    
    def build(self, context: Dict[str, Any]) -> str:
        conversation = context.get("conversation", {})
        
        if not conversation:
            return ""
            
        lines = ["=== CONVERSATION CONTEXT ==="]
        lines.extend([
            f"Current Round: {conversation.get('current_round', 1)}",
            f"Conversation Energy: {conversation.get('energy', 'medium')}",
            ""
        ])
        
        recent_turns = conversation.get("recent_turns", [])
        if recent_turns:
            lines.append("Recent Exchange:")
            for turn in recent_turns:  
                speaker = turn.get("speaker", "Unknown")
                content = turn.get("content", "...")
                tone = turn.get("tone", "neutral")
                action = turn.get("action")
                
                if action:
                    lines.append(f"{speaker} ({tone}): \"{content}\" *{action}*")
                else:
                    lines.append(f"{speaker} ({tone}): \"{content}\"")
            lines.append("")
            
        # Most recent statement
        last_statement = conversation.get("last_statement")
        last_speaker = conversation.get("last_speaker")
        last_tone = conversation.get("last_tone", "neutral")
        last_action = conversation.get("last_action")
        
        if last_statement and last_speaker:
            lines.extend([
                "Most Recent (What you must respond to):",
                f"{last_speaker} said: \"{last_statement}\"",
                f"Their tone: {last_tone}"
            ])
            if last_action:
                lines.append(f"Their action: {last_action}")
            
        return "\n".join(lines)

class PromptInstructionBlock(PromptBlock):
    """Instructions for how the NPC should respond"""
    
    def build_turn_instruction(self, context: Dict[str, Any]) -> str:
        """Standard speaking turn instruction (like mafia.py)"""
        personal = context.get("personal", {})
        scenario = context.get("scenario", {})
        current_round = context.get("conversation", {}).get("current_round", 1)
        
        name = personal.get("name", "Character")
        
        round_guidance = ""
        if current_round >= 6:
            round_guidance = "- You may want to exit this conversation if it feels resolved"

        if current_round >= 4:
            round_guidance = "- This conversation may end soon - ensure you resolve it"

        elif current_round >= 8:
            round_guidance = "- This conversation should wrap up soon"

        exit_field = ""
        if current_round >= 4:
            exit_field = '  ,"wants_to_exit": false  // true if you want to end conversation'

        return f"""

IMPORTANT:
- You are {name}. Stay in character based on your personality
- Be natural and conversational, build an ENGAGING story. 
- Ensure what you say progresses the story forward. 
- You can target someone specific to speak next by mentioning them
{round_guidance}

Respond with ONLY a JSON object in this format:
{{
  "speaks": "what you want to say (1 sentence max)",
  "does": "physical action (optional)",
  "tone": "your emotional tone",
  "conversation_target": "if targeting someone to respond, state their name, else null",
  "emotional_state": "one word describing your current emotion",
  "reasoning": "brief internal reasoning for this response"{exit_field}
}}

Be strategic and stay true to your character."""
        
    def build_interjection_instruction(self, context: Dict[str, Any]) -> str:
        """Interjection opportunity instruction"""
        current_speaker = context.get("current_speaker", "someone")
        their_target = context.get("their_target", "someone")
        statement = context.get("statement", "...")
        already_interjected = context.get("already_interjected", False)
        
        lines = ["=== PROMPT ==="]
        lines.extend([
            f"You are observing {current_speaker} speaking to {their_target}.",
            f"They just said: \"{statement}\"",
            ""
        ])
        
        if already_interjected:
            lines.append("You have already interjected this round.")
        else:
            lines.append("You may INTERJECT if you feel strongly (only ONCE per round).")
            
        lines.extend([
            "",
            "Consider interjecting if:",
            "- Someone is lying about facts you know",
            "- Someone you trust (7+) is being unfairly attacked",
            "- Critical information needs immediate correction",
            "- Your emotional state is heightened (8+) by what was said",
            "",
            "Required Response Format:",
            "{",
            '  "observation": "internal thought about what you heard",',
            '  "wants_to_interject": boolean,',
            '  "interjection": {',
            '    "speaks": "what you\'d say if interjecting",',
            '    "tone": "your interjection tone",',
            '    "reason": "why this deserves your one interjection"',
            '  } // only if wants_to_interject is true',
            '}'
        ])
        
        return "\n".join(lines)
        
    def build_reflection_instruction(self, context: Dict[str, Any]) -> str:
        """Beat reflection instruction"""
        participants = context.get("beat_participants", [])
        
        return f"""=== PROMPT ===
Reflect on how this beat affected your relationships.

For each OTHER character you interacted with ({', '.join(participants)}):
- How did your trust in them change? (-3 to +3)  
- How did your affection for them change? (-3 to +3)
- Two-word relationship label?
- What's important to remember about them from this scene?

Required Response Format:
{{
  "relationships": {{
    "CharacterName": {{
      "label": "two words",
      "trust_delta": number,
      "affection_delta": number,
      "memory": "one sentence to describe what is important to remember about this scene for CharacterName"
    }}
  }},
  "knowledge_gained": {{
    "gossip_worthy": ["array of gossip"]
  }}
}}"""
        
    def build_compression_instruction(self, context: Dict[str, Any]) -> str:
        """Scene memory compression instruction"""
        lines = ["=== PROMPT ==="]
        lines.extend([
            "Compress your memories from this scene. You can only keep:",
            "- 3 specific moments (one sentence each)",
            "- 2 general impressions about people",
            "- 1 lesson learned",
            "",
            "Everything else becomes fuzzy or forgotten.",
            "",
            "Required Response Format:",
            "{",
            '  "specific_memories": [',
            '    "moment 1",',
            '    "moment 2",',
            '    "moment 3"',
            '  ],',
            '  "general_impressions": [',
            '    "feeling about person 1",',
            '    "feeling about person 2"',
            '  ],',
            '  "lesson": "what you learned"',
            '}'
        ])
        
        return "\n".join(lines)
    
    def build(self, context: Dict[str, Any]) -> str:
        """Default build method - should use specific methods above"""
        return self.build_turn_instruction(context)

class PromptBuilder:
    """Main prompt builder that composes blocks"""
    
    def __init__(self):
        self.blocks = {
            'personal': PersonalContextBlock(),
            'scenario': ScenarioContextBlock(), 
            'relationship': RelationshipContextBlock(),
            'conversation': ConversationContextBlock(),
            'prompt': PromptInstructionBlock()
        }
        
    def build_turn_prompt(self, context: Dict[str, Any]) -> str:
        """Standard NPC turn during conversation"""
        sections = [
            self.blocks['personal'].build(context),
            self.blocks['scenario'].build(context),
            self.blocks['relationship'].build(context),
            self.blocks['conversation'].build(context),
            self.blocks['prompt'].build_turn_instruction(context)
        ]
        
        return self._compose(sections)
        
    def build_interjection_prompt(self, context: Dict[str, Any]) -> str:
        """NPC observing and potentially interjecting"""
        sections = [
            self.blocks['personal'].build(context),
            self.blocks['scenario'].build(context),
            self.blocks['relationship'].build(context),
            self.blocks['conversation'].build(context),
            self.blocks['prompt'].build_interjection_instruction(context)
        ]
        
        return self._compose(sections)
        
    def build_reflection_prompt(self, context: Dict[str, Any]) -> str:
        """Beat completion reflection"""
        sections = [
            self.blocks['personal'].build(context),
            self.blocks['scenario'].build_beat_summary(context),
            self.blocks['relationship'].build_participants(context),
            # Skip conversation context for reflection
            self.blocks['prompt'].build_reflection_instruction(context)
        ]
        
        return self._compose(sections)
        
    def build_compression_prompt(self, context: Dict[str, Any]) -> str:
        """Scene memory compression"""
        sections = [
            self.blocks['personal'].build_minimal(context),
            self.blocks['scenario'].build_scene_summary(context),
            self.blocks['relationship'].build_participants(context),
            # Minimal conversation stats
            self.blocks['prompt'].build_compression_instruction(context)
        ]
        
        return self._compose(sections)
        
    def _compose(self, sections: List[str]) -> str:
        """Compose sections with clear separation"""
        valid_sections = [s for s in sections if s and s.strip()]
        return "\n\n".join(valid_sections)
        
    def estimate_tokens(self, prompt: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token)"""
        return len(prompt) // 4