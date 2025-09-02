#!/usr/bin/env python3
"""
Scene Director - Interface for managing scenes and beats

Provides the main interface for directors to set up scenes, define beats,
and manage the narrative flow of the village simulator.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import logging
import asyncio
import os

from ..core.game_state import GameState, Scene, Beat
from ..core.conversation_manager import ConversationManager
from ..npc.npc_manager import NPCManager
from ..prompts.llm_interface import LLMInterface

@dataclass
class BeatSetup:
    """Configuration for a beat"""
    situation: str
    location: str
    time: str
    characters: List[str]
    complications: Dict[str, str]  # character -> secret complication
    witnesses: List[str] = field(default_factory=list)

class SceneDirector:
    """Main interface for directing scenes and managing NPCs"""
    
    def __init__(self, characters: List[str] = None):
        if characters is None:
            characters = ["Alice", "Bob", "Charlie"]
            
        self.characters = characters
        self.game_state = GameState()
        self.llm_interface = LLMInterface()
        self.logger = logging.getLogger(__name__)
        
        # Current scene/beat management
        self.current_conversation: Optional[ConversationManager] = None
        self.beat_events: List[str] = []
        
        # Auto-load/save NPC data (including relationships)
        self.npc_data_file = "saves/npc_data.json"
        self.npc_manager = NPCManager.load_from_file(self.npc_data_file, characters)
        
        # Establish first meetings if this is a fresh start
        if not os.path.exists(self.npc_data_file):
            self.npc_manager.establish_first_meetings()
            
        # Always save after initialization to ensure file exists
        self.npc_manager.save_to_file(self.npc_data_file)
        
        self.logger.info(f"SceneDirector initialized with {len(characters)} characters")
        self.logger.info(f"NPC data auto-saved to: {self.npc_data_file}")
        
    def _clear_session_logs(self):
        """Clear session logs for a fresh start"""
        import os
        log_file = "logs/session.log"
        try:
            if os.path.exists(log_file):
                # Clear the log file by truncating it
                with open(log_file, 'w') as f:
                    f.truncate(0)
                # Log the clearing action (this will be the first entry)
                self.logger.info("🧹 Session logs cleared for new scene")
            else:
                # Ensure logs directory exists
                os.makedirs("logs", exist_ok=True)
                self.logger.info("🧹 Created logs directory and session log file")
        except Exception as e:
            self.logger.warning(f"Failed to clear session logs: {e}")
        
    def create_scene(self, title: str, premise: str, stakes: str) -> Scene:
        """Create a new scene"""
        # Clear session logs for new scene
        self._clear_session_logs()
        
        scene = self.game_state.create_scene(title, premise, stakes)
        self.logger.info(f"Created scene {scene.number}: {title}")
        return scene
        
    def setup_beat(self, beat_setup: BeatSetup) -> Beat:
        """Set up a new beat within the current scene"""
        beat = self.game_state.create_beat(
            situation=beat_setup.situation,
            location=beat_setup.location, 
            time=beat_setup.time,
            characters=beat_setup.characters,
            complications=beat_setup.complications
        )
        
        # Set complications in NPC manager
        self.npc_manager.set_beat_complications(beat_setup.complications)
        
        # Reset beat events tracking
        self.beat_events = []
        
        self.logger.info(f"Set up beat {beat.number}: {beat_setup.situation}")
        return beat
        
    async def run_beat_conversation(self, max_rounds: int = 8) -> Dict[str, Any]:
        """Run the conversation for the current beat"""
        current_beat = self.game_state.get_current_beat()
        if not current_beat:
            raise ValueError("No beat is currently active")
            
        # Initialize conversation manager
        self.current_conversation = ConversationManager(current_beat.characters)
        
        conversation_log = []
        round_count = 0
        last_round = 0  # Track rounds to print when they change
        
        self.logger.info(f"Starting beat conversation with {len(current_beat.characters)} characters")
        
        try:
            # Run conversation turns (like mafia.py)
            for turn_num in range(max_rounds * len(current_beat.characters)):
                # Check if conversation should end
                should_end, reason = self.current_conversation.should_end_conversation()
                if should_end:
                    self.logger.info(f"Conversation ended: {reason}")
                    break
                    
                print(f"\n--- Turn {turn_num + 1} ---")
                
                # Print round number when it changes
                current_round = self.current_conversation.state.current_round
                if current_round > last_round:
                    print(f"\n=== Round {current_round} ===")
                    last_round = current_round
                
                # Get current speaker (like mafia.py)
                speaker = self.current_conversation.get_next_speaker()
                
                # Generate turn context
                turn_context = await self._build_turn_context(speaker, current_beat)
                
                # Generate NPC response
                turn_result = await self.llm_interface.generate_npc_turn(turn_context)
                
                if turn_result and turn_result["action"]["speaks"]:
                    speaks = turn_result["action"]["speaks"]
                    tone = turn_result["action"]["tone"]
                    action = turn_result["action"].get("does")
                    target = turn_result.get("conversation_target")
                    
                    print(f"\n{speaker}: {speaks}")
                    if action:
                        print(f"  ({action})")
                    
                    # Add turn to conversation manager
                    turn = self.current_conversation.add_turn(
                        speaker=speaker,
                        content=speaks,
                        action=action,
                        tone=tone,
                        target=target
                    )
                    
                    # Update NPC state
                    self.npc_manager.process_turn_result(speaker, turn_result)
                    
                    # Add to conversation log and beat events  
                    log_entry = {
                        "turn": turn_num + 1,
                        "round": self.current_conversation.state.current_round,
                        "speaker": speaker,
                        "content": speaks,
                        "tone": tone,
                        "action": action,
                        "target": target,
                        "emotional_state": turn_result["internal"]["emotional_state"],
                        "wants_to_exit": turn_result["internal"].get("wants_to_exit", False)
                    }
                    conversation_log.append(log_entry)
                    
                    event_desc = f"{speaker}: \"{speaks}\""
                    if action:
                        event_desc += f" ({action})"
                    self.beat_events.append(event_desc)
                    
                else:
                    self.logger.info(f"⏭️  {speaker} skipped turn - null message")
                    
                await asyncio.sleep(0.5)  # Brief pause between turns
                    
        except Exception as e:
            self.logger.error(f"Error during beat conversation: {e}")
            raise
            
        # End beat and process reflections
        await self._complete_beat(conversation_log)
        
        return {
            "total_rounds": self.current_conversation.state.current_round,
            "total_turns": len(conversation_log),
            "conversation_log": conversation_log,
            "end_reason": reason if 'reason' in locals() else "max_turns_reached",
            "beat_events": self.beat_events
        }
        
    async def _build_turn_context(self, speaker: str, beat: Beat) -> Dict[str, Any]:
        """Build context for NPC turn generation"""
        # Get NPC context
        npc_context = self.npc_manager.get_npc_context(
            character=speaker,
            speaking_to=self._determine_speaking_target(speaker, beat.characters),
            conversation_context={
                "present_characters": beat.characters,
                "current_round": self.current_conversation.state.current_round
            }
        )
        
        # Get current scene and beat
        current_scene = self.game_state.get_current_scene()
        
        # Build conversation context
        recent_turns = self.current_conversation.get_recent_turns(3)
        last_turn = recent_turns[-1] if recent_turns else None
        
        conversation_context = {
            "current_round": self.current_conversation.state.current_round,
            "energy": self.current_conversation.state.conversation_energy,
            "recent_turns": [
                {
                    "speaker": t.speaker,
                    "content": t.content,
                    "tone": t.tone,
                    "action": t.action
                } for t in recent_turns
            ]
        }
        
        if last_turn and last_turn.speaker != speaker:
            conversation_context.update({
                "last_statement": last_turn.content,
                "last_speaker": last_turn.speaker,
                "last_tone": last_turn.tone,
                "last_action": last_turn.action
            })
            
        return {
            "personal": npc_context["personal"],
            "scenario": npc_context["scenario"],
            "relationship": npc_context["relationship"],
            "conversation": conversation_context,
            "scene": {
                "premise": current_scene.premise if current_scene else "Unknown situation",
                "stakes": current_scene.stakes if current_scene else "Unknown consequences"
            },
            "beat": {
                "number": beat.number,
                "situation": beat.situation,
                "location": beat.location,
                "time": beat.time
            },
            "present_characters": beat.characters
        }
        
    def _determine_speaking_target(self, speaker: str, characters: List[str]) -> str:
        """Determine who the speaker is primarily addressing"""
        # For now, simple logic - address the group or first other character
        others = [c for c in characters if c != speaker]
        return others[0] if others else speaker
        
    async def _complete_beat(self, conversation_log: List[Dict[str, Any]]):
        """Complete the beat and process reflections"""
        current_beat = self.game_state.get_current_beat()
        
        # Generate reflections for each character
        for character in current_beat.characters:
            reflection_context = await self._build_reflection_context(character, conversation_log)
            reflection = await self.llm_interface.generate_beat_reflection(reflection_context)
            
            # Process the reflection to update relationships and knowledge
            self.npc_manager.process_beat_reflection(character, reflection)
            
        # Mark beat as completed
        outcome = f"Conversation completed after {len(conversation_log)} turns"
        self.game_state.complete_beat(outcome)
        
        # Auto-save NPC data after beat completion (relationships updated)
        self.npc_manager.save_to_file(self.npc_data_file)
        self.logger.info(f"Beat {current_beat.number} completed with {len(conversation_log)} total turns")
        self.logger.info(f"NPC relationships auto-saved to: {self.npc_data_file}")
        
    async def _build_reflection_context(self, character: str, conversation_log: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build context for beat reflection"""
        current_beat = self.game_state.get_current_beat()
        
        # Get character's personal context
        npc_context = self.npc_manager.get_npc_context(
            character=character,
            speaking_to="",  # Not needed for reflection
            conversation_context={"present_characters": current_beat.characters}
        )
        
        # Extract key exchanges involving this character
        key_exchanges = []
        for entry in conversation_log:
            if entry["speaker"] == character or character.lower() in entry["content"].lower():
                summary = f"{entry['speaker']}: \"{entry['content'][:50]}...\""
                key_exchanges.append(summary)
                
        # Get other characters (exclude self from reflection)
        other_characters = [c for c in current_beat.characters if c != character]
        
        return {
            "personal": npc_context["personal"],
            "beat": {
                "number": current_beat.number,
                "situation": current_beat.situation
            },
            "beat_participants": other_characters,  # Only OTHER characters
            "beat_events": self.beat_events[-10:],  # Recent events
            "key_exchanges": key_exchanges[-5:]  # Most relevant exchanges
        }
        
    def get_scene_summary(self) -> Dict[str, Any]:
        """Get summary of current scene progress"""
        scene = self.game_state.get_current_scene()
        beat = self.game_state.get_current_beat()
        
        summary = {
            "scene": {
                "number": scene.number if scene else 0,
                "title": scene.title if scene else "No scene",
                "premise": scene.premise if scene else "",
                "stakes": scene.stakes if scene else ""
            },
            "beat": {
                "number": beat.number if beat else 0,
                "situation": beat.situation if beat else "",
                "location": beat.location if beat else "",
                "time": beat.time if beat else ""
            },
            "characters": self.characters,
            "npc_status": self.npc_manager.get_npc_status_summary(),
            "relationships": self.npc_manager.get_relationship_summary(),
            "story_progress": self.game_state.get_story_summary()
        }
        
        return summary
        
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "llm_stats": self.llm_interface.get_performance_stats(),
            "conversation_stats": self.current_conversation.get_turn_statistics() if self.current_conversation else {},
            "relationship_asymmetries": self.npc_manager.get_relationship_asymmetries()
        }