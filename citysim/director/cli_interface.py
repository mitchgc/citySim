#!/usr/bin/env python3
"""
Command Line Interface - Terminal interface for directing scenes

Provides a simple command-line interface for directors to create scenes,
set up beats, and manage the village simulator.
"""

import asyncio
import sys
import logging

from .scene_director import SceneDirector, BeatSetup

class CLIInterface:
    """Command-line interface for the village simulator"""
    
    def __init__(self):
        self.director = SceneDirector()
        self.logger = logging.getLogger(__name__)
        
        # Setup logging for CLI
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)-7s | %(message)s',
            handlers=[
                logging.FileHandler('logs/session.log'),
            ]
        )
        
    def print_header(self):
        """Print the application header"""
        print("=" * 60)
        print("🏘️  VILLAGE SIMULATOR - LLM-Powered Conversational NPCs")
        print("=" * 60)
        print()
        
    def print_menu(self):
        """Print the main menu options"""
        print("📋 DIRECTOR COMMANDS:")
        print("1. Create Scene")
        print("2. Set Up Beat") 
        print("3. Run Beat Conversation")
        print("4. View Scene Summary")
        print("5. View NPC Status")
        print("6. View Relationships") 
        print("7. View Relationship File")
        print("8. Performance Stats")
        print("9. Export Story")
        print("10. Quick Test Scene")
        print("0. Exit")
        print()
        
    async def run(self):
        """Main CLI loop"""
        self.print_header()
        
        while True:
            self.print_menu()
            choice = input("Enter choice (0-10): ").strip()
            
            if choice == "0":
                print("👋 Goodbye!")
                break
            elif choice == "1":
                await self.create_scene()
            elif choice == "2":
                await self.setup_beat()
            elif choice == "3":
                await self.run_beat_conversation()
            elif choice == "4":
                self.view_scene_summary()
            elif choice == "5":
                self.view_npc_status()
            elif choice == "6":
                self.view_relationships()
            elif choice == "7":
                self.view_relationship_file()
            elif choice == "8":
                self.view_performance_stats()
            elif choice == "9":
                self.export_story()
            elif choice == "10":
                await self.run_quick_test()
            else:
                print("❌ Invalid choice. Please try again.")
                
            input("\nPress Enter to continue...")
            print("\n" + "=" * 60 + "\n")
            
    async def create_scene(self):
        """Interactive scene creation"""
        print("🎬 CREATE NEW SCENE")
        print("-" * 30)
        
        title = input("Scene title: ").strip()
        if not title:
            print("❌ Title is required")
            return
            
        print("\nDescribe what's happening and why:")
        premise = input("Premise: ").strip()
        if not premise:
            print("❌ Premise is required")
            return
            
        print("\nWhat could go wrong?")
        stakes = input("Stakes: ").strip()
        if not stakes:
            print("❌ Stakes are required")
            return
            
        scene = self.director.create_scene(title, premise, stakes)
        
        print(f"\n✅ Created Scene {scene.number}: {title}")
        print(f"   Premise: {premise}")
        print(f"   Stakes: {stakes}")
        
    async def setup_beat(self):
        """Interactive beat setup"""
        print("🎭 SET UP BEAT")
        print("-" * 30)
        
        current_scene = self.director.game_state.get_current_scene()
        if not current_scene:
            print("❌ No scene is currently active. Create a scene first.")
            return
            
        print(f"Setting up beat for Scene {current_scene.number}: {current_scene.title}")
        print()
        
        situation = input("Beat situation (immediate challenge): ").strip()
        if not situation:
            print("❌ Situation is required")
            return
            
        location = input("Location: ").strip() or "Village center"
        time = input("Time: ").strip() or "Morning"
        
        # Character selection
        print(f"\nAvailable characters: {', '.join(self.director.characters)}")
        char_input = input("Characters in this beat (comma-separated, or 'all'): ").strip()
        
        if char_input.lower() == "all":
            characters = self.director.characters.copy()
        else:
            characters = [c.strip() for c in char_input.split(",") if c.strip() in self.director.characters]
            
        if not characters:
            print("❌ At least one valid character is required")
            return
            
        # Complications
        complications = {}
        print(f"\n🤫 SET SECRET COMPLICATIONS")
        print("Each character can have a secret that influences their behavior.")
        
        for char in characters:
            comp = input(f"{char}'s secret complication (optional): ").strip()
            if comp:
                complications[char] = comp
                
        beat_setup = BeatSetup(
            situation=situation,
            location=location,
            time=time,
            characters=characters,
            complications=complications
        )
        
        beat = self.director.setup_beat(beat_setup)
        
        print(f"\n✅ Set up Beat {beat.number}")
        print(f"   Situation: {situation}")
        print(f"   Location: {location}, Time: {time}")
        print(f"   Characters: {', '.join(characters)}")
        print(f"   Complications: {len(complications)} secrets set")
        
    async def run_beat_conversation(self):
        """Run the conversation for current beat"""
        current_beat = self.director.game_state.get_current_beat()
        if not current_beat:
            print("❌ No beat is currently active. Set up a beat first.")
            return
            
        print("🗣️  RUNNING BEAT CONVERSATION")
        print("-" * 30)
        print(f"Beat {current_beat.number}: {current_beat.situation}")
        print(f"Characters: {', '.join(current_beat.characters)}")
        print()
        
        max_rounds = int(input("Maximum rounds (default 8): ") or "8")
        
        print(f"\n🎬 Starting conversation... (max {max_rounds} rounds)")
        print("=" * 40)
        
        try:
            result = await self.director.run_beat_conversation(max_rounds)
            
            print(f"\n✅ Beat conversation completed!")
            print(f"   Total rounds: {result['total_rounds']}")
            print(f"   Total turns: {result['total_turns']}")
            print(f"   End reason: {result['end_reason']}")
            
            # Show conversation highlights
            print(f"\n📜 CONVERSATION HIGHLIGHTS:")
            for i, entry in enumerate(result['conversation_log'][-5:], 1):  # Last 5 turns
                prefix = "🗯️ " if entry.get("turn_type") == "interjection" else ""
                print(f"{i}. {prefix}{entry['speaker']}: \"{entry['content']}\" ({entry['tone']})")
                
        except Exception as e:
            print(f"❌ Error running conversation: {e}")
            self.logger.error(f"Conversation error: {e}")
            
    def view_scene_summary(self):
        """Display current scene summary"""
        print("📋 SCENE SUMMARY")
        print("-" * 30)
        
        summary = self.director.get_scene_summary()
        
        scene = summary["scene"]
        beat = summary["beat"]
        
        if scene["number"] == 0:
            print("❌ No scene is currently active.")
            return
            
        print(f"Scene {scene['number']}: {scene['title']}")
        print(f"Premise: {scene['premise']}")
        print(f"Stakes: {scene['stakes']}")
        print()
        
        if beat["number"] > 0:
            print(f"Beat {beat['number']}: {beat['situation']}")
            print(f"Location: {beat['location']}, Time: {beat['time']}")
            print()
            
        print(f"Characters: {', '.join(summary['characters'])}")
        
        story_progress = summary["story_progress"]
        print(f"\nStory Progress:")
        print(f"  Total days: {story_progress['total_days']}")
        print(f"  Scenes completed: {story_progress['scenes_completed']}/{story_progress['total_scenes']}")
        print(f"  Total beats: {story_progress['total_beats']}")
        
    def view_npc_status(self):
        """Display NPC status summary"""
        print("👥 NPC STATUS")
        print("-" * 30)
        
        summary = self.director.get_scene_summary()
        npc_status = summary["npc_status"]
        
        for char, status in npc_status.items():
            print(f"{char}:")
            print(f"  Primary trait: {status['primary_trait']}")
            print(f"  Confidence: {status['confidence']}/10")
            print(f"  Emotional state: {status['emotional_state']}")
            print(f"  Emotional intensity: {status['emotional_intensity']}/10")
            print(f"  Wants to exit: {status['wants_to_exit']}")
            print(f"  Has complication: {status['current_complication']}")
            print()
            
    def view_relationships(self):
        """Display relationship matrix"""
        print("💝 RELATIONSHIPS")
        print("-" * 30)
        
        summary = self.director.get_scene_summary()
        relationships = summary["relationships"]
        
        if not relationships:
            print("No established relationships yet.")
            return
            
        for from_char, relations in relationships.items():
            print(f"{from_char} feels about others:")
            for to_char, rel in relations.items():
                trust = rel.get("trust", "?")
                affection = rel.get("affection", "?")
                label = rel.get("label", "unknown")
                print(f"  {to_char}: {label} (Trust:{trust}/10, Affection:{affection}/10)")
            print()
            
        # Show asymmetries
        asymmetries = self.director.npc_manager.get_relationship_asymmetries()
        if asymmetries:
            print("🔀 RELATIONSHIP ASYMMETRIES:")
            for asym in asymmetries[:3]:  # Top 3
                c1, c2 = asym["char1"], asym["char2"]
                gap = max(asym["trust_gap"], asym["affection_gap"])
                print(f"  {c1} ↔ {c2}: {gap} point difference in feelings")
                
    def view_relationship_file(self):
        """Display the location and contents of the relationship file"""
        print("📁 RELATIONSHIP FILE")
        print("-" * 30)
        
        relationship_file = self.director.npc_data_file
        print(f"File location: {relationship_file}")
        
        try:
            import json
            import os
            
            if os.path.exists(relationship_file):
                print(f"File size: {os.path.getsize(relationship_file)} bytes")
                print(f"Last modified: {os.path.getmtime(relationship_file)}")
                print()
                
                with open(relationship_file, 'r') as f:
                    data = json.load(f)
                    
                # Show relationship summary from file
                relationships = data.get("relationships", {}).get("relationships", {})
                print("CURRENT RELATIONSHIPS IN FILE:")
                print("-" * 40)
                
                # Group by character
                char_relationships = {}
                for key, rel_data in relationships.items():
                    from_char = rel_data["from_char"]
                    to_char = rel_data["to_char"]
                    
                    if from_char not in char_relationships:
                        char_relationships[from_char] = {}
                    char_relationships[from_char][to_char] = rel_data
                    
                for from_char, rels in char_relationships.items():
                    print(f"\n{from_char} feels about:")
                    for to_char, rel in rels.items():
                        status = rel.get("status", "unknown")
                        if status == "known":
                            trust = rel.get("trust", "?")
                            affection = rel.get("affection", "?")
                            label = rel.get("label", "unknown")
                            print(f"  {to_char}: {label} (T:{trust}/10, A:{affection}/10)")
                        else:
                            print(f"  {to_char}: {status}")
                            
            else:
                print("❌ Relationship file not found!")
                print("Run a conversation first to generate the file.")
                
        except Exception as e:
            print(f"❌ Error reading relationship file: {e}")
                
    def view_performance_stats(self):
        """Display performance statistics"""
        print("📊 PERFORMANCE STATS")
        print("-" * 30)
        
        stats = self.director.get_performance_stats()
        
        llm_stats = stats["llm_stats"]
        print("LLM Performance:")
        print(f"  Total calls: {llm_stats['total_calls']}")
        print(f"  Estimated tokens: {llm_stats['total_tokens_estimate']:,}")
        print(f"  Avg response time: {llm_stats['average_response_time']:.2f}s")
        print(f"  Model: {llm_stats['model']}")
        print()
        
        conv_stats = stats.get("conversation_stats", {})
        if conv_stats:
            print("Conversation Stats:")
            print(f"  Total turns: {conv_stats['total_turns']}")
            print(f"  Rounds completed: {conv_stats['rounds_completed']}")
            
            turns_by_char = conv_stats.get("turns_by_character", {})
            interjections_by_char = conv_stats.get("interjections_by_character", {})
            
            for char in self.director.characters:
                turns = turns_by_char.get(char, 0)
                interjections = interjections_by_char.get(char, 0)
                print(f"  {char}: {turns} turns, {interjections} interjections")
                
    def export_story(self):
        """Export the story to a text file"""
        print("📤 EXPORT STORY")
        print("-" * 30)
        
        try:
            filename = self.director.game_state.export_story_log()
            print(f"✅ Story exported to: {filename}")
        except Exception as e:
            print(f"❌ Error exporting story: {e}")
            
    async def run_quick_test(self):
        """Run a quick test scenario"""
        print("🚀 QUICK TEST SCENARIO")
        print("-" * 30)
        
        # Create test scene
        scene = self.director.create_scene(
            "The Missing Food",
            "The food storage was raided overnight",
            "Find the thief or the group falls apart from suspicion"
        )
        print(f"✅ Created test scene: {scene.title}")
        
        # Setup test beat
        beat_setup = BeatSetup(
            situation="Discovering the empty storage at dawn",
            location="Food storage area",
            time="Dawn",
            characters=["Alice", "Bob", "Charlie"],
            complications={
                "Alice": "You saw someone near storage but couldn't tell who",
                "Bob": "You sleep-walked last night and don't remember",
                "Charlie": "You took the food but regret it immediately"
            }
        )
        
        beat = self.director.setup_beat(beat_setup)
        print(f"✅ Set up test beat: {beat.situation}")
        
        # Run conversation
        print("\n🗣️  Running test conversation...")
        try:
            result = await self.director.run_beat_conversation(6)  # Shorter for testing
            
            print(f"\n✅ Test completed!")
            print(f"   Rounds: {result['total_rounds']}, Turns: {result['total_turns']}")
            
            # Show key moments
            print(f"\n🎭 KEY MOMENTS:")
            interjections = [entry for entry in result['conversation_log'] 
                           if entry.get("turn_type") == "interjection"]
            
            if interjections:
                for intr in interjections:
                    print(f"🗯️ {intr['speaker']} interjected: \"{intr['content']}\"")
            else:
                print("No interjections occurred")
                
            print(f"\n📊 Final emotional states:")
            for entry in result['conversation_log'][-3:]:  # Last few turns
                print(f"  {entry['speaker']}: {entry.get('emotional_state', 'neutral')}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")

def main():
    """Main entry point"""
    cli = CLIInterface()
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()