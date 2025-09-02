#!/usr/bin/env python3
"""
Village Simulator - Main Entry Point

LLM-powered village survival simulator where 3-5 NPCs create emergent 
narratives through conversational dynamics.
"""

import sys
import os
import logging

# Add the parent directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from citysim.director.cli_interface import main

if __name__ == "__main__":
    main()