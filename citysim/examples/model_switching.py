#!/usr/bin/env python3
"""
Example of how to easily switch between different LLM models with Together API

This script shows three ways to change the model:
1. Set default model at module level
2. Pass model at initialization
3. Change model on existing instance
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from prompts.llm_interface import LLMInterface, DEFAULT_MODEL

def example_model_switching():
    """Show different ways to use different models"""
    
    print("=== Model Switching Examples ===\n")
    
    # Method 1: Use default model (set at module level)
    print(f"Default model: {DEFAULT_MODEL}")
    llm1 = LLMInterface()
    print(f"LLM1 using: {llm1.model_name}\n")
    
    # Method 2: Pass model at initialization
    llm2 = LLMInterface(model_name="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")
    print(f"LLM2 using: {llm2.model_name}\n")
    
    # Method 3: Change model on existing instance
    llm1.set_model("Qwen/Qwen2.5-72B-Instruct-Turbo")
    print(f"LLM1 now using: {llm1.model_name}\n")
    
    # Show available models
    print("Available models:")
    for i, model in enumerate(LLMInterface.get_available_models(), 1):
        print(f"  {i}. {model}")
    
    print("\n=== To change the default model ===")
    print("Edit citysim/prompts/llm_interface.py")
    print("Change the DEFAULT_MODEL variable at the top of the file")

if __name__ == "__main__":
    example_model_switching()