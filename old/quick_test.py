#!/usr/bin/env python3
"""Quick balance test with fewer configurations"""

from simulate import run_simulation_batch

def quick_balance_test():
    """Test a smaller set of configurations for faster results"""
    
    print("QUICK BALANCE TEST")
    print("="*50)
    
    # Test key configurations
    configs = [
        (1, 3, 10, 6),   # Fewer players, bad-heavy
        (1, 3, 8, 8),    # Fewer players, balanced cards
        (1, 4, 12, 8),   # Original config
        (1, 4, 10, 10),  # Original players, balanced cards
        (1, 4, 14, 6),   # Original players, bad-heavy
        (2, 3, 12, 8),   # More bad players
        (2, 4, 14, 10),  # More bad players, more cards
    ]
    
    results = []
    for bad_p, good_p, bad_c, good_c in configs:
        total_players = bad_p + good_p
        total_cards = bad_c + good_c
        
        # Skip if not enough cards
        if total_cards < total_players * 2:
            continue
            
        print(f"Testing {bad_p}B-{good_p}G vs {bad_c}b-{good_c}g...", end=" ")
        
        result = run_simulation_batch(bad_p, good_p, bad_c, good_c, 50)  # 50 runs each
        results.append(result)
        
        print(f"Good: {result['good_win_rate']:.1%}, Bad: {result['bad_win_rate']:.1%}, "
              f"Rounds: {result['avg_rounds']:.1f}, Balance: {result['balance_score']:.3f}")
    
    # Sort by balance
    results.sort(key=lambda x: x['balance_score'])
    
    print("\n" + "="*50)
    print("MOST BALANCED CONFIGURATIONS")
    print("="*50)
    
    for i, result in enumerate(results[:3], 1):
        print(f"{i}. {result['config']}")
        print(f"   Good: {result['good_win_rate']:.1%}, Bad: {result['bad_win_rate']:.1%}")
        print(f"   Rounds: {result['avg_rounds']:.1f}, Balance: {result['balance_score']:.3f}")
        print()

if __name__ == "__main__":
    quick_balance_test()