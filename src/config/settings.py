"""Configuration settings for the MCP client application."""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "claude-3-5-sonnet-20241022")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))

SSE_ENDPOINT = os.getenv("SSE_ENDPOINT", "http://localhost:8000/sse")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "5000"))
ENV = os.getenv("ENV", "development")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def validate_config() -> Dict[str, Any]:
    """Validate essential configuration settings.
    
    Returns:
        Dict[str, Any]: Dictionary of validation issues or empty if valid
    """
    issues = {}
    
    if not ANTHROPIC_API_KEY:
        issues["ANTHROPIC_API_KEY"] = "Missing API key"
    
    if not SSE_ENDPOINT:
        issues["SSE_ENDPOINT"] = "Missing SSE endpoint URL"
    
    return issues