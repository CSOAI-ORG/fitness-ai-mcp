# Fitness AI MCP

> Health and fitness tools - workout generation, calorie tracking, body composition, training plans, exercise form

Built by **MEOK AI Labs** | [meok.ai](https://meok.ai)

## Features

| Tool | Description |
|------|-------------|
| `generate_workout` | See tool docstring for details |
| `track_calories` | See tool docstring for details |
| `calculate_body_composition` | See tool docstring for details |
| `build_training_plan` | See tool docstring for details |
| `check_exercise_form` | See tool docstring for details |

## Installation

```bash
pip install mcp
```

## Usage

### As an MCP Server

```bash
python server.py
```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fitness-ai-mcp": {
      "command": "python",
      "args": ["/path/to/fitness-ai-mcp/server.py"]
    }
  }
}
```

## Rate Limits

Free tier includes **30-50 calls per tool per day**. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

Built with FastMCP by MEOK AI Labs
