"""Message processing and tool calling functionality."""
from typing import List, Dict, Any, Optional
import json

from anthropic import Anthropic

from src.utils.helpers import setup_logger, format_tool_response
from src.config.settings import MODEL_NAME, MAX_TOKENS

logger = setup_logger()

class MessageProcessor:
    """Processes messages and handles tool calling."""
    
    def __init__(self, anthropic_client: Anthropic, connection):
        """Initialize the message processor.
        
        Args:
            anthropic_client: Initialized Anthropic client
            connection: Server connection manager
        """
        self.anthropic = anthropic_client
        self.connection = connection
    
    async def process_query(self, query: str, available_tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a query using Claude and available tools.
        
        Args:
            query: User input query
            available_tools: List of available tools
            
        Returns:
            Dict[str, Any]: Response with text, tool calls, and results
        """
        # Initialize conversation with user query
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]
        
        # Store final result data
        result = {
            "text": [],
            "tool_calls": [],
            "tool_results": []
        }
        
        # Process the conversation until no more tool calls
        while True:
            # Call the model
            logger.debug(f"Sending {len(messages)} messages to model")
            response = self.anthropic.messages.create(
                model=MODEL_NAME,
                max_tokens=MAX_TOKENS,
                messages=messages,
                tools=available_tools,
                stream=True,
            )
            
            # Process the response content
            assistant_message_content = []
            tool_calls = []
            
            for content in response.content:
                if content.type == 'text':
                    text_content = content.text.strip()
                    if text_content:
                        result["text"].append(text_content)
                    assistant_message_content.append(content)
                    
                elif content.type == 'tool_use':
                    tool_calls.append(content)
                    assistant_message_content.append(content)
                    # Add tool call to results
                    result["tool_calls"].append({
                        "id": content.id,
                        "name": content.name,
                        "args": content.input
                    })
            
            # If no tool calls, we're done
            if not tool_calls:
                # Add the assistant's message to the conversation
                if assistant_message_content:
                    messages.append({
                        "role": "assistant",
                        "content": assistant_message_content
                    })
                break
                
            # Add the assistant's message to the conversation
            messages.append({
                "role": "assistant",
                "content": assistant_message_content
            })
            
            # Process tool calls
            for tool_call in tool_calls:
                tool_name = tool_call.name
                tool_args = tool_call.input
                
                try:
                    # Execute the tool call
                    result_data = await self.connection.call_tool(tool_name, tool_args)
                    
                    # Add tool result to results
                    tool_result = {
                        "tool_use_id": tool_call.id,
                        "name": tool_name,
                        "args": tool_args,
                        "result": result_data.content,
                        "status": "success"
                    }
                    result["tool_results"].append(tool_result)
                    
                    # Add tool result to conversation
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_call.id,
                                "content": result_data.content
                            }
                        ]
                    })
                    
                except Exception as e:
                    error_message = f"Error executing tool {tool_name}: {str(e)}"
                    logger.error(error_message)
                    
                    # Add error result to results
                    tool_result = {
                        "tool_use_id": tool_call.id,
                        "name": tool_name,
                        "args": tool_args,
                        "error": str(e),
                        "status": "error"
                    }
                    result["tool_results"].append(tool_result)
                    
                    # Add error result to conversation
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_call.id,
                                "content": f"Error: {str(e)}"
                            }
                        ]
                    })
        
        # Return the complete result
        return result