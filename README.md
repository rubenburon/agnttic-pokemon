# PokéArena (Hackathon Edition)

A multi-agent system to determine the winner between two Pokémon using type advantages.

## Features

- **Multi-Agent Architecture**: Three agents working in parallel with handoff
  - **Scout-Left & Scout-Right**: Fetch Pokémon data concurrently
  - **Referee**: Judge battles using type effectiveness
- **ReAct Loop**: Reason → Action → Observation → Result
- **Type Effectiveness System**: Simplified type wheel with multipliers
- **Dual-Type Support**: Handles complex type interactions
- **Error Handling**: Graceful failure for unknown Pokémon

## Usage

```bash
python main.py <pokemon1> <pokemon2>
```

### Examples

```bash
python main.py squirtle charmander    # Water beats Fire
python main.py pikachu squirtle       # Electric beats Water
python main.py bulbasaur charmander   # Fire beats Grass
python main.py gyarados charizard     # Complex dual-type battle
```

## Type Effectiveness Rules

- **Super-effective (2.0×)**: water>fire, fire>grass, grass>water, electric>water, ground>electric, ice>dragon, fighting>ice, psychic>fighting, dark>psychic, fairy>dragon, ghost>psychic
- **Not very effective (0.5×)**: Reverse of super-effective pairings
- **Immunity (0.0×)**: ground immune to electric
- **Dual types**: Multiply defender multipliers
- **Multiple attacker types**: Use maximum multiplier

## Output Format

The system outputs a human-readable one-liner followed by a detailed JSON report containing:

- Winner determination
- Type effectiveness multipliers  
- Pokémon stats and types
- Confidence score
- Source attribution

## Architecture

Single-file implementation (`main.py`) with:
- No external dependencies (Python standard library only)
- Concurrent agent execution with `asyncio`
- Mock MCP integration (easily replaceable with real pokemon-mcp-server)
- Clean separation of concerns between agents

## Requirements

- Python 3.7+
- No external dependencies required