import re
from flask import Flask, render_template, request, jsonify, redirect, url_for
from config import get_chain_config, get_all_chains
from services.blockchain import BlockchainClient
from services.analyzer import LinkAnalyzer

app = Flask(__name__)


def is_valid_address(address):
    """Validate Ethereum-style address."""
    if not address:
        return False
    return bool(re.match(r'^0x[a-fA-F0-9]{40}$', address))


@app.route('/')
def index():
    """Homepage with search form."""
    chains = get_all_chains()
    return render_template('index.html', chains=chains)


@app.route('/search')
def search():
    """Handle search and redirect to address page."""
    address = request.args.get('address', '').strip()
    chain = request.args.get('chain', 'ethereum').strip()

    if not address:
        return redirect(url_for('index'))

    # Validate address format
    if not is_valid_address(address):
        chains = get_all_chains()
        return render_template('index.html', chains=chains, error='Invalid address format. Must be 0x followed by 40 hex characters.')

    # Validate chain
    if not get_chain_config(chain):
        chains = get_all_chains()
        return render_template('index.html', chains=chains, error=f'Unsupported chain: {chain}')

    return redirect(url_for('address_detail', chain=chain, address=address))


@app.route('/address/<chain>/<address>')
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


@app.route('/api/graph/<chain>/<address>')
def api_graph(chain, address):
    """API endpoint for D3.js graph data."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400

    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        analyzer = LinkAnalyzer(chain)
        graph_data = analyzer.build_graph(address)
        return jsonify(graph_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/address/<chain>/<address>')
def api_address(chain, address):
    """API endpoint for address information."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400

    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        address_info = client.get_address_info(address)
        return jsonify(address_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/expand/<chain>/<address>', methods=['POST'])
def api_expand(chain, address):
    """API endpoint to expand a node and get its connections."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400

    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        # Get existing nodes from request body
        data = request.get_json() or {}
        existing_nodes = data.get('existing_nodes', [])

        analyzer = LinkAnalyzer(chain)
        expand_data = analyzer.expand_node(address, existing_nodes)
        return jsonify(expand_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chains')
def api_chains():
    """API endpoint for supported chains."""
    return jsonify(get_all_chains())


@app.template_filter('format_value')
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


@app.template_filter('short_address')
def short_address(address):
    """Shorten address for display."""
    if address and len(address) > 10:
        return f'{address[:6]}...{address[-4:]}'
    return address or ''


@app.template_filter('timestamp_to_date')
def timestamp_to_date(timestamp):
    """Convert Unix timestamp to readable date."""
    from datetime import datetime
    if timestamp:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
    return ''


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
