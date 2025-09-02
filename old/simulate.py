#!/usr/bin/env python3
"""
Game Balance Simulator

Tests different configurations of the card conspiracy game
to find balanced settings by running 100 simulations per config.
"""

import random
from collections import defaultdict
from demo_game import simulate_game

def run_simulation_batch(bad_players, good_players, bad_cards, good_cards, num_runs=100):
    """Run multiple simulations and return aggregated stats"""
    results = []
    
    for _ in range(num_runs):
        # Set random seed for reproducibility if needed
        result = simulate_game(bad_players, good_players, bad_cards, good_cards, verbose=False)
        results.append(result)
    
    # Aggregate statistics
    good_wins = sum(1 for r in results if r['winner'] == 'good')
    bad_wins = sum(1 for r in results if r['winner'] == 'bad')
    
    avg_rounds = sum(r['rounds'] for r in results) / len(results)
    avg_good_score = sum(r['good_score'] for r in results) / len(results)
    avg_bad_score = sum(r['bad_score'] for r in results) / len(results)

    g_ratio = good_players / (good_players+bad_players)
    desired_g_wr = (g_ratio + 0.5 + 0.5) / 3

    
    return {
        'config': f"{bad_players}B-{good_players}G vs {bad_cards}b-{good_cards}g",
        'bad_players': bad_players,
        'good_players': good_players, 
        'g_ratio': g_ratio,
        'desired_b_wr': desired_g_wr,
        'bad_cards_count': bad_cards,
        'good_cards_count': good_cards,
        'good_wins': good_wins,
        'bad_wins': bad_wins,
        'good_win_rate': good_wins / num_runs,
        'bad_win_rate': bad_wins / num_runs,
        'avg_rounds': round(avg_rounds, 1),
        'avg_good_score': round(avg_good_score, 1),
        'avg_bad_score': round(avg_bad_score, 1),
        'balance_score': abs(desired_g_wr - (good_wins / num_runs))  # Lower = more balanced
    }

def test_configurations():
    """Test various game configurations for balance"""
    
    print("="*80)
    print("CARD CONSPIRACY GAME BALANCE ANALYSIS")
    print("="*80)
    print("Testing different configurations (100 simulations each)...")
    print()
    
    configurations = []
    
    # Test different player counts
    for bad_p in [1]:
        for good_p in [3,4]:
            # Test different card ratios
            for total_cards in [(bad_p + good_p) * 8, (bad_p + good_p) * 10]:
                for bad_ratio in [0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]:
                    bad_c = int(total_cards * bad_ratio)
                    good_c = total_cards - bad_c
                    
                    # Skip if not enough total players for the card count
                    total_players = bad_p + good_p
                    if total_cards < total_players * 2:  # Each player needs 2 cards
                        continue
                    
                    config = {
                        'bad_players': bad_p,
                        'good_players': good_p,
                        'bad_cards': bad_c, 
                        'good_cards': good_c
                    }
                    configurations.append(config)
    
    # Remove duplicates
    unique_configs = []
    seen = set()
    for config in configurations:
        key = (config['bad_players'], config['good_players'], config['bad_cards'], config['good_cards'])
        if key not in seen:
            seen.add(key)
            unique_configs.append(config)
    
    print(f"Testing {len(unique_configs)} unique configurations...")
    print()
    
    # Run simulations
    results = []
    for i, config in enumerate(unique_configs, 1):
        print(f"[{i:2d}/{len(unique_configs)}] Testing {config['bad_players']}B-{config['good_players']}G vs {config['bad_cards']}b-{config['good_cards']}g cards...", end=" ")
        
        result = run_simulation_batch(**config)
        results.append(result)
        
        print(f"Good: {result['good_win_rate']:.1%}, Bad: {result['bad_win_rate']:.1%}, Rounds: {result['avg_rounds']}")
    
    # Sort by balance (closest to 50/50)
    results.sort(key=lambda x: x['balance_score'])
    
    print()
    print("="*80)
    print("MOST BALANCED CONFIGURATIONS")
    print("="*80)
    print(f"{'Config':<12} {'Good%':<6} {'Bad%':<6} {'Rounds':<7} {'G.Score':<7} {'B.Score':<7} {'Balance':<7}")
    print("-" * 80)
    
    for result in results[:15]:  # Show top 15 most balanced
        print(f"{result['config']:<12} "
              f"{result['good_win_rate']:.1%}  "
              f"{result['bad_win_rate']:.1%}  "
              f"{result['avg_rounds']:<7.1f} "
              f"{result['avg_good_score']:<7.1f} "
              f"{result['avg_bad_score']:<7.1f} "
              f"{result['balance_score']:<7.3f}")
    
    print()
    print("="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    
    best = results[0]
    print(f"Most balanced config: {best['config']}")
    print(f"Win rates: Good {best['good_win_rate']:.1%}, Bad {best['bad_win_rate']:.1%}")
    print(f"Average game length: {best['avg_rounds']} rounds")
    print(f"Average scores: Good {best['avg_good_score']}, Bad {best['avg_bad_score']}")
    
    # Find shortest games
    shortest = min(results, key=lambda x: x['avg_rounds'])
    print(f"\nShortest games: {shortest['config']} ({shortest['avg_rounds']} rounds avg)")
    
    # Find longest games  
    longest = max(results, key=lambda x: x['avg_rounds'])
    print(f"Longest games: {longest['config']} ({longest['avg_rounds']} rounds avg)")
    
    return results

def analyze_specific_config(bad_players=1, good_players=4, bad_cards=12, good_cards=8, runs=1000):
    """Deep analysis of a specific configuration"""
    print(f"="*60)
    print(f"DEEP ANALYSIS: {bad_players} Bad vs {good_players} Good | {bad_cards}b-{good_cards}g cards")
    print(f"="*60)
    print(f"Running {runs} simulations...")
    
    result = run_simulation_batch(bad_players, good_players, bad_cards, good_cards, runs)
    
    print(f"\nResults:")
    print(f"Good team wins: {result['good_wins']}/{runs} ({result['good_win_rate']:.1%})")
    print(f"Bad team wins: {result['bad_wins']}/{runs} ({result['bad_win_rate']:.1%})")
    print(f"Average rounds: {result['avg_rounds']}")
    print(f"Average final scores: Good {result['avg_good_score']}, Bad {result['avg_bad_score']}")
    print(f"Balance score: {result['balance_score']:.3f} (lower = more balanced)")
    
    return result

if __name__ == "__main__":
    # Run full configuration test
    all_results = test_configurations()
    
    print("\n" + "="*80)
    print("Want to analyze a specific configuration in detail?")
    print("Edit the script and call: analyze_specific_config(bad_players, good_players, bad_cards, good_cards)")
    print("="*80)