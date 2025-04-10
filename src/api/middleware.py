"""API middleware functions for the MCP client."""
from flask import request
import time
from src.utils.helpers import setup_logger

logger = setup_logger()

def log_request():
    """Log incoming API requests.
    
    This function is designed to be used with Flask's before_request handler
    and logs details about each incoming request.
    """
    # Get current timestamp for request duration calculation
    request.start_time = time.time()
    
    # Log the request details
    logger.info(f"Request: {request.method} {request.path} | IP: {request.remote_addr}")
    
    # No need to return anything for before_request handlers


def log_response(response):
    """Log outgoing API responses.
    
    This function is designed to be used with Flask's after_request handler
    and logs details about each outgoing response, including request duration.
    
    Args:
        response: The Flask response object
        
    Returns:
        response: The unmodified Flask response object
    """
    # Calculate request duration if start_time was set
    duration = 0
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        
    # Log the response details
    logger.info(f"Response: {request.method} {request.path} | Status: {response.status_code} | Duration: {duration:.4f}s")
    
    return response