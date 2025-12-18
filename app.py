import re
import csv
import io
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
from config import get_chain_config, get_all_chains
from services.blockchain import BlockchainClient
from services.analyzer import LinkAnalyzer
from services.prices import get_token_prices, get_eth_price, get_gas_prices, get_native_price
from services.labels import get_address_label, search_labels, get_category_addresses
from services.decoder import decode_transaction, get_transaction_summary, categorize_transaction
from services.approvals import get_token_approvals, get_approval_summary
from services.pnl import calculate_token_pnl, get_pnl_summary
from services.clustering import find_related_addresses, analyze_funding_chain, detect_sybil_patterns
from services.mev import detect_mev_exposure, get_mev_summary
from services.analytics import (generate_activity_heatmap, generate_hourly_activity,
                                calculate_balance_history, get_transaction_stats,
                                get_token_distribution, calculate_monthly_summary)
from services.smartmoney import identify_smart_money_interactions, get_smart_money_summary
from services.reputation import calculate_wallet_score, get_wallet_badges
from services.airdrops import check_airdrop_claims, estimate_airdrop_eligibility, get_airdrop_summary
from services.gas_optimizer import analyze_gas_history, get_gas_summary, get_optimal_times
from services.ens import detect_ens_transactions, extract_ens_names_from_transfers, get_ens_summary
from services.whale_tracker import detect_whale_transactions, analyze_whale_patterns, get_whale_alerts, classify_whale_activity
from services.flash_loans import detect_flash_loans, detect_arbitrage, get_flash_loan_summary
from services.token_sniper import detect_early_buyers, detect_sniper_patterns, analyze_token_launch_buys, get_sniper_summary
from services.security_scanner import scan_contract_security, check_honeypot_indicators, generate_security_report
from services.copy_trading import analyze_wallet_performance, generate_copy_signals, calculate_copy_score, generate_copy_trading_report
from services.tax_report import generate_tax_events, calculate_gains_fifo, generate_tax_summary, generate_tax_report, export_to_csv
from services.funding_flow import trace_funding_sources, trace_funding_destinations, build_flow_graph, detect_suspicious_patterns, generate_flow_report
from services.liquidity_tracker import detect_lp_tokens, detect_lp_operations, generate_lp_report
from services.governance import detect_governance_activity, calculate_governance_score, generate_governance_report
from services.wallet_profiler import analyze_transaction_patterns, classify_wallet, generate_wallet_profile

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


@app.route('/api/prices')
def api_prices():
    """API endpoint for token prices."""
    tokens = request.args.get('tokens', 'ethereum').split(',')
    try:
        prices = get_token_prices(tokens)
        return jsonify(prices)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/gas/<chain>')
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


@app.route('/api/decode/<chain>/<tx_hash>')
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


@app.route('/api/labels/search')
def api_search_labels():
    """API endpoint to search labels."""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify({'error': 'Query too short'}), 400

    results = search_labels(query)
    return jsonify(results)


@app.route('/api/labels/category/<category>')
def api_category_labels(category):
    """API endpoint to get addresses by category."""
    addresses = get_category_addresses(category)
    return jsonify([{'address': k, **v} for k, v in addresses.items()])


@app.route('/api/export/<chain>/<address>')
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
            writer.writerow(['Hash', 'Block', 'Timestamp', 'From', 'To', 'Value', 'Gas Used', 'Gas Price (Gwei)', 'Status'])
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
            writer.writerow(['Token Symbol', 'Token Name', 'Balance', 'Contract Address', 'Transfers In', 'Transfers Out'])
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


@app.route('/api/whales/<chain>')
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
            current_block = int(block_hex, 16)
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


@app.route('/api/portfolio')
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


@app.route('/api/compare')
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


@app.route('/api/tx-summary/<chain>/<address>')
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


@app.route('/api/flow/<chain>/<address>')
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
        links = []
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
                    link_values[link_key] = {'source': source, 'target': target, 'value': 0, 'token': 'ETH'}
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


@app.route('/compare')
def compare_page():
    """Address comparison page."""
    chains = get_all_chains()
    return render_template('compare.html', chains=chains)


@app.route('/portfolio')
def portfolio_page():
    """Multi-chain portfolio page."""
    chains = get_all_chains()
    return render_template('portfolio.html', chains=chains)


# ============== NEW ADVANCED API ENDPOINTS ==============

