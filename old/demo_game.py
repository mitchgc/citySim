#!/usr/bin/env python3
"""Demo version of the card game without Ollama dependency"""

import random
from dataclasses import dataclass, field

@dataclass
class Card:
    type: str  # "good" or "bad"
    id: int

@dataclass
class Player:
    name: str
    role: str  # "good" or "bad"
    hand: list = field(default_factory=list)
    excluded: bool = False
    bad_votes: int = 0  # Track how many times they've voted "bad"

def simulate_game(bad_players=1, good_players=3, bad_cards=24, good_cards=16, verbose=False):
    if verbose:
        print("=== CARD CONSPIRACY SIMULATION ===")
        print(f"Config: {bad_players} bad, {good_players} good players | {bad_cards} bad, {good_cards} good cards\n")
    
    # Create deck with configurable card counts
    deck = []
    for i in range(good_cards):
        deck.append(Card("good", i))
    for i in range(bad_cards):
        deck.append(Card("bad", i + good_cards))
    random.shuffle(deck)
    
    # Create players with configurable counts
    player_names = ["Alex", "Blake", "Casey", "Drew", "Emma", "Frank", "Grace", "Henry"]
    players = []
    
    # Add bad players
    for i in range(bad_players):
        players.append(Player(player_names[i], "bad"))
    
    # Add good players  
    for i in range(good_players):
        players.append(Player(player_names[bad_players + i], "good"))
    
    random.shuffle(players)
    
    if verbose:
        print("RULES:")
        print(f"- {good_cards + bad_cards} cards: {good_cards} good, {bad_cards} bad")
        print("- Each player gets 2 cards")
        print("- Vote to exclude 1 player's cards")
        print("- Everyone plays 1 card")
        print("- First team to 10 points wins!")
        print("- If tied, continue until tie is broken\n")
    
    good_score = 0
    bad_score = 0
    round_num = 1
    bad_voters_history = []  # Track all players who voted "bad" across rounds
    exclusion_history = []  # Track who was excluded each round
    max_rounds = 10  # Safety limit
    
    while round_num <= max_rounds:
        if verbose:
            print(f"\n{'='*30}")
            print(f"ROUND {round_num}")
            print(f"Score: Good {good_score}/10 | Bad {bad_score}/10")
            print(f"{'='*30}")
        
        # Deal cards
        if verbose:
            print("\nDealing cards...")
        for player in players:
            if len(deck) >= 2:
                player.hand = [deck.pop(), deck.pop()]
                if verbose:
                    print(f"{player.name} cards: {player.hand[0].type}, {player.hand[1].type}")
        
        # Enhanced voting system with strategic considerations
        if verbose:
            print("\n[Discussion phase]")
        
        # Track votes for each player (who gets voted for exclusion)
        exclusion_votes = {player.name: 0 for player in players}
        round_bad_voters = []
        
        for voter in players:
            voter_bad_cards = len([c for c in voter.hand if c.type == "bad"])
            
            if voter.role == "good":
                # Good players vote strategically
                for target in players:
                    if target.name == voter.name:
                        continue
                    
                    target_bad_cards = len([c for c in target.hand if c.type == "bad"])
                    
                    # Higher probability to vote for good players with 2 bad cards
                    if target.role == "good" and target_bad_cards == 2:
                        # 90% chance to vote for exclusion
                        if random.random() < 0.9:
                            exclusion_votes[target.name] += 1
                            if verbose:
                                print(f"  {voter.name} (good) votes to exclude {target.name} (good with 2 bad cards)")
                            break
                    # Also consider players who have voted bad frequently in the past
                    elif target.bad_votes > 2:
                        if random.random() < 0.4:
                            exclusion_votes[target.name] += 1
                            if verbose:
                                print(f"  {voter.name} (good) votes to exclude {target.name} (frequent bad voter)")
                            break
                
                # Track if this good player votes "bad" (for old system compatibility)
                if voter_bad_cards > 0:
                    round_bad_voters.append(voter.name)
                    voter.bad_votes += 1
                    if verbose and voter.name not in [name for name, votes in exclusion_votes.items() if votes > 0]:
                        print(f"  {voter.name} votes 'bad' (has {voter_bad_cards} bad card(s))")
            
            else:  # Bad player
                # Bad players try to exclude good players to prevent good cards being played
                good_targets = [p for p in players if p.role == "good" and p.name != voter.name]
                if good_targets:
                    # Prioritize good players with good cards, avoid those with 2 bad cards
                    target_weights = []
                    for target in good_targets:
                        target_good_cards = len([c for c in target.hand if c.type == "good"])
                        target_bad_cards = len([c for c in target.hand if c.type == "bad"])
                        
                        # Avoid good players with 2 bad cards (they can't play good cards)
                        if target_bad_cards == 2:
                            weight = 0.1  # Very low weight, almost never target them
                        else:
                            # Higher weight for good players with good cards
                            weight = 1 + target_good_cards * 2
                            # Lower weight if they've voted bad frequently (appear suspicious)
                            if target.bad_votes > 1:
                                weight = max(1, weight - target.bad_votes)
                        target_weights.append(weight)
                    
                    # Choose target based on weights
                    total_weight = sum(target_weights)
                    if total_weight > 0:
                        rand_val = random.random() * total_weight
                        cumulative = 0
                        for i, (target, weight) in enumerate(zip(good_targets, target_weights)):
                            cumulative += weight
                            if rand_val <= cumulative:
                                exclusion_votes[target.name] += 1
                                if verbose:
                                    target_good_cards = len([c for c in target.hand if c.type == "good"])
                                    print(f"  {voter.name} (bad) votes to exclude {target.name} (good with {target_good_cards} good cards)")
                                break
                
                # Bad players also vote "bad" if they have bad cards
                if voter_bad_cards > 0:
                    round_bad_voters.append(voter.name)
                    voter.bad_votes += 1
        
        # Update history
        bad_voters_history.extend(round_bad_voters)
        if verbose:
            print(f"Bad voters this round: {round_bad_voters}")
            exclusion_vote_summary = {name: votes for name, votes in exclusion_votes.items() if votes > 0}
            if exclusion_vote_summary:
                print(f"Exclusion votes: {exclusion_vote_summary}")
        
        # Determine who gets excluded based on votes
        max_votes = max(exclusion_votes.values()) if exclusion_votes.values() else 0
        
        if max_votes > 0:
            # Find all players with the maximum votes
            most_voted = [name for name, votes in exclusion_votes.items() if votes == max_votes]
            excluded_name = random.choice(most_voted)
            excluded = next(p for p in players if p.name == excluded_name)
            excluded.excluded = True
            exclusion_history.append(excluded.name)
            if verbose:
                print(f"\n{excluded.name} is excluded ({max_votes} exclusion vote(s))!")
        elif bad_voters_history:
            # Fallback to old system if no exclusion votes but there are bad voters
            weighted_pool = []
            for player in players:
                if player.bad_votes > 0:
                    weighted_pool.extend([player.name] * player.bad_votes)
            
            if weighted_pool:
                excluded_name = random.choice(weighted_pool)
                excluded = next(p for p in players if p.name == excluded_name)
                excluded.excluded = True
                exclusion_history.append(excluded.name)
                if verbose:
                    print(f"\n{excluded.name} is excluded (bad vote fallback)!")
            else:
                excluded = random.choice(players)
                excluded.excluded = True
                exclusion_history.append(excluded.name)
                if verbose:
                    print(f"\n{excluded.name} is excluded (random fallback)!")
        else:
            # Pure random fallback
            excluded = random.choice(players)
            excluded.excluded = True
            exclusion_history.append(excluded.name)
            if verbose:
                print(f"\n{excluded.name} is excluded (random - no voters yet)!")
        
        # Play cards
        if verbose:
            print("\nPlaying cards:")
        for player in players:
            if player.hand:
                # Simple logic: good players play good if they have it
                if player.role == "good":
                    good_cards = [c for c in player.hand if c.type == "good"]
                    card = good_cards[0] if good_cards else player.hand[0]
                else:
                    bad_cards = [c for c in player.hand if c.type == "bad"]
                    card = bad_cards[0] if bad_cards else player.hand[0]
                
                player.hand.remove(card)
                
                if not player.excluded:
                    if card.type == "good":
                        good_score += 1
                    else:
                        bad_score += 1
                    if verbose:
                        print(f"  {player.name}: {card.type} (counts)")
                else:
                    if verbose:
                        print(f"  {player.name}: {card.type} (excluded)")
        
        # Check for early win condition after each round
        if verbose:
            print(f"\nRound {round_num} complete: Good {good_score} | Bad {bad_score}")
        
        if good_score >= 10:
            if verbose:
                print(f"\n{'='*50}")
                print("🎉 GOOD TEAM WINS! (Reached 10 points)")
                print(f"Final Score: Good {good_score} | Bad {bad_score}")
            winner = "good"
            break
        elif bad_score >= 10:
            if verbose:
                print(f"\n{'='*50}")
                print("😈 BAD TEAM WINS! (Reached 10 points)")
                print(f"Final Score: Good {good_score} | Bad {bad_score}")
            winner = "bad"
            break
        
        # Return cards to deck
        for player in players:
            deck.extend(player.hand)
            player.hand = []
            player.excluded = False
        random.shuffle(deck)
        
        round_num += 1
    else:
        # Only run if no early win occurred (loop completed normally)
        # After 10 rounds, determine winner by highest score
        if verbose:
            print(f"\n{'='*50}")
            print(f"GAME OVER - {max_rounds} ROUNDS COMPLETED")
            print(f"Final Score: Good {good_score} | Bad {bad_score}")
        
        if good_score > bad_score:
            if verbose:
                print("🎉 GOOD TEAM WINS! (Higher score)")
            winner = "good"
        elif bad_score > good_score:
            if verbose:
                print("😈 BAD TEAM WINS! (Higher score)")
            winner = "bad"
        else:
            if verbose:
                print("🤝 TIE GAME! Playing tie-breaker rounds...")
            
            # Tie-breaker rounds
            while good_score == bad_score:
                round_num += 1
                if verbose:
                    print(f"\n{'='*30}")
                    print(f"TIE-BREAKER ROUND {round_num}")
                    print(f"Score: Good {good_score} | Bad {bad_score}")
                    print(f"{'='*30}")
                
                # Deal cards
                if verbose:
                    print("\nDealing cards...")
                for player in players:
                    if len(deck) >= 2:
                        player.hand = [deck.pop(), deck.pop()]
                        if verbose:
                            print(f"{player.name} cards: {player.hand[0].type}, {player.hand[1].type}")
                
                # Enhanced voting system for tie-breaker (same as main game)
                if verbose:
                    print("\n[Discussion phase]")
                
                exclusion_votes = {player.name: 0 for player in players}
                round_bad_voters = []
                
                for voter in players:
                    voter_bad_cards = len([c for c in voter.hand if c.type == "bad"])
                    
                    if voter.role == "good":
                        # Good players vote strategically
                        for target in players:
                            if target.name == voter.name:
                                continue
                            
                            target_bad_cards = len([c for c in target.hand if c.type == "bad"])
                            
                            # Higher probability to vote for good players with 2 bad cards
                            if target.role == "good" and target_bad_cards == 2:
                                if random.random() < 0.9:
                                    exclusion_votes[target.name] += 1
                                    if verbose:
                                        print(f"  {voter.name} (good) votes to exclude {target.name} (good with 2 bad cards)")
                                    break
                            elif target.bad_votes > 2:
                                if random.random() < 0.4:
                                    exclusion_votes[target.name] += 1
                                    if verbose:
                                        print(f"  {voter.name} (good) votes to exclude {target.name} (frequent bad voter)")
                                    break
                        
                        # Track if this good player votes "bad"
                        if voter_bad_cards > 0:
                            round_bad_voters.append(voter.name)
                            voter.bad_votes += 1
                            if verbose and voter.name not in [name for name, votes in exclusion_votes.items() if votes > 0]:
                                print(f"  {voter.name} votes 'bad' (has {voter_bad_cards} bad card(s))")
                    
                    else:  # Bad player
                        # Bad players try to exclude good players
                        good_targets = [p for p in players if p.role == "good" and p.name != voter.name]
                        if good_targets:
                            target_weights = []
                            for target in good_targets:
                                target_good_cards = len([c for c in target.hand if c.type == "good"])
                                target_bad_cards = len([c for c in target.hand if c.type == "bad"])
                                
                                # Avoid good players with 2 bad cards (they can't play good cards)
                                if target_bad_cards == 2:
                                    weight = 0.1  # Very low weight, almost never target them
                                else:
                                    # Higher weight for good players with good cards
                                    weight = 1 + target_good_cards * 2
                                    # Lower weight if they've voted bad frequently (appear suspicious)
                                    if target.bad_votes > 1:
                                        weight = max(1, weight - target.bad_votes)
                                target_weights.append(weight)
                            
                            total_weight = sum(target_weights)
                            if total_weight > 0:
                                rand_val = random.random() * total_weight
                                cumulative = 0
                                for i, (target, weight) in enumerate(zip(good_targets, target_weights)):
                                    cumulative += weight
                                    if rand_val <= cumulative:
                                        exclusion_votes[target.name] += 1
                                        if verbose:
                                            target_good_cards = len([c for c in target.hand if c.type == "good"])
                                            print(f"  {voter.name} (bad) votes to exclude {target.name} (good with {target_good_cards} good cards)")
                                        break
                        
                        if voter_bad_cards > 0:
                            round_bad_voters.append(voter.name)
                            voter.bad_votes += 1
                
                bad_voters_history.extend(round_bad_voters)
                if verbose:
                    exclusion_vote_summary = {name: votes for name, votes in exclusion_votes.items() if votes > 0}
                    if exclusion_vote_summary:
                        print(f"Exclusion votes: {exclusion_vote_summary}")
                
                # Exclude player based on votes
                max_votes = max(exclusion_votes.values()) if exclusion_votes.values() else 0
                
                if max_votes > 0:
                    most_voted = [name for name, votes in exclusion_votes.items() if votes == max_votes]
                    excluded_name = random.choice(most_voted)
                    excluded = next(p for p in players if p.name == excluded_name)
                    excluded.excluded = True
                    exclusion_history.append(excluded.name)
                    if verbose:
                        print(f"\n{excluded.name} is excluded ({max_votes} exclusion vote(s))!")
                elif bad_voters_history:
                    weighted_pool = []
                    for player in players:
                        if player.bad_votes > 0:
                            weighted_pool.extend([player.name] * player.bad_votes)
                    
                    if weighted_pool:
                        excluded_name = random.choice(weighted_pool)
                        excluded = next(p for p in players if p.name == excluded_name)
                        excluded.excluded = True
                        exclusion_history.append(excluded.name)
                        if verbose:
                            print(f"\n{excluded.name} is excluded (bad vote fallback)!")
                    else:
                        excluded = random.choice(players)
                        excluded.excluded = True
                        exclusion_history.append(excluded.name)
                        if verbose:
                            print(f"\n{excluded.name} is excluded (random)!")
                else:
                    excluded = random.choice(players)
                    excluded.excluded = True
                    exclusion_history.append(excluded.name)
                    if verbose:
                        print(f"\n{excluded.name} is excluded (random)!")
                
                # Play cards
                if verbose:
                    print("\nPlaying cards:")
                for player in players:
                    if player.hand:
                        if player.role == "good":
                            good_cards = [c for c in player.hand if c.type == "good"]
                            card = good_cards[0] if good_cards else player.hand[0]
                        else:
                            bad_cards = [c for c in player.hand if c.type == "bad"]
                            card = bad_cards[0] if bad_cards else player.hand[0]
                        
                        player.hand.remove(card)
                        
                        if not player.excluded:
                            if card.type == "good":
                                good_score += 1
                            else:
                                bad_score += 1
                            if verbose:
                                print(f"  {player.name}: {card.type} (counts)")
                        else:
                            if verbose:
                                print(f"  {player.name}: {card.type} (excluded)")
                
                # Return cards to deck
                for player in players:
                    deck.extend(player.hand)
                    player.hand = []
                    player.excluded = False
                random.shuffle(deck)
                
                if verbose:
                    print(f"\nTie-breaker score: Good {good_score} | Bad {bad_score}")
            
            # Final tie-breaker winner
            if good_score > bad_score:
                if verbose:
                    print("🎉 GOOD TEAM WINS TIE-BREAKER!")
                winner = "good"
            else:
                if verbose:
                    print("😈 BAD TEAM WINS TIE-BREAKER!")
                winner = "bad"
    
    # Show game history
    if verbose:
        print(f"\n{'='*50}")
        print("GAME HISTORY:")
        print(f"Bad voters history: {bad_voters_history}")
        print(f"Exclusion history: {exclusion_history}")
        player_stats = {p.name: p.bad_votes for p in players}
        print(f"Final bad vote counts: {player_stats}")
        print(f"{'='*50}")
    
    # Return game results
    return {
        'winner': winner,
        'good_score': good_score,
        'bad_score': bad_score,
        'rounds': round_num,
        'bad_players': bad_players,
        'good_players': good_players,
        'bad_cards_count': bad_cards,
        'good_cards_count': good_cards,
        'exclusions': exclusion_history,
        'total_bad_votes': sum(p.bad_votes for p in players)
    }

def demo_game():
    """Run a single demo game with verbose output"""
    return simulate_game(verbose=True)

if __name__ == "__main__":
    demo_game()