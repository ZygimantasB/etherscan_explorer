"""
Main page routes for Crypto Explorer.
Handles homepage, search, address detail, and other page views.
"""

from flask import Blueprint, render_template, request, redirect, url_for
from config import get_chain_config, get_all_chains
from services.blockchain import BlockchainClient
from services.analyzer import LinkAnalyzer
from utils import is_valid_address

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Homepage with search form."""
    chains = get_all_chains()
    return render_template('index.html', chains=chains)


@main_bp.route('/search')
def search():
    """Handle search and redirect to address page."""
    address = request.args.get('address', '').strip()
    chain = request.args.get('chain', 'ethereum').strip()

    if not address:
        return redirect(url_for('main.index'))

    # Validate address format
    if not is_valid_address(address):
        chains = get_all_chains()
        return render_template('index.html', chains=chains,
                             error='Invalid address format. Must be 0x followed by 40 hex characters.')

    # Validate chain
    if not get_chain_config(chain):
        chains = get_all_chains()
        return render_template('index.html', chains=chains, error=f'Unsupported chain: {chain}')

    return redirect(url_for('main.address_detail', chain=chain, address=address))


@main_bp.route('/address/<chain>/<address>')
def address_detail(chain, address):
    """Display address details with link analysis graph."""
    # Validate inputs
    if not is_valid_address(address):
        return render_template('error.html', error='Invalid address format'), 400

    chain_config = get_chain_config(chain)
    if not chain_config:
        return render_template('error.html', error=f'Unsupported chain: {chain}'), 400

    try:
        # Get address information
        client = BlockchainClient(chain)
        address_info = client.get_address_info(address)

        # Get related addresses for sidebar
        analyzer = LinkAnalyzer(chain)
        related = analyzer.get_related_addresses(address, limit=10)

        chains = get_all_chains()

        return render_template(
            'address.html',
            address_info=address_info,
            related_addresses=related,
            chains=chains,
            current_chain=chain
        )
    except Exception as e:
        return render_template('error.html', error=str(e)), 500


@main_bp.route('/compare')
def compare_page():
    """Address comparison page."""
    chains = get_all_chains()
    return render_template('compare.html', chains=chains)


@main_bp.route('/portfolio')
def portfolio_page():
    """Multi-chain portfolio page."""
    chains = get_all_chains()
    return render_template('portfolio.html', chains=chains)


@main_bp.route('/analytics')
def analytics_page():
    """Analytics dashboard page."""
    chains = get_all_chains()
    return render_template('analytics.html', chains=chains)


@main_bp.route('/advanced')
def advanced_page():
    """Advanced analytics page."""
    chains = get_all_chains()
    return render_template('advanced.html', chains=chains)
