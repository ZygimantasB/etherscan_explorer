"""
Analytics API routes for Crypto Explorer.
Handles approvals, PnL, clustering, MEV, analytics, reputation, etc.
"""

from flask import Blueprint, jsonify
from config import get_chain_config
from services.blockchain import BlockchainClient
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
from utils import is_valid_address

api_analytics_bp = Blueprint('api_analytics', __name__)


@api_analytics_bp.route('/api/approvals/<chain>/<address>')
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


@api_analytics_bp.route('/api/pnl/<chain>/<address>')
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


@api_analytics_bp.route('/api/clustering/<chain>/<address>')
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


@api_analytics_bp.route('/api/mev/<chain>/<address>')
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


@api_analytics_bp.route('/api/analytics/<chain>/<address>')
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


@api_analytics_bp.route('/api/smartmoney/<chain>/<address>')
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


@api_analytics_bp.route('/api/reputation/<chain>/<address>')
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


@api_analytics_bp.route('/api/airdrops/<chain>/<address>')
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
        eligibility = estimate_airdrop_eligibility(transactions, token_transfers,
                                                   defi_summary, address)
        summary = get_airdrop_summary(claimed, eligibility)

        return jsonify({
            'claimed': claimed,
            'potential_eligibility': eligibility,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_analytics_bp.route('/api/gas-optimizer/<chain>/<address>')
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


@api_analytics_bp.route('/api/ens/<chain>/<address>')
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
