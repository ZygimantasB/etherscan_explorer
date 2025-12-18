"""
Utility functions for the Crypto Explorer application.
"""

import re
from datetime import datetime


def is_valid_address(address):
    """Validate Ethereum-style address."""
    if not address:
        return False
    return bool(re.match(r'^0x[a-fA-F0-9]{40}$', address))


def format_value(value):
    """Format crypto value for display."""
    if value is None:
        return '0'
    if value >= 1:
        return f'{value:,.4f}'
    elif value >= 0.0001:
        return f'{value:.6f}'
    elif value > 0:
        return f'{value:.10f}'
    return '0'


def short_address(address):
    """Shorten address for display."""
    if address and len(address) > 10:
        return f'{address[:6]}...{address[-4:]}'
    return address or ''


def timestamp_to_date(timestamp):
    """Convert Unix timestamp to readable date."""
    if timestamp:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
    return ''


def register_template_filters(app):
    """Register all template filters with the Flask app."""
    app.template_filter('format_value')(format_value)
    app.template_filter('short_address')(short_address)
    app.template_filter('timestamp_to_date')(timestamp_to_date)
