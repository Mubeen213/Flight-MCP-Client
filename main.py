#!/usr/bin/env python3
"""
MCP API Server - A REST API for interacting with ModelContextProtocol servers.

This script starts a Flask server that exposes endpoints for chat and tool calling.
"""
import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS

from src.api.routes import api
from src.api.middleware import log_request
from src.config.settings import API_HOST, API_PORT, ENV, validate_config, SSE_ENDPOINT
from src.utils.helpers import setup_logger

logger = setup_logger()

def create_app():
    """Create and configure the Flask application.
    
    Returns:
        Flask: Configured Flask application
    """
    config_issues = validate_config()
    if config_issues:
        issues_str = ", ".join(f"{k}: {v}" for k, v in config_issues.items())
        logger.error(f"Configuration issues: {issues_str}")
        sys.exit(1)
    
    app = Flask(__name__)
    
    CORS(app)
    
    app.before_request(log_request)

    app.register_blueprint(api, url_prefix='/api')

    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            "service": "MCP Client API",
            "version": "1.0.0",
            "status": "running"
        })
    
    return app

if __name__ == "__main__":
    app = create_app()
    debug = ENV == "development"
    
    logger.info(f"Starting MCP API server on {API_HOST}:{API_PORT}")
    logger.info(f"Connecting to MCP server at {SSE_ENDPOINT}")
    
    app.run(host=API_HOST, port=API_PORT, debug=debug)