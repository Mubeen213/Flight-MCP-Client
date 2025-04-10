"""Client for interacting with ModelContextProtocol servers."""
import sys
from typing import List, Dict, Any, Optional
import asyncio

from anthropic import Anthropic

from src.client.connection import ServerConnection
from src.config.settings import ANTHROPIC_API_KEY, MODEL_NAME, MAX_TOKENS, validate_config
from src.client.processor import MessageProcessor
from src.utils.helpers import setup_logger

logger = setup_logger()

class MCPClient:
    """Client for interacting with ModelContextProtocol servers."""
    
    def __init__(self):
        """Initialize the MCP client."""
        # Validate configuration
        config_issues = validate_config()
        if config_issues:
            issues_str = ", ".join(f"{k}: {v}" for k, v in config_issues.items())
            raise ValueError(f"Configuration issues: {issues_str}")
        
        # Initialize components
        self.anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.connection = ServerConnection()
        self.processor = MessageProcessor(self.anthropic, self.connection)
        self.available_tools = []
        self.connection_url = None
        
    async def connect(self, connection_url: str) -> bool:
        """Connect to an MCP server via SSE.
        
        Args:
            connection_url: Server SSE endpoint URL
            
        Returns:
            bool: True if connection successful
        """
        try:
            self.connection_url = connection_url
            connected = await self.connection.connect_sse(connection_url)
            
            if connected:
                # Fetch and store available tools
                response = await self.connection.list_tools()
                self.available_tools = [{
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                } for tool in response.tools]
                
                logger.info(f"Connected to server with {len(self.available_tools)} tools")
                return True
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query.
        
        Args:
            query: User input query
            
        Returns:
            Dict[str, Any]: Response with text and metadata
        """
        try:
            if not self.connection.session:
                await self.connect(self.connection_url)
                
            response = await self.processor.process_query(query, self.available_tools)
            return {
                "status": "success",
                "response": response
            }
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_available_tools(self) -> Dict[str, Any]:
        """Get available tools from the connected server.
        
        Returns:
            Dict[str, Any]: Available tools information
        """
        try:
            if not self.connection.session:
                await self.connect(self.connection_url)
                
            return {
                "status": "success",
                "tools": self.available_tools
            }
        except Exception as e:
            logger.error(f"Error getting available tools: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def cleanup(self):
        """Clean up resources."""
        await self.connection.cleanup()

# Singleton instance
_client_instance = None
_client_lock = asyncio.Lock()

async def get_client_instance(connection_url: str = None) -> MCPClient:
    """Get or create the MCP client singleton instance.
    
    Args:
        connection_url: Optional connection URL to use if client needs to be created
        
    Returns:
        MCPClient: Singleton client instance
    """
    global _client_instance
    
    async with _client_lock:
        if _client_instance is None:
            if not connection_url:
                raise ValueError("Connection URL is required for initial client creation")
                
            _client_instance = MCPClient()
            await _client_instance.connect(connection_url)
            
    return _client_instance