"""
Core API routes for Crypto Explorer.
Handles graph data, address info, gas prices, chains, exports, etc.
"""

import csv
import io
from flask import Blueprint, request, jsonify, Response
from config import get_chain_config, get_all_chains
from services.blockchain import BlockchainClient
from services.analyzer import LinkAnalyzer
from services.prices import get_token_prices
from services.labels import get_address_label, search_labels, get_category_addresses
from services.decoder import decode_transaction, get_transaction_summary
from utils import is_valid_address

api_core_bp = Blueprint('api_core', __name__)


@api_core_bp.route('/api/graph/<chain>/<address>')
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


@api_core_bp.route('/api/address/<chain>/<address>')
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


@api_core_bp.route('/api/expand/<chain>/<address>', methods=['POST'])
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


@api_core_bp.route('/api/chains')
def api_chains():
    """API endpoint for supported chains."""
    return jsonify(get_all_chains())


@api_core_bp.route('/api/prices')
def api_prices():
    """API endpoint for token prices."""
    tokens = request.args.get('tokens', 'ethereum').split(',')
    try:
        prices = get_token_prices(tokens)
        return jsonify(prices)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_core_bp.route('/api/gas/<chain>')
def api_gas(chain):
    """API endpoint for gas prices."""
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        # Get gas oracle data from Etherscan
        params = {
            'module': 'gastracker',
            'action': 'gasoracle'
        }
        gas_data = client._make_request(params)
        if gas_data:
            return jsonify({
                'low': float(gas_data.get('SafeGasPrice', 0)),
                'average': float(gas_data.get('ProposeGasPrice', 0)),
                'high': float(gas_data.get('FastGasPrice', 0)),
                'base_fee': float(gas_data.get('suggestBaseFee', 0))
            })
        return jsonify({'low': 0, 'average': 0, 'high': 0, 'base_fee': 0})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_core_bp.route('/api/decode/<chain>/<tx_hash>')
