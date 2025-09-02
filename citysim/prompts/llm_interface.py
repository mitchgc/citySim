#!/usr/bin/env python3
"""
LLM Interface - Manages communication with local and cloud LLMs

Handles prompt generation, LLM calls, response parsing, and error handling.
Now using Together API for cloud-based LLM inference.
"""

import asyncio
import aiohttp
import json
import logging
import re
import os
import ssl
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv
import time

from .prompt_builder import PromptBuilder

# Load environment variables
load_dotenv()

# Model configuration - change this to easily switch between models
DEFAULT_MODEL = "deepseek-ai/DeepSeek-V3.1"

# Other available models you can try:
# "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
# "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo" 
# "mistralai/Mixtral-8x7B-Instruct-v0.1"
# "Qwen/Qwen2.5-72B-Instruct-Turbo"
# "microsoft/WizardLM-2-8x22B"

class LLMInterface:
    """Interface for communicating with LLMs"""
    
    def _attempt_json_repair(self, json_text: str) -> str:
        """Attempt to repair common JSON issues"""
        # Fix unterminated strings at end of JSON
        if json_text.strip().endswith('```'):
            # Already properly terminated
            return json_text
            
        # Check for unterminated string at the end
        if json_text.count('"') % 2 == 1:
            # Odd number of quotes - likely unterminated string
            # Find the last quote and see if it needs closing
            last_quote_pos = json_text.rfind('"')
            if last_quote_pos != -1:
                # Check if this quote is opening a string value
                after_quote = json_text[last_quote_pos + 1:].strip()
                # If there's content after the quote but no closing quote, add one
                if after_quote and not after_quote.endswith('"'):
                    # Add closing quote before any trailing braces/brackets
                    closing_chars = ''
                    while after_quote and after_quote[-1] in '}]':
                        closing_chars = after_quote[-1] + closing_chars
                        after_quote = after_quote[:-1].strip()
                    
                    json_text = json_text[:last_quote_pos + 1] + after_quote + '"' + closing_chars
        
        # Ensure proper JSON structure closure
        open_braces = json_text.count('{') - json_text.count('}')
        open_brackets = json_text.count('[') - json_text.count(']')
        
        # Add missing closing braces/brackets
        json_text += '}' * open_braces
        json_text += ']' * open_brackets
        
        return json_text
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Unified JSON parsing function (same as mafia.py)"""
        # print("new version")
        try:
            # Extract JSON from markdown code blocks if present
            json_text = content
            # print(json_text)
            if "```json" in json_text:
                # Extract content between ```json and ```
                start = json_text.find("```json") + 7
                end = json_text.find("```", start)
                if end != -1:
                    json_text = json_text[start:end].strip()
            
            # Fix all Unicode quotes that break JSON parsing (exactly like mafia.py)
            json_text = json_text.replace(""", '"').replace(""", '"').replace("'", "'").replace("'", "'")
            # Also handle smart/curly apostrophes and additional quote variants
            json_text = json_text.replace("’", "").replace("’", "").replace("‚", "'").replace("„", '"').replace("‟", '"').replace("”",'"').replace("…","...").replace("“",'"').replace("–","-")
            # More aggressive control character cleaning for JSON strings
            # Replace newlines and tabs in JSON string values with spaces
            json_text = re.sub(r'[\r\n\t]', ' ', json_text)
            # Remove other control characters that can break JSON parsing
            json_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', json_text)
            # Clean up multiple spaces
            json_text = re.sub(r'\s+', ' ', json_text)
            
            # Try to parse the JSON
            try: 
                loaded_json = json.loads(json_text)
                return loaded_json
            except json.JSONDecodeError as parse_error:
                # Debug information when JSON parsing fails
                print("Non-ASCII characters found:")
                for i, char in enumerate(json_text):
                    if ord(char) > 127:
                        print(f"Position {i}: {repr(char)} (Unicode: U+{ord(char):04X})")
                
                print(f"JSON parse error at line {parse_error.lineno}, column {parse_error.colno}")
                print(f"Error message: {parse_error.msg}")
                
                # Show the problematic area
                lines = json_text.split('\n')
                if parse_error.lineno <= len(lines):
                    problematic_line = lines[parse_error.lineno - 1]
                    print(f"Problematic line: {repr(problematic_line)}")
                
                # Re-raise the error so it's caught by the outer except block
                raise parse_error
                
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Invalid JSON in response: {e}")
            self.logger.error(f"Response: {content[:200]}...")  # Show first 200 chars
            return {}
        except Exception as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
            return {}
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self.prompt_builder = PromptBuilder()
        self.logger = logging.getLogger(__name__)
        
        # Together API configuration
        self.api_key = os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("TOGETHER_API_KEY not found in environment variables")
        
        self.api_url = "https://api.together.xyz/v1/chat/completions"
        
        # Response tracking
        self.total_calls = 0
        self.total_tokens_estimate = 0
        self.average_response_time = 0.0
        
    def set_model(self, model_name: str):
        """Easily change the model being used"""
        self.model_name = model_name
        self.logger.info(f"Model changed to: {model_name}")
        
    @classmethod
    def get_available_models(cls):
        """Get list of commonly available models"""
        return [
            "deepseek-ai/DeepSeek-V3.1",
            "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", 
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "Qwen/Qwen2.5-72B-Instruct-Turbo",
            "microsoft/WizardLM-2-8x22B"
        ]
        
    async def generate_npc_turn(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an NPC's conversational turn"""
        prompt = self.prompt_builder.build_turn_prompt(context)
        
        self.logger.debug(f"Generated turn prompt ({self.prompt_builder.estimate_tokens(prompt)} tokens)")
        
        response = await self._call_llm(prompt, context.get("personal", {}).get("name", "NPC"))
        
        if response["success"]:
            return self._parse_turn_response(response["content"])
        else:
            return self._fallback_turn_response(context)
            
    async def generate_interjection_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate interjection decision for observing NPC"""
        prompt = self.prompt_builder.build_interjection_prompt(context)
        
        response = await self._call_llm(prompt, context.get("personal", {}).get("name", "NPC"))
        
        if response["success"]:
            return self._parse_interjection_response(response["content"])
        else:
            return {"wants_to_interject": False, "observation": "listening"}
            
    async def generate_beat_reflection(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate beat reflection for relationship updates"""
        prompt = self.prompt_builder.build_reflection_prompt(context)
        
        response = await self._call_llm(prompt, context.get("personal", {}).get("name", "NPC"))
        
        if response["success"]:
            return self._parse_reflection_response(response["content"], context)
        else:
            return {"relationships": {}, "knowledge_gained": {"facts": [], "suspicions": [], "gossip_worthy": []}}
            
    async def generate_memory_compression(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate compressed memories for scene end"""
        prompt = self.prompt_builder.build_compression_prompt(context)
        
        response = await self._call_llm(prompt, context.get("personal", {}).get("name", "NPC"))
        
        if response["success"]:
            return self._parse_compression_response(response["content"])
        else:
            return {"specific_memories": [], "general_impressions": [], "lesson": ""}
            
    async def _call_llm(self, prompt: str, character_name: str = "NPC") -> Dict[str, Any]:
        """Make async call to Together API with error handling"""
        start_time = time.time()
        
        # Log the prompt (like mafia.py)
        self.logger.info(f"")
        self.logger.info(f"{'='*50}")
        self.logger.info(f"CHARACTER: {character_name.upper()}")
        self.logger.info(f"{'='*50}")
        self.logger.info(f"📝 PROMPT:")
        self.logger.info("-" * 40)
        self.logger.info(prompt)
        self.logger.info("-" * 40)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 1.05,
            "stream": False,
            "max_tokens": 1000
        }
        
        # Use longer timeout and SSL context
        timeout = aiohttp.ClientTimeout(total=120)  # 2 minutes
        
        # Create SSL context that doesn't verify certificates (for development)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        try:
            async with aiohttp.ClientSession(timeout=timeout, connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        llm_response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        
                        # Update statistics
                        response_time = time.time() - start_time
                        self._update_stats(prompt, response_time)
                        
                        # Log raw response (like mafia.py)
                        if llm_response.strip():
                            self.logger.info(f"RAW RESPONSE:")
                            self.logger.info(f"{llm_response.strip()}")
                        else:
                            self.logger.warning(f"RAW RESPONSE: [EMPTY - NO OUTPUT FROM MODEL]")
                        
                        return {
                            "success": True,
                            "content": llm_response,
                            "response_time": response_time,
                            "model": self.model_name
                        }
                    else:
                        error_text = await response.text()
                        self.logger.error(f"🚫 HTTP ERROR {response.status} - {error_text}")
                        
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}",
                            "response_time": time.time() - start_time
                        }
                        
        except asyncio.TimeoutError:
            self.logger.error(f"🚫 CONNECTION TIMEOUT for {character_name}")
            return {
                "success": False,
                "error": "Request timeout",
                "response_time": time.time() - start_time
            }
        except Exception as e:
            self.logger.error(f"🚫 CONNECTION ERROR: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }
            
    def _update_stats(self, prompt: str, response_time: float):
        """Update LLM call statistics"""
        self.total_calls += 1
        self.total_tokens_estimate += self.prompt_builder.estimate_tokens(prompt)
        
        # Update moving average of response time
        if self.average_response_time == 0:
            self.average_response_time = response_time
        else:
            self.average_response_time = (self.average_response_time * 0.9) + (response_time * 0.1)
            
    def _parse_turn_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response for conversational turn (using unified parser)"""
        
        response = self._parse_json_response(content)
        if not response:  # If parsing failed, return fallback
            return self._fallback_turn_response()
            
        # Validate required fields
        if "speaks" not in response:
            self.logger.error(f"❌ JSON missing 'speaks' key. Got: {list(response.keys())}")
            return self._fallback_turn_response()
                
        # Extract fields like mafia.py
        speaks = response["speaks"]
        conversation_target = None
        if "conversation_target" in response and response["conversation_target"] != "null":
            conversation_target = response["conversation_target"]
            self.logger.info(f"🎯 TARGET: {conversation_target}")
            
        # Log reasoning if available
        if "reasoning" in response:
            self.logger.info(f"🧠 REASONING: {response['reasoning']}")
            
        # Convert to citysim format
        return {
            "action": {
                "speaks": speaks.strip(),
                "does": response.get("does", None),
                "tone": response.get("tone", "neutral")
            },
            "internal": {
                "emotional_state": response.get("emotional_state", "neutral"),
                "wants_to_exit": response.get("wants_to_exit", False)
            },
            "conversation_target": conversation_target
        }
            
    def _parse_interjection_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response for interjection decision (with Unicode quote handling)"""
        try:
            # Extract JSON from markdown code blocks if present (like mafia.py)
            json_text = content.strip()
            if "```json" in json_text:
                start = json_text.find("```json") + 7
                end = json_text.find("```", start)
                if end != -1:
                    json_text = json_text[start:end].strip()
            
            # Fix Unicode quotes that break JSON parsing (like mafia.py)
            json_text = json_text.replace(""", '"').replace(""", '"').replace("'", "'").replace("'", "'")
            json_text = json_text.replace("'", "'").replace("'", "'").replace("‚", "'").replace("„", '"').replace("‟", '"')
            
            response = json.loads(json_text)
            
            response.setdefault("observation", "listening")
            response.setdefault("wants_to_interject", False)
            
            if response.get("wants_to_interject") and "interjection" not in response:
                # If they want to interject but didn't provide content, create default
                response["interjection"] = {
                    "speaks": "Wait, that's not right!",
                    "tone": "urgent",
                    "reason": "disagreement"
                }
                
            return response
            
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Invalid JSON in interjection response: {e}")
            self.logger.error(f"Response: {content[:200]}...")
            return {"observation": "listening", "wants_to_interject": False}
        except Exception as e:
            self.logger.warning(f"Failed to parse interjection response: {e}")
            return {"observation": "listening", "wants_to_interject": False}
            
    def _parse_reflection_response(self, content: str, context: Dict[str, Any] = "None") -> Dict[str, Any]:
        """Parse LLM response for beat reflection (using unified parser)"""
        
        response = self._parse_json_response(content)
        if not response:  # If parsing failed, return empty structure
            return {"relationships": {}, "knowledge_gained": {"facts": [], "suspicions": [], "gossip_worthy": []}}
        
        # Set default structure
        response.setdefault("relationships", {})
        response.setdefault("knowledge_gained", {
            "facts": [],
            "suspicions": [],
            "gossip_worthy": []
        })
        
        # Validate relationship entries have required fields and remove self-references
        validated_relationships = {}
        character_name = context.get("personal", {}).get("name", "") if context else ""
        
        for char, rel_data in response["relationships"].items():
            # Skip self-relationships - characters shouldn't reflect on themselves
            if char == character_name:
                self.logger.warning(f"Ignoring self-relationship entry for {char}")
                continue
                
            rel_data.setdefault("label", "complicated person")
            rel_data.setdefault("trust_delta", 0)
            rel_data.setdefault("affection_delta", 0)
            rel_data.setdefault("memory", "interacted somehow")
            validated_relationships[char] = rel_data
            
        response["relationships"] = validated_relationships
        return response
            
    def _parse_compression_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response for memory compression (with Unicode quote handling)"""
        try:
            # Extract JSON from markdown code blocks if present (like mafia.py)
            json_text = content.strip()
            if "```json" in json_text:
                start = json_text.find("```json") + 7
                end = json_text.find("```", start)
                if end != -1:
                    json_text = json_text[start:end].strip()
            
            # Fix Unicode quotes that break JSON parsing (like mafia.py)
            json_text = json_text.replace(""", '"').replace(""", '"').replace("'", "'").replace("'", "'")
            json_text = json_text.replace("'", "'").replace("'", "'").replace("‚", "'").replace("„", '"').replace("‟", '"')
            
            response = json.loads(json_text)
            
            response.setdefault("specific_memories", [])
            response.setdefault("general_impressions", [])
            response.setdefault("lesson", "")
            
            # Ensure we don't exceed limits
            response["specific_memories"] = response["specific_memories"][:3]
            response["general_impressions"] = response["general_impressions"][:2]
            
            return response
            
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Invalid JSON in compression response: {e}")
            self.logger.error(f"Response: {content[:200]}...")
            return {"specific_memories": [], "general_impressions": [], "lesson": ""}
        except Exception as e:
            self.logger.warning(f"Failed to parse compression response: {e}")
            return {"specific_memories": [], "general_impressions": [], "lesson": ""}
            
    def _fallback_turn_response(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Fallback response when LLM fails"""
        fallback_responses = [
            "I'm not sure what to say right now.",
            "Let me think about that for a moment.",
            "That's interesting. Tell me more.",
            "I need to consider this carefully."
        ]
        
        import random
        speaks = random.choice(fallback_responses)
        
        return {
            "action": {
                "speaks": speaks,
                "does": None,
                "tone": "thoughtful"
            },
            "internal": {
                "emotional_state": "confused",
                "wants_to_exit": False
            }
        }
        
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get LLM performance statistics"""
        return {
            "total_calls": self.total_calls,
            "total_tokens_estimate": self.total_tokens_estimate,
            "average_response_time": self.average_response_time,
            "model": self.model_name,
            "api_url": self.api_url
        }
        
    def reset_stats(self):
        """Reset performance statistics"""
        self.total_calls = 0
        self.total_tokens_estimate = 0
        self.average_response_time = 0.0