#!/usr/bin/env python3
"""
PokéArena (Hackathon edition) — Multi-Agent Prompt
A multi-agent system using smolagents framework with Gemini LLM.
"""

import asyncio
import json
import sys
import os
from typing import Dict, List, Optional, Any

# Check for Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY environment variable not set")
    print("Please set it with: export GEMINI_API_KEY=your_api_key")
    sys.exit(1)

# Import smolagents
from smolagents import CodeAgent, ToolCallingAgent
from smolagents.models import LiteLLMModel
from smolagents.tools import Tool
from smolagents.agents import PromptTemplates


class TypeWheel:
    """Simplified type effectiveness wheel."""
    
    SUPER_EFFECTIVE = {
        'water': ['fire'], 'fire': ['grass'], 'grass': ['water'], 'electric': ['water'],
        'ground': ['electric'], 'ice': ['dragon'], 'fighting': ['ice'], 
        'psychic': ['fighting'], 'dark': ['psychic'], 'fairy': ['dragon'], 'ghost': ['psychic']
    }
    
    IMMUNITY = {'ground': ['electric']}
    
    @classmethod
    def get_multiplier(cls, attacker_type: str, defender_type: str) -> float:
        """Get type effectiveness multiplier."""
        attacker_type, defender_type = attacker_type.lower(), defender_type.lower()
        
        if attacker_type in cls.IMMUNITY and defender_type in cls.IMMUNITY[attacker_type]:
            return 0.0
        if attacker_type in cls.SUPER_EFFECTIVE and defender_type in cls.SUPER_EFFECTIVE[attacker_type]:
            return 2.0
        if defender_type in cls.SUPER_EFFECTIVE and attacker_type in cls.SUPER_EFFECTIVE[defender_type]:
            return 0.5
        return 1.0
    
    @classmethod
    def calculate_attack_multiplier(cls, attacker_types: List[str], defender_types: List[str]) -> float:
        """Calculate attack multiplier for attacker vs defender."""
        if not attacker_types or not defender_types:
            return 1.0
        
        max_multiplier = 0.0
        for attacker_type in attacker_types:
            current_multiplier = 1.0
            for defender_type in defender_types:
                current_multiplier *= cls.get_multiplier(attacker_type, defender_type)
            max_multiplier = max(max_multiplier, current_multiplier)
        
        return max_multiplier


class PokemonMCPTool(Tool):
    """MCP tool to fetch Pokemon data."""
    
    name = "fetch_pokemon"
    description = "Fetch Pokemon data by name using pokemon-mcp-server"
    inputs = {
        "name": {
            "type": "string", 
            "description": "The name of the Pokemon to fetch"
        }
    }
    output_type = "string"
    
    def forward(self, name: str) -> str:
        """Fetch Pokemon data via MCP server."""
        try:
            # Mock data for testing - in real implementation would call MCP server
            pokemon_db = {
                "pikachu": {"name": "pikachu", "types": ["electric"], "base_total": 320},
                "squirtle": {"name": "squirtle", "types": ["water"], "base_total": 314},
                "charmander": {"name": "charmander", "types": ["fire"], "base_total": 309},
                "bulbasaur": {"name": "bulbasaur", "types": ["grass", "poison"], "base_total": 318},
                "gyarados": {"name": "gyarados", "types": ["water", "flying"], "base_total": 540},
                "charizard": {"name": "charizard", "types": ["fire", "flying"], "base_total": 534}
            }
            
            normalized_name = name.strip().lower()
            if normalized_name in pokemon_db:
                return json.dumps(pokemon_db[normalized_name])
            else:
                return json.dumps({"error": "unknown_pokemon", "suggestion": "check spelling"})
                
        except Exception as e:
            return json.dumps({"error": "unknown_pokemon", "suggestion": "check spelling"})


def create_scout_agent(side: str, model: LiteLLMModel) -> ToolCallingAgent:
    """Create a Scout agent with appropriate system prompt."""
    
    agent = ToolCallingAgent(
        tools=[PokemonMCPTool()],
        model=model
    )
    
    return agent


def create_referee_agent(model: LiteLLMModel) -> CodeAgent:
    """Create a Referee agent with appropriate system prompt."""
    
    agent = CodeAgent(
        tools=[],
        model=model
    )
    
    return agent


