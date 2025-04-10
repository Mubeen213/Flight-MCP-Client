"""MCP Server connection management."""
import os
from typing import Optional, Dict, Any
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.server.sse import SseServerTransport

from src.utils.helpers import setup_logger

logger = setup_logger()

class ServerConnection:
    """Manages connections to ModelContextProtocol servers via SSE."""
    
    def __init__(self):
        """Initialize the server connection manager."""
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
    
    async def connect_sse(self, endpoint: str) -> bool:
        """Connect to an MCP server via SSE.
        
        Args:
            endpoint: The SSE endpoint URL
            
        Returns:
            bool: True if connection successful, False otherwise
            
        Raises:
            ConnectionError: If connection to server fails
        """
        try:
            logger.info(f"Connecting to SSE endpoint: {endpoint}")
            streams = await self.exit_stack.enter_async_context(SseServerTransport(endpoint))
            self.session = await self.exit_stack.enter_async_context(ClientSession(streams[0], streams[1]))
            
            # Initialize session
            await self.session.initialize()
            logger.info("SSE server connection established successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to SSE server: {e}")
            await self.cleanup()
            raise ConnectionError(f"Failed to connect to SSE server: {e}")
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools from the connected MCP server.
        
        Returns:
            Dict[str, Any]: Server response containing available tools
            
        Raises:
            ConnectionError: If the server is not connected
        """
        if not self.session:
            raise ConnectionError("Not connected to an MCP server")
            
        try:
            response = await self.session.list_tools()
            return response
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            raise
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the connected MCP server.
        
        Args:
            tool_name: Name of the tool to call
            args: Arguments to pass to the tool
            
        Returns:
            Dict[str, Any]: Tool execution result
            
        Raises:
            ConnectionError: If the server is not connected
            Exception: If tool execution fails
        """
        if not self.session:
            raise ConnectionError("Not connected to an MCP server")
            
        try:
            logger.debug(f"Calling tool {tool_name} with args: {args}")
            result = await self.session.call_tool(tool_name, args)
            return result
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            raise
    
    async def cleanup(self):
        """Clean up resources."""
        try:
            logger.info("Cleaning up server connection resources")
            await self.exit_stack.aclose()
            self.session = None
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")