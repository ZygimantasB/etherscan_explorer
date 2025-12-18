"""
Advanced API routes for Crypto Explorer.
Handles whale tracking, flash loans, snipers, security, copy trading, tax, etc.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, Response
from config import get_chain_config
from services.blockchain import BlockchainClient
from services.whale_tracker import (detect_whale_transactions, analyze_whale_patterns,
                                    get_whale_alerts, classify_whale_activity)
from services.flash_loans import detect_flash_loans, detect_arbitrage, get_flash_loan_summary
from services.token_sniper import (detect_early_buyers, detect_sniper_patterns,
                                   analyze_token_launch_buys, get_sniper_summary)
from services.security_scanner import (scan_contract_security, check_honeypot_indicators,
                                       generate_security_report)
from services.copy_trading import (analyze_wallet_performance, generate_copy_signals,
                                   calculate_copy_score, generate_copy_trading_report)
from services.tax_report import generate_tax_report, export_to_csv
from services.funding_flow import generate_flow_report
from services.liquidity_tracker import generate_lp_report
from services.governance import generate_governance_report
from services.wallet_profiler import generate_wallet_profile
from utils import is_valid_address

api_advanced_bp = Blueprint('api_advanced', __name__)


@api_advanced_bp.route('/api/whale-tracker/<chain>/<address>')
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


@api_advanced_bp.route('/api/flash-loans/<chain>/<address>')
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


@api_advanced_bp.route('/api/sniper-detection/<chain>/<address>')
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


@api_advanced_bp.route('/api/security-scan/<chain>/<address>')
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


@api_advanced_bp.route('/api/copy-trading/<chain>/<address>')
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


@api_advanced_bp.route('/api/tax-report/<chain>/<address>')
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


@api_advanced_bp.route('/api/tax-report/<chain>/<address>/export')
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
            headers={'Content-Disposition':
                    f'attachment; filename=tax_report_{address[:10]}_{year or "all"}.csv'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_advanced_bp.route('/api/funding-flow/<chain>/<address>')
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


@api_advanced_bp.route('/api/liquidity-pools/<chain>/<address>')
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


@api_advanced_bp.route('/api/governance/<chain>/<address>')
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


@api_advanced_bp.route('/api/wallet-profile/<chain>/<address>')
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


@api_advanced_bp.route('/api/token-transfers/<chain>/<address>')
def api_token_transfers(chain, address):
    """Get ERC-20 token transfers for an address."""
    if not is_valid_address(address):
        return jsonify({'error': 'Invalid address'}), 400
    if not get_chain_config(chain):
        return jsonify({'error': 'Invalid chain'}), 400

    try:
        client = BlockchainClient(chain)
        # get_token_transfers already returns formatted data with token_name, token_symbol, etc.
        token_transfers = client.get_token_transfers(address, limit=100)

        # Use the already formatted data from the service
        formatted_transfers = []
        for tx in token_transfers[:50]:  # Limit to 50 for modal
            # Convert timestamp to readable format
            timestamp = tx.get('timestamp', 0)
            if timestamp:
                try:
                    date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
                except Exception:
                    date_str = ''
            else:
                date_str = ''

            formatted_transfers.append({
                'hash': tx.get('hash', ''),
                'from': tx.get('from', ''),
                'to': tx.get('to', ''),
                'value': tx.get('value', 0),  # Already formatted by the service
                'token_name': tx.get('token_name', 'Unknown Token'),
                'token_symbol': tx.get('token_symbol', '???'),
                'contract_address': tx.get('contract_address', ''),
                'timestamp': date_str,
                'direction': tx.get('direction', 'out')
            })

        # Summary stats - group by token
        tokens_sent = {}
        tokens_received = {}
        token_names = {}  # Store token names for display

        for tx in formatted_transfers:
            symbol = tx['token_symbol']
            name = tx['token_name']
            token_names[symbol] = name

            if tx['direction'] == 'out':
                tokens_sent[symbol] = tokens_sent.get(symbol, 0) + tx['value']
            else:
                tokens_received[symbol] = tokens_received.get(symbol, 0) + tx['value']

        return jsonify({
            'transfers': formatted_transfers,
            'total_transfers': len(token_transfers),
            'tokens_sent': [{'symbol': k, 'name': token_names.get(k, ''), 'amount': v}
                          for k, v in sorted(tokens_sent.items(), key=lambda x: -x[1])],
            'tokens_received': [{'symbol': k, 'name': token_names.get(k, ''), 'amount': v}
                               for k, v in sorted(tokens_received.items(), key=lambda x: -x[1])],
            'unique_tokens': len(set(tx['token_symbol'] for tx in formatted_transfers)),
            'token_names': token_names
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