async def main():
    """Main orchestrator function."""
    if len(sys.argv) != 3:
        print("Usage: python main.py <pokemon1> <pokemon2>")
        sys.exit(1)
    
    pokemon1_name = sys.argv[1]
    pokemon2_name = sys.argv[2]
    
    print(f"🔥 PokéArena Battle: {pokemon1_name} vs {pokemon2_name}")
    print("=" * 50)
    
    try:
        # Initialize Gemini model via LiteLLM
        model = LiteLLMModel(
            model_id="gemini/gemini-2.0-flash-exp",
            api_key=GEMINI_API_KEY
        )
        
        # Create agents
        scout_left = create_scout_agent("Left", model)
        scout_right = create_scout_agent("Right", model)
        referee = create_referee_agent(model)
        
        print("🕵️ Deploying smolagents scouts...")
        
        # Create scout prompts with role information
        scout_left_prompt = f"""You are Scout-Left, a Pokemon data fetcher agent.

**Role:** Fetch canonical Pokémon data for {pokemon1_name} using the fetch_pokemon tool.
**Goal:** Return structured JSON with name, types, and base_total.

**Instructions:**
1. Use the fetch_pokemon tool to get Pokemon data for {pokemon1_name}
2. Return ONLY valid JSON, no additional text

**Output Format:**
{{"name": "<resolved_name>", "types": ["<type1>", "<type2_optional>"], "base_total": 0}}

**Error Format:**
{{"error": "unknown_pokemon", "suggestion": "check spelling"}}

Fetch data for: {pokemon1_name}"""

        scout_right_prompt = f"""You are Scout-Right, a Pokemon data fetcher agent.

**Role:** Fetch canonical Pokémon data for {pokemon2_name} using the fetch_pokemon tool.
**Goal:** Return structured JSON with name, types, and base_total.

**Instructions:**
1. Use the fetch_pokemon tool to get Pokemon data for {pokemon2_name}
2. Return ONLY valid JSON, no additional text

**Output Format:**
{{"name": "<resolved_name>", "types": ["<type1>", "<type2_optional>"], "base_total": 0}}

**Error Format:**
{{"error": "unknown_pokemon", "suggestion": "check spelling"}}

Fetch data for: {pokemon2_name}"""

        # Run scouts concurrently
        def run_scout_left():
            return scout_left.run(scout_left_prompt)
        
        def run_scout_right():
            return scout_right.run(scout_right_prompt)
        
        # Execute scouts in parallel
        loop = asyncio.get_event_loop()
        p1_result, p2_result = await asyncio.gather(
            loop.run_in_executor(None, run_scout_left),
            loop.run_in_executor(None, run_scout_right)
        )
        
        print(f"Scout-Left result: {p1_result}")
        print(f"Scout-Right result: {p2_result}")
        
        # Parse scout results
        try:
            p1_data = json.loads(p1_result.strip())
            p2_data = json.loads(p2_result.strip())
        except json.JSONDecodeError:
            print("❌ Error: Could not parse scout results")
            return
        
        # Check for errors
        if "error" in p1_data:
            print(f"❌ Error: {pokemon1_name} not found. {p1_data.get('suggestion', '')}")
            return
        
        if "error" in p2_data:
            print(f"❌ Error: {pokemon2_name} not found. {p2_data.get('suggestion', '')}")
            return
        
        print("⚖️ Handoff to referee...")
        
        # Prepare referee input with detailed instructions
        referee_input = f"""You are the Referee, a Pokemon battle judge agent.

**Role:** Decide the victor using the simplified type wheel.

**Type Effectiveness Rules:**
- Super-effective (2.0×): water>fire, fire>grass, grass>water, electric>water, ground>electric, ice>dragon, fighting>ice, psychic>fighting, dark>psychic, fairy>dragon, ghost>psychic
- Not very effective (0.5×): reverse of super-effective pairings  
- Immunity (0.0×): ground immune to electric
- Dual types: multiply defender multipliers
- Multiple attacker types: use maximum multiplier

**Computation Logic:**
For each attacker type vs each defender type, multiply pairwise multipliers. 
If attacker has two types, take the MAXIMUM attack path.

**Tie-break:** Compare base_total (higher wins). If equal → draw.

**Confidence:** Map multiplier delta to [0.60-0.95]; tie-break caps at 0.75; draw = 0.50.

**Battle Data:**
Pokemon 1: {json.dumps(p1_data)}
Pokemon 2: {json.dumps(p2_data)}

**Task:** Apply the type effectiveness rules and determine the winner.

**Output ONLY this JSON format with playful reasoning:**
{{"winner": "<p1|p2|draw>", "reasoning": "<one sentence, playful>", "p1": {json.dumps(p1_data)}, "p2": {json.dumps(p2_data)}, "scores": {{"p1_attack_multiplier_vs_p2": 1.0, "p2_attack_multiplier_vs_p1": 2.0}}, "sources": ["pokemon-mcp-server: fetch_pokemon"], "confidence": 0.0}}

Return ONLY the JSON, no additional text."""
        
        # Get referee decision
        referee_result = referee.run(referee_input)
        print(f"Referee result: {referee_result}")
        
        # Parse and display result
        try:
            if isinstance(referee_result, dict):
                result = referee_result
            else:
                # Fix JSON formatting issues (contractions and quotes)
                import re
                referee_result_fixed = referee_result
                # Handle contractions like "Squirtle"s" -> "Squirtle's" 
                referee_result_fixed = re.sub(r'"([^"]*)"s\b', r'"\1\'s', referee_result_fixed)
                result = json.loads(referee_result_fixed)
            
            print("\n" + "=" * 50)
            print(f"🏆 Referee: {result['reasoning']}")
            print(f"\n📊 Full Battle Report:")
            print(json.dumps(result, indent=2))
        except (json.JSONDecodeError, TypeError) as e:
            print("❌ Error: Could not parse referee result")
            print(f"Raw result: {referee_result}")
            print(f"Error: {e}")
        
    except Exception as e:
        print(f"💥 System Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())