@app.route('/api/approvals/<chain>/<address>')
def api_approvals(chain, address):
    """Get token approvals for an address."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        transactions = client.get_transactions(address, limit=500)
        token_transfers = client.get_token_transfers(address, limit=500)

        approvals = get_token_approvals(token_transfers, transactions)
        summary = get_approval_summary(approvals)

        return jsonify({
            'approvals': approvals,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/pnl/<chain>/<address>')
def api_pnl(chain, address):
    """Get profit/loss analysis for an address."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        token_transfers = client.get_token_transfers(address, limit=1000)

        pnl_data = calculate_token_pnl(token_transfers, address)
        summary = get_pnl_summary(pnl_data)

        return jsonify({
            'tokens': pnl_data[:50],  # Top 50 tokens
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/clustering/<chain>/<address>')
def api_clustering(chain, address):
    """Find related addresses (potential same owner)."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        transactions = client.get_transactions(address, limit=200)
        token_transfers = client.get_token_transfers(address, limit=200)

        related = find_related_addresses(transactions, token_transfers, address)
        funding_chain = analyze_funding_chain(transactions, address)
        sybil = detect_sybil_patterns(transactions, token_transfers, address)

        return jsonify({
            'related_addresses': related,
            'funding_chain': funding_chain,
            'sybil_analysis': sybil
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/mev/<chain>/<address>')
def api_mev(chain, address):
    """Detect MEV exposure for an address."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        transactions = client.get_transactions(address, limit=200)
        token_transfers = client.get_token_transfers(address, limit=200)

        mev_analysis = detect_mev_exposure(transactions, token_transfers, address)
        mev_summary = get_mev_summary(mev_analysis)

        return jsonify({
            'analysis': mev_analysis,
            'summary': mev_summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/<chain>/<address>')
def api_analytics(chain, address):
    """Get comprehensive analytics for an address."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        transactions = client.get_transactions(address, limit=500)
        token_transfers = client.get_token_transfers(address, limit=500)
        token_balances = client.get_token_balances(address)

        heatmap = generate_activity_heatmap(transactions, token_transfers)
        hourly = generate_hourly_activity(transactions)
        balance_history = calculate_balance_history(transactions, address)
        tx_stats = get_transaction_stats(transactions, address)
        distribution = get_token_distribution(token_balances)
        monthly = calculate_monthly_summary(transactions, address)

        return jsonify({
            'heatmap': heatmap,
            'hourly_activity': hourly,
            'balance_history': balance_history,
            'transaction_stats': tx_stats,
            'token_distribution': distribution,
            'monthly_summary': monthly
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/smartmoney/<chain>/<address>')
def api_smartmoney(chain, address):
    """Identify smart money interactions."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        transactions = client.get_transactions(address, limit=200)
        token_transfers = client.get_token_transfers(address, limit=200)

        interactions = identify_smart_money_interactions(transactions, token_transfers, address)
        summary = get_smart_money_summary(interactions)

        return jsonify({
            'interactions': interactions,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reputation/<chain>/<address>')
def api_reputation(chain, address):
    """Get wallet reputation score and badges."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        address_info = client.get_address_info(address)
        transactions = address_info.get('transactions', [])
        token_transfers = address_info.get('token_transfers', [])

        score = calculate_wallet_score(address_info, transactions, token_transfers)
        badges = get_wallet_badges(address_info, transactions, token_transfers)

        return jsonify({
            'score': score,
            'badges': badges
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/airdrops/<chain>/<address>')
def api_airdrops(chain, address):
    """Check airdrop eligibility and claims."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        address_info = client.get_address_info(address)
        transactions = address_info.get('transactions', [])
        token_transfers = address_info.get('token_transfers', [])
        defi_summary = address_info.get('defi_summary', {})

        claimed = check_airdrop_claims(token_transfers, address)
        eligibility = estimate_airdrop_eligibility(transactions, token_transfers, defi_summary, address)
        summary = get_airdrop_summary(claimed, eligibility)

        return jsonify({
            'claimed': claimed,
            'potential_eligibility': eligibility,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/gas-optimizer/<chain>/<address>')
def api_gas_optimizer(chain, address):
    """Get gas optimization analysis."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        transactions = client.get_transactions(address, limit=200)

        gas_history = analyze_gas_history(transactions)
        summary = get_gas_summary(gas_history, transactions)
        optimal = get_optimal_times(gas_history)

        return jsonify({
            'history': gas_history,
            'summary': summary,
            'optimal_times': optimal
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ens/<chain>/<address>')
def api_ens(chain, address):
    """Get ENS activity for an address."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        transactions = client.get_transactions(address, limit=200)
        nft_transfers = client.get_nft_transfers(address, limit=100)

        ens_ops = detect_ens_transactions(transactions)
        ens_tokens = extract_ens_names_from_transfers(nft_transfers)
        summary = get_ens_summary(ens_ops, ens_tokens)

        return jsonify({
            'operations': ens_ops,
            'names': ens_tokens,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/contract/<chain>/<address>')
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


@app.route('/analytics')
def analytics_page():
    """Analytics dashboard page."""
    chains = get_all_chains()
    return render_template('analytics.html', chains=chains)


@app.route('/api/whale-tracker/<chain>/<address>')
def api_whale_tracker(chain, address):
    """Track whale transactions for an address."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        address_info = client.get_address_info(address)
        transactions = address_info.get('transactions', [])
        token_transfers = address_info.get('token_transfers', [])
        native_price = address_info.get('native_price', 0)

        whale_txs = detect_whale_transactions(transactions, token_transfers, native_price)
        analysis = analyze_whale_patterns(whale_txs, address)
        alerts = get_whale_alerts(whale_txs)
        classifications = classify_whale_activity(analysis)

        return jsonify({
            'whale_transactions': whale_txs[:50],
            'analysis': analysis,
            'alerts': alerts,
            'classifications': classifications
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/flash-loans/<chain>/<address>')
def api_flash_loans(chain, address):
    """Detect flash loan and arbitrage activity."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        address_info = client.get_address_info(address)
        transactions = address_info.get('transactions', [])
        token_transfers = address_info.get('token_transfers', [])
        internal_txs = address_info.get('internal_transactions', [])

        flash_loans = detect_flash_loans(transactions, internal_txs)
        arbitrage = detect_arbitrage(transactions, token_transfers)
        summary = get_flash_loan_summary(flash_loans, arbitrage, address)

        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sniper-detection/<chain>/<address>')
def api_sniper_detection(chain, address):
    """Detect token sniping activity."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        address_info = client.get_address_info(address)
        transactions = address_info.get('transactions', [])
        token_transfers = address_info.get('token_transfers', [])

        early_buys = detect_early_buyers(token_transfers, transactions)
        patterns = detect_sniper_patterns(transactions, token_transfers, address)
        launch_analysis = analyze_token_launch_buys(token_transfers, address)
        summary = get_sniper_summary(early_buys, patterns, launch_analysis)

        return jsonify({
            'early_buys': early_buys[:30],
            'patterns': patterns,
            'launch_analysis': launch_analysis,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/security-scan/<chain>/<address>')
def api_security_scan(chain, address):
    """Scan contract for security issues."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        contract_info = client.get_contract_info(address)

        if not contract_info:
            return jsonify({'error': 'Not a contract or not verified'}), 404

        scan_results = scan_contract_security(contract_info)

        # Get token transfers for honeypot check
        token_transfers = client.get_token_transfers(address, limit=100)
        honeypot_check = check_honeypot_indicators(token_transfers, address)

        report = generate_security_report(contract_info, scan_results, honeypot_check)

        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/copy-trading/<chain>/<address>')
def api_copy_trading(chain, address):
    """Get copy trading analysis for a wallet."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        address_info = client.get_address_info(address)
        transactions = address_info.get('transactions', [])
        token_transfers = address_info.get('token_transfers', [])

        performance = analyze_wallet_performance(transactions, token_transfers, address)
        signals = generate_copy_signals(token_transfers, address)
        copy_score = calculate_copy_score(performance)
        report = generate_copy_trading_report(address, performance, signals, copy_score)

        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tax-report/<chain>/<address>')
def api_tax_report(chain, address):
    """Generate tax report for an address."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    year = request.args.get('year', type=int)
    chain_config = get_chain_config(chain)

    try:
        client = BlockchainClient(chain)
        address_info = client.get_address_info(address)
        transactions = address_info.get('transactions', [])
        token_transfers = address_info.get('token_transfers', [])
        native_symbol = chain_config.get('symbol', 'ETH')

        report = generate_tax_report(address, transactions, token_transfers, year, native_symbol)

        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tax-report/<chain>/<address>/export')
def api_tax_export(chain, address):
    """Export tax report as CSV."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    year = request.args.get('year', type=int)
    format_type = request.args.get('format', 'generic')
    chain_config = get_chain_config(chain)

    try:
        client = BlockchainClient(chain)
        address_info = client.get_address_info(address)
        transactions = address_info.get('transactions', [])
        token_transfers = address_info.get('token_transfers', [])
        native_symbol = chain_config.get('symbol', 'ETH')

        report = generate_tax_report(address, transactions, token_transfers, year, native_symbol)
        csv_data = export_to_csv(report.get('capital_gains', []), format_type)

        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=tax_report_{address[:10]}_{year or "all"}.csv'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/funding-flow/<chain>/<address>')
def api_funding_flow(chain, address):
    """Get funding flow analysis."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        address_info = client.get_address_info(address)
        transactions = address_info.get('transactions', [])
        token_transfers = address_info.get('token_transfers', [])

        report = generate_flow_report(address, transactions, token_transfers)

        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/liquidity-pools/<chain>/<address>')
def api_liquidity_pools(chain, address):
    """Get liquidity pool positions and activity."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        address_info = client.get_address_info(address)
        token_balances = address_info.get('token_balances', [])
        transactions = address_info.get('transactions', [])
        token_transfers = address_info.get('token_transfers', [])

        report = generate_lp_report(address, token_balances, transactions, token_transfers)

        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/governance/<chain>/<address>')
def api_governance(chain, address):
    """Get governance participation analysis."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        address_info = client.get_address_info(address)
        transactions = address_info.get('transactions', [])
        token_balances = address_info.get('token_balances', [])

        report = generate_governance_report(address, transactions, token_balances)

        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/wallet-profile/<chain>/<address>')
def api_wallet_profile(chain, address):
    """Get comprehensive wallet profile."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        address_info = client.get_address_info(address)
        transactions = address_info.get('transactions', [])
        token_transfers = address_info.get('token_transfers', [])
        defi_summary = address_info.get('defi_summary', {})
        nft_holdings = address_info.get('nft_holdings', [])

        profile = generate_wallet_profile(
            address, address_info, transactions, token_transfers,
            defi_summary, nft_holdings
        )

        return jsonify(profile)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/token-transfers/<chain>/<address>')
def api_token_transfers(chain, address):
    """Get ERC-20 token transfers for an address."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        token_transfers = client.get_token_transfers(address, limit=100)

        # Format transfers for display
        formatted_transfers = []
        for tx in token_transfers[:50]:  # Limit to 50 for modal
            formatted_transfers.append({
                'hash': tx.get('hash', ''),
                'from': tx.get('from', ''),
                'to': tx.get('to', ''),
                'value': float(tx.get('value', 0)) / (10 ** int(tx.get('tokenDecimal', 18))),
                'token_name': tx.get('tokenName', 'Unknown'),
                'token_symbol': tx.get('tokenSymbol', '???'),
                'contract_address': tx.get('contractAddress', ''),
                'timestamp': tx.get('timeStamp', ''),
                'direction': 'out' if tx.get('from', '').lower() == address.lower() else 'in'
            })

        # Summary stats
        tokens_sent = {}
        tokens_received = {}
        for tx in formatted_transfers:
            symbol = tx['token_symbol']
            if tx['direction'] == 'out':
                tokens_sent[symbol] = tokens_sent.get(symbol, 0) + tx['value']
            else:
                tokens_received[symbol] = tokens_received.get(symbol, 0) + tx['value']

        return jsonify({
            'transfers': formatted_transfers,
            'total_transfers': len(token_transfers),
            'tokens_sent': [{'symbol': k, 'amount': v} for k, v in sorted(tokens_sent.items(), key=lambda x: -x[1])],
            'tokens_received': [{'symbol': k, 'amount': v} for k, v in sorted(tokens_received.items(), key=lambda x: -x[1])],
            'unique_tokens': len(set(tx['token_symbol'] for tx in formatted_transfers))
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/advanced')
def advanced_page():
    """Advanced analytics page."""
    chains = get_all_chains()
    return render_template('advanced.html', chains=chains)


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
    app.run(debug=True, host='0.0.0.0', port=5001)