def api_decode_tx(chain, tx_hash):
    """API endpoint to decode a transaction."""
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        # Get transaction details
        params = {
            'module': 'proxy',
            'action': 'eth_getTransactionByHash',
            'txhash': tx_hash
        }
        tx_data = client._make_request(params)
        if tx_data:
            decoded = decode_transaction(tx_data)
            return jsonify(decoded)
        return jsonify({'error': 'Transaction not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_core_bp.route('/api/labels/search')
def api_search_labels():
    """API endpoint to search labels."""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify({'error': 'Query too short'}), 400

    results = search_labels(query)
    return jsonify(results)


@api_core_bp.route('/api/labels/category/<category>')
def api_category_labels(category):
    """API endpoint to get addresses by category."""
    addresses = get_category_addresses(category)
    return jsonify([{'address': k, **v} for k, v in addresses.items()])


@api_core_bp.route('/api/export/<chain>/<address>')
def api_export(chain, address):
    """Export address transactions as CSV."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400

    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    export_type = request.args.get('type', 'transactions')

    try:
        client = BlockchainClient(chain)

        output = io.StringIO()
        writer = csv.writer(output)

        if export_type == 'transactions':
            transactions = client.get_transactions(address, limit=500)
            writer.writerow(['Hash', 'Block', 'Timestamp', 'From', 'To', 'Value',
                           'Gas Used', 'Gas Price (Gwei)', 'Status'])
            for tx in transactions:
                writer.writerow([
                    tx['hash'],
                    tx['block_number'],
                    tx['timestamp'],
                    tx['from'],
                    tx['to'],
                    tx['value'],
                    tx['gas_used'],
                    tx['gas_price_gwei'],
                    'Success' if not tx['is_error'] else 'Failed'
                ])
        elif export_type == 'tokens':
            token_transfers = client.get_token_transfers(address, limit=500)
            writer.writerow(['Hash', 'Timestamp', 'Token', 'From', 'To', 'Amount', 'Direction'])
            for tx in token_transfers:
                writer.writerow([
                    tx['hash'],
                    tx['timestamp'],
                    tx['token_symbol'],
                    tx['from'],
                    tx['to'],
                    tx['value'],
                    tx['direction']
                ])
        elif export_type == 'balances':
            token_balances = client.get_token_balances(address)
            writer.writerow(['Token Symbol', 'Token Name', 'Balance', 'Contract Address',
                           'Transfers In', 'Transfers Out'])
            for token in token_balances:
                writer.writerow([
                    token['token_symbol'],
                    token['token_name'],
                    token['balance'],
                    token['contract_address'],
                    token['transfers_in'],
                    token['transfers_out']
                ])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={address[:10]}_{export_type}.csv'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_core_bp.route('/api/whales/<chain>')
def api_whales(chain):
    """API endpoint for recent whale transactions."""
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    min_value = float(request.args.get('min_value', 100))  # Minimum ETH value

    try:
        # Get recent large transactions from known whale addresses
        client = BlockchainClient(chain)
        # Get recent blocks
        params = {
            'module': 'proxy',
            'action': 'eth_blockNumber'
        }
        block_hex = client._make_request(params)
        if block_hex:
            # Get transactions from recent blocks
            whale_txs = []
            # For demo, we return exchange hot wallet activity
            exchange_addresses = get_category_addresses('exchange')
            for addr in list(exchange_addresses.keys())[:5]:
                txs = client.get_transactions(addr, limit=10)
                for tx in txs:
                    if tx['value'] >= min_value:
                        tx['whale_address'] = addr
                        tx['whale_name'] = exchange_addresses[addr]['name']
                        whale_txs.append(tx)

            whale_txs.sort(key=lambda x: x['timestamp'], reverse=True)
            return jsonify(whale_txs[:20])

        return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_core_bp.route('/api/portfolio')
def api_portfolio():
    """API endpoint for multi-chain portfolio view."""
    addresses = request.args.get('addresses', '').split(',')
    addresses = [a.strip() for a in addresses if is_valid_address(a.strip())]

    if not addresses:
        return jsonify({'error': 'No valid addresses provided'}), 400

    portfolio = {
        'total_usd': 0,
        'chains': {},
        'tokens': {},
        'nfts': []
    }

    for chain_id in ['ethereum', 'polygon', 'arbitrum', 'bsc']:
        try:
            client = BlockchainClient(chain_id)
            chain_total = 0

            for address in addresses:
                info = client.get_address_info(address)
                chain_total += info.get('total_portfolio_usd', 0)

                # Aggregate tokens
                for token in info.get('token_balances', []):
                    symbol = token['token_symbol']
                    if symbol not in portfolio['tokens']:
                        portfolio['tokens'][symbol] = {
                            'symbol': symbol,
                            'name': token['token_name'],
                            'balance': 0,
                            'value_usd': 0
                        }
                    portfolio['tokens'][symbol]['balance'] += token['balance']
                    portfolio['tokens'][symbol]['value_usd'] += token.get('value_usd', 0)

                # Aggregate NFTs
                portfolio['nfts'].extend(info.get('nft_holdings', []))

            portfolio['chains'][chain_id] = {
                'name': get_chain_config(chain_id)['name'],
                'total_usd': chain_total
            }
            portfolio['total_usd'] += chain_total

        except Exception:
            portfolio['chains'][chain_id] = {'name': chain_id, 'total_usd': 0, 'error': True}

    return jsonify(portfolio)


@api_core_bp.route('/api/compare')
def api_compare():
    """API endpoint to compare multiple addresses."""
    addresses = request.args.get('addresses', '').split(',')
    chain = request.args.get('chain', 'ethereum')
    addresses = [a.strip() for a in addresses if is_valid_address(a.strip())]

    if len(addresses) < 2:
        return jsonify({'error': 'Need at least 2 addresses to compare'}), 400

    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        comparison = []

        for address in addresses[:5]:  # Max 5 addresses
            info = client.get_address_info(address)
            comparison.append({
                'address': address,
                'label': info.get('label'),
                'balance': info['balance']['balance'],
                'balance_usd': info.get('balance_usd', 0),
                'total_usd': info.get('total_portfolio_usd', 0),
                'token_count': len(info.get('token_balances', [])),
                'nft_count': len(info.get('nft_holdings', [])),
                'tx_count': info.get('tx_count', 0),
                'risk_score': info.get('risk_score', {}),
                'stats': info.get('stats', {})
            })

        return jsonify(comparison)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_core_bp.route('/api/tx-summary/<chain>/<address>')
def api_tx_summary(chain, address):
    """API endpoint for transaction type summary."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400

    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        transactions = client.get_transactions(address, limit=200)
        summary = get_transaction_summary(transactions)
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_core_bp.route('/api/flow/<chain>/<address>')
def api_flow(chain, address):
    """API endpoint for Sankey flow diagram data."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400

    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        transactions = client.get_transactions(address, limit=100)
        token_transfers = client.get_token_transfers(address, limit=100)

        # Build flow data for Sankey diagram
        nodes = {address.lower(): {'id': address.lower(), 'name': 'This Address'}}
        link_values = {}

        # Process native transactions
        for tx in transactions:
            if tx['value'] > 0:
                source = tx['from'].lower()
                target = tx['to'].lower() if tx['to'] else 'contract'

                # Add nodes
                if source not in nodes:
                    label = get_address_label(source)
                    nodes[source] = {
                        'id': source,
                        'name': label['name'] if label else source[:10] + '...'
                    }
                if target not in nodes:
                    label = get_address_label(target)
                    nodes[target] = {
                        'id': target,
                        'name': label['name'] if label else target[:10] + '...'
                    }

                # Aggregate link values
                link_key = f"{source}->{target}"
                if link_key not in link_values:
                    link_values[link_key] = {'source': source, 'target': target,
                                            'value': 0, 'token': 'ETH'}
                link_values[link_key]['value'] += tx['value']

        # Process token transfers
        for tx in token_transfers:
            if tx['value'] > 0:
                source = tx['from'].lower()
                target = tx['to'].lower()

                if source not in nodes:
                    label = get_address_label(source)
                    nodes[source] = {
                        'id': source,
                        'name': label['name'] if label else source[:10] + '...'
                    }
                if target not in nodes:
                    label = get_address_label(target)
                    nodes[target] = {
                        'id': target,
                        'name': label['name'] if label else target[:10] + '...'
                    }

        links = list(link_values.values())

        return jsonify({
            'nodes': list(nodes.values()),
            'links': links
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_core_bp.route('/api/contract/<chain>/<address>')
def api_contract(chain, address):
    """Get contract source code and details."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        contract_info = client.get_contract_info(address)

        if contract_info:
            return jsonify(contract_info)
        return jsonify({'error': 'Contract not found or not verified'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
