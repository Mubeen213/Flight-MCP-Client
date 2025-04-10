"""API routes for the MCP client."""
import asyncio
from flask import Blueprint, request, jsonify
from functools import wraps

from src.client.mcp_client import get_client_instance
from src.config.settings import SSE_ENDPOINT
from src.utils.helpers import setup_logger

logger = setup_logger()
api = Blueprint('api', __name__)

def async_route(route_function):
    """Decorator to handle async route functions."""
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        return asyncio.run(route_function(*args, **kwargs))
    return wrapper

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "mcp-client-api"
    })

@api.route('/chat', methods=['POST'])
@async_route
async def process_chat():
    """Process a chat message.
    
    Expected JSON body:
    {
        "message": "User message here"
    }
    """
    try:
        logger.info("Processing chat request with payload: {request.json}")
        if not request.is_json:
            return jsonify({
                "status": "error",
                "error": "Content-Type must be application/json"
            }), 415
        data = request.json
        
        if not data or 'prompt' not in data:
            return jsonify({
                "status": "error",
                "error": "Missing 'message' in request body"
            }), 400
            
        message = data['prompt']
        client = await get_client_instance(SSE_ENDPOINT)
        result = await client.process_query(message)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@api.route('/tools', methods=['GET'])
@async_route
async def get_tools():
    """Get available tools from the MCP server."""
    try:
        client = await get_client_instance(SSE_ENDPOINT)
        tools = await client.get_available_tools()
        
        return jsonify(tools)
        
    except Exception as e:
        logger.error(f"Error getting tools: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@api.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({
        "status": "error",
        "error": "Resource not found"
    }), 404

@api.errorhandler(405)
def method_not_allowed(e):
    """Handle 405 errors."""
    return jsonify({
        "status": "error",
        "error": "Method not allowed"
    }), 405