"""Modular API routes for the MCP client."""
import asyncio
from flask import Blueprint, request, jsonify
from functools import wraps

from src.client.mcp_client import get_client_instance
from src.config.settings import SSE_ENDPOINT
from src.utils.helpers import setup_logger

# Constants for HTTP status codes
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_UNSUPPORTED_MEDIA_TYPE = 415
HTTP_INTERNAL_SERVER_ERROR = 500

logger = setup_logger()
api = Blueprint('api', __name__)

# Utility decorator to handle async route functions
def async_route(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        return asyncio.run(route_function(*args, **kwargs))
    return wrapper

# Validation helper function
def validate_json(required_fields):
    if not request.is_json:
        raise ValueError("Content-Type must be application/json")

    data = request.json
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(f"Missing fields in request body: {', '.join(missing_fields)}")

    return data

# Error response helper function
def error_response(message, status_code):
    return jsonify({
        "status": "error",
        "error": message
    }), status_code

# Routes
@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "mcp-client-api"
    }), HTTP_OK

@api.route('/chat', methods=['POST'])
@async_route
async def process_chat():
    """Process a chat message."""
    try:
        data = validate_json(required_fields=['prompt'])
        message = data['prompt']

        logger.info(f"Processing chat request: {message}")
        client = await get_client_instance(SSE_ENDPOINT)
        result = await client.process_query(message)

        return jsonify({
            "status": "success",
            "data": result
        }), HTTP_OK

    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        return error_response(str(ve), HTTP_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Unhandled error during chat processing: {e}")
        return error_response("Internal server error", HTTP_INTERNAL_SERVER_ERROR)

@api.route('/tools', methods=['GET'])
@async_route
async def get_tools():
    """Get available tools from the MCP server."""
    try:
        logger.info("Fetching available tools")
        client = await get_client_instance(SSE_ENDPOINT)
        tools = await client.get_available_tools()


        return jsonify({
            "status": "success",
            "tools": tools
        }), HTTP_OK

    except Exception as e:
        logger.error(f"Error fetching tools: {e}")
        return error_response("Could not retrieve tools", HTTP_INTERNAL_SERVER_ERROR)

# Error handlers
@api.errorhandler(HTTP_NOT_FOUND)
def not_found(e):
    logger.warning(f"404 error: {request.path} not found")
    return error_response("Resource not found", HTTP_NOT_FOUND)

@api.errorhandler(HTTP_METHOD_NOT_ALLOWED)
def method_not_allowed(e):
    logger.warning(f"405 error: Method {request.method} not allowed on {request.path}")
    return error_response("Method not allowed", HTTP_METHOD_NOT_ALLOWED)

@api.errorhandler(HTTP_UNSUPPORTED_MEDIA_TYPE)
def unsupported_media_type(e):
    logger.warning("415 error: Unsupported Media Type")
    return error_response("Unsupported Media Type, must be application/json", HTTP_UNSUPPORTED_MEDIA_TYPE)