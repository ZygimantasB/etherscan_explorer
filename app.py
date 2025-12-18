"""
Crypto Explorer - Multi-chain Blockchain Address Explorer
Main application entry point.
"""

from flask import Flask
from routes import register_blueprints
from utils import register_template_filters


def create_app():
    """Application factory function."""
    app = Flask(__name__)

    # Register template filters
    register_template_filters(app)

    # Register blueprints
    register_blueprints(app)

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
