#!/bin/bash
# Simple wrapper for running the automation loop

echo "🎮 Mafia Game Automation Loop"
echo "=============================="
echo ""
echo "Options:"
echo "1. Run 5 games"
echo "2. Run 10 games" 
echo "3. Run continuously (Ctrl+C to stop)"
echo "4. Run with custom settings"
echo ""
read -p "Choose option (1-4): " choice

case $choice in
    1)
        echo "Running 5 games..."
        python3 run_loop.py --games 5
        ;;
    2)
        echo "Running 10 games..."
        python3 run_loop.py --games 10
        ;;
    3)
        echo "Running continuously (Ctrl+C to stop)..."
        python3 run_loop.py
        ;;
    4)
        echo ""
        read -p "Number of games (leave empty for infinite): " games
        read -p "Quick results only? (y/n): " quick
        
        args=""
        if [[ -n "$games" ]]; then
            args="$args --games $games"
        fi
        if [[ "$quick" == "y" ]]; then
            args="$args --quick"
        fi
        
        echo "Running with args: $args"
        python3 run_loop.py $args
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac