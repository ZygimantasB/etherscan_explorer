"""
Routes module for Crypto Explorer.
Contains Flask Blueprints for different route categories.
"""

from routes.main import main_bp
from routes.api_core import api_core_bp
from routes.api_analytics import api_analytics_bp
from routes.api_advanced import api_advanced_bp


def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    app.register_blueprint(main_bp)
    app.register_blueprint(api_core_bp)
    app.register_blueprint(api_analytics_bp)
    app.register_blueprint(api_advanced_bp)
