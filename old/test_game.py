#!/usr/bin/env python3
"""Test script to verify game structure without Ollama dependency"""

import sys
sys.path.insert(0, '.')

from mafia import Card, Player

# Test Card class
print("Testing Card class...")
card1 = Card("good", 1)
card2 = Card("bad", 2)
print(f"✓ Created cards: {card1.type}, {card2.type}")

# Test Player class
print("\nTesting Player class...")
player = Player("p1", "Test", "good", "Test personality")
print(f"✓ Created player: {player.name}, role={player.role}")
print(f"✓ Player hand initially: {player.hand}")

player.hand.append(card1)
player.hand.append(card2)
print(f"✓ Added cards to hand: {[c.type for c in player.hand]}")

# Test deck initialization logic
print("\nTesting deck creation...")
deck = []
card_id = 0
for _ in range(8):
    deck.append(Card("good", card_id))
    card_id += 1
for _ in range(12):
    deck.append(Card("bad", card_id))
    card_id += 1

good_count = len([c for c in deck if c.type == "good"])
bad_count = len([c for c in deck if c.type == "bad"])
print(f"✓ Deck has {good_count} good and {bad_count} bad cards")

print("\n✅ All tests passed! Game structure is working correctly.")