#!/usr/bin/env python3
"""
Game State Management - Central state for the village simulator

Manages the overall game state including story progression,
scene/beat structure, and persistence.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os

@dataclass
class Scene:
    """A major story segment with premise and stakes"""
    number: int
    title: str
    premise: str  # What's happening and why
    stakes: str   # What could go wrong
    resolution: Optional[str] = None  # How it ended
    start_time: Optional[str] = None
    end_time: Optional[str] = None

@dataclass 
class Beat:
    """A subsection of a scene with situation and complications"""
    number: int
    scene_number: int
    situation: str  # Immediate challenge
    location: str
    time: str
    characters: List[str]
    witnesses: List[str] = field(default_factory=list)
    complications: Dict[str, str] = field(default_factory=dict)  # char -> secret complication
    outcome: Optional[str] = None

@dataclass
class Story:
    """The complete narrative structure"""
    title: str
    current_scene: int = 1
    current_beat: int = 1
    total_days: int = 0
    scenes: List[Scene] = field(default_factory=list)
    beats: List[Beat] = field(default_factory=list)

@dataclass
class Resources:
    """Village resources that affect survival"""
    food: int = 10
    wood: int = 10
    medicine: int = 5
    morale: int = 50
    
    def update(self, **changes):
        """Update resources with changes"""
        for resource, change in changes.items():
            if hasattr(self, resource):
                current = getattr(self, resource)
                setattr(self, resource, max(0, current + change))

class GameState:
    """Central game state manager"""
    
    def __init__(self, save_file: str = "saves/game_state.json"):
        self.save_file = save_file
        self.story = Story(title="Untitled Story")
        self.resources = Resources()
        self.metadata = {
            "created": datetime.now().isoformat(),
            "last_saved": None,
            "version": "0.1.0"
        }
        
        # Ensure save directory exists
        os.makedirs(os.path.dirname(save_file), exist_ok=True)
        
    def create_scene(self, title: str, premise: str, stakes: str) -> Scene:
        """Create a new scene"""
        scene = Scene(
            number=len(self.story.scenes) + 1,
            title=title,
            premise=premise,
            stakes=stakes,
            start_time=datetime.now().isoformat()
        )
        self.story.scenes.append(scene)
        self.story.current_scene = scene.number
        return scene
        
    def create_beat(self, situation: str, location: str, time: str, 
                   characters: List[str], complications: Dict[str, str]) -> Beat:
        """Create a new beat within current scene"""
        beat = Beat(
            number=len(self.story.beats) + 1,
            scene_number=self.story.current_scene,
            situation=situation,
            location=location,
            time=time,
            characters=characters,
            complications=complications
        )
        self.story.beats.append(beat)
        self.story.current_beat = beat.number
        return beat
        
    def complete_scene(self, resolution: str):
        """Mark current scene as completed"""
        if self.story.scenes:
            current_scene = self.story.scenes[-1]
            current_scene.resolution = resolution
            current_scene.end_time = datetime.now().isoformat()
            
    def complete_beat(self, outcome: str):
        """Mark current beat as completed"""
        if self.story.beats:
            current_beat = self.story.beats[-1]
            current_beat.outcome = outcome
            
    def get_current_scene(self) -> Optional[Scene]:
        """Get the current active scene"""
        if self.story.scenes:
            return self.story.scenes[-1]
        return None
        
    def get_current_beat(self) -> Optional[Beat]:
        """Get the current active beat"""
        if self.story.beats:
            return self.story.beats[-1]
        return None
        
    def advance_time(self, days: int = 1):
        """Advance the story timeline"""
        self.story.total_days += days
        
    def save_state(self):
        """Save current state to disk"""
        self.metadata["last_saved"] = datetime.now().isoformat()
        
        state_dict = {
            "story": asdict(self.story),
            "resources": asdict(self.resources),
            "metadata": self.metadata
        }
        
        with open(self.save_file, 'w') as f:
            json.dump(state_dict, f, indent=2)
            
    def load_state(self) -> bool:
        """Load state from disk. Returns True if successful."""
        if not os.path.exists(self.save_file):
            return False
            
        try:
            with open(self.save_file, 'r') as f:
                state_dict = json.load(f)
                
            # Reconstruct story
            story_data = state_dict["story"]
            self.story = Story(
                title=story_data["title"],
                current_scene=story_data["current_scene"],
                current_beat=story_data["current_beat"],
                total_days=story_data["total_days"],
                scenes=[Scene(**scene) for scene in story_data["scenes"]],
                beats=[Beat(**beat) for beat in story_data["beats"]]
            )
            
            # Reconstruct resources
            self.resources = Resources(**state_dict["resources"])
            
            # Restore metadata
            self.metadata = state_dict["metadata"]
            
            return True
            
        except Exception as e:
            print(f"Error loading game state: {e}")
            return False
            
    def get_story_summary(self) -> Dict[str, Any]:
        """Get a summary of the story so far"""
        return {
            "title": self.story.title,
            "current_scene": self.story.current_scene,
            "current_beat": self.story.current_beat,
            "total_days": self.story.total_days,
            "scenes_completed": len([s for s in self.story.scenes if s.resolution]),
            "total_scenes": len(self.story.scenes),
            "total_beats": len(self.story.beats),
            "resources": asdict(self.resources)
        }
        
    def export_story_log(self, filename: Optional[str] = None) -> str:
        """Export complete story as readable text"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"exports/story_{timestamp}.txt"
            
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        lines = []
        lines.append(f"# {self.story.title}")
        lines.append(f"Duration: {self.story.total_days} days")
        lines.append("")
        
        for scene in self.story.scenes:
            lines.append(f"## Scene {scene.number}: {scene.title}")
            lines.append(f"Premise: {scene.premise}")
            lines.append(f"Stakes: {scene.stakes}")
            if scene.resolution:
                lines.append(f"Resolution: {scene.resolution}")
            lines.append("")
            
            # Add beats for this scene
            scene_beats = [b for b in self.story.beats if b.scene_number == scene.number]
            for beat in scene_beats:
                lines.append(f"### Beat {beat.number}: {beat.situation}")
                lines.append(f"Location: {beat.location}, Time: {beat.time}")
                lines.append(f"Characters: {', '.join(beat.characters)}")
                if beat.outcome:
                    lines.append(f"Outcome: {beat.outcome}")
                lines.append("")
                
        content = "\n".join(lines)
        
        with open(filename, 'w') as f:
            f.write(content)
            
        return filename