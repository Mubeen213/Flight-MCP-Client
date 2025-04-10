"""Helper utilities for the MCP client."""
import logging
import json
from typing import Dict, Any, List, Optional

from src.config.settings import LOG_LEVEL

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_client")

def setup_logger() -> logging.Logger:
    """Get configured application logger.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    return logger

def format_tool_response(tool_name: str, args: Dict[str, Any], result: str) -> str:
    """Format tool execution response for display.
    
    Args:
        tool_name: Name of the tool executed
        args: Arguments provided to the tool
        result: Result content from tool execution
    
    Returns:
        str: Formatted response string
    """
    try:
        # Try to parse and pretty-print JSON results
        parsed_result = json.loads(result)
        pretty_result = json.dumps(parsed_result, indent=2)
    except (json.JSONDecodeError, TypeError):
        pretty_result = result

    return f"\n[Tool: {tool_name}]\nArguments: {json.dumps(args, indent=2)}\nResult: {pretty_result}\n"