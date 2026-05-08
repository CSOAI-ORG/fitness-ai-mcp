<div align="center">

# Fitness Ai MCP

**Fitness AI MCP Server**

[![PyPI](https://img.shields.io/pypi/v/meok-fitness-ai-mcp)](https://pypi.org/project/meok-fitness-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Fitness AI MCP Server
Health and fitness tools powered by MEOK AI Labs.

## Tools

| Tool | Description |
|------|-------------|
| `generate_workout` | Generate a complete workout plan tailored to goals and equipment. |
| `track_calories` | Track daily calorie and macronutrient intake from food entries. |
| `calculate_body_composition` | Calculate BMI, body fat estimate, BMR, and TDEE. |
| `build_training_plan` | Build a multi-week training program with periodization. |
| `check_exercise_form` | Get exercise form cues, common mistakes, and muscle activation info. |

## Installation

```bash
pip install meok-fitness-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "fitness-ai": {
      "command": "python",
      "args": ["-m", "meok_fitness_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 5 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
