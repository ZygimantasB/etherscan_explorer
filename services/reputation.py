# Wallet Reputation/Score Service
# Calculate wallet trustworthiness and activity score

from datetime import datetime
from services.labels import get_address_label


def calculate_wallet_score(address_info, transactions, token_transfers):
    """
    Calculate comprehensive wallet reputation score (0-100).

    Factors:
    - Wallet age
    - Transaction history
    - Token diversity
    - DeFi activity
    - Interaction with known entities
    - Balance
    """
    score = 0
    factors = []
    breakdown = {}

    # 1. Wallet Age (max 20 points)
    stats = address_info.get('stats', {})
    first_tx = stats.get('first_tx_timestamp')
    if first_tx:
        if isinstance(first_tx, str):
            # Already formatted
            age_days = 365  # Assume at least 1 year if formatted
        else:
            age_days = (datetime.now() - datetime.fromtimestamp(first_tx)).days

        age_score = min(age_days / 365 * 10, 20)  # Max 20 points for 2+ years
        score += age_score
        breakdown['age'] = round(age_score, 1)

        if age_days > 730:
            factors.append(f"Mature wallet ({age_days // 365}+ years old)")
        elif age_days > 365:
            factors.append("Established wallet (1+ year)")
        elif age_days > 180:
            factors.append("Developing wallet (6+ months)")
        elif age_days < 30:
            factors.append("New wallet (< 30 days)")

    # 2. Transaction Count (max 15 points)
    tx_count = len(transactions)
    tx_score = min(tx_count / 100 * 15, 15)
    score += tx_score
    breakdown['transactions'] = round(tx_score, 1)

    if tx_count > 500:
        factors.append(f"Highly active ({tx_count}+ transactions)")
    elif tx_count > 100:
        factors.append("Active wallet")

    # 3. Token Diversity (max 10 points)
    unique_tokens = stats.get('unique_tokens_count', 0)
    token_score = min(unique_tokens / 20 * 10, 10)
    score += token_score
    breakdown['token_diversity'] = round(token_score, 1)

    if unique_tokens > 30:
        factors.append(f"Diverse portfolio ({unique_tokens} tokens)")

    # 4. Balance Value (max 15 points)
    total_value = address_info.get('total_portfolio_usd', 0)
    if total_value > 100000:
        balance_score = 15
    elif total_value > 10000:
        balance_score = 12
    elif total_value > 1000:
        balance_score = 8
    elif total_value > 100:
        balance_score = 4
    else:
        balance_score = 1

    score += balance_score
    breakdown['balance'] = balance_score

    if total_value > 100000:
        factors.append("High-value wallet ($100k+)")
    elif total_value > 10000:
        factors.append("Significant holdings ($10k+)")

    # 5. DeFi Activity (max 15 points)
    defi_summary = address_info.get('defi_summary', {})
    protocol_count = defi_summary.get('protocol_count', 0)
    defi_score = min(protocol_count * 3, 15)
    score += defi_score
    breakdown['defi'] = defi_score

    if protocol_count > 5:
        factors.append(f"DeFi power user ({protocol_count} protocols)")
    elif protocol_count > 0:
        factors.append("DeFi active")

    # 6. Interaction Quality (max 15 points)
    quality_score = 0

    # Check for interactions with verified contracts
    for tx in transactions[:50]:  # Check last 50
        to_label = tx.get('to_label')
        if to_label:
            category = to_label.get('category', '')
            if category in ['exchange', 'defi', 'bridge']:
                quality_score += 0.3

    quality_score = min(quality_score, 15)
    score += quality_score
    breakdown['interaction_quality'] = round(quality_score, 1)

    if quality_score > 10:
        factors.append("Interacts with reputable protocols")

    # 7. Risk Factors (negative points)
    risk_score = address_info.get('risk_score', {})
    risk_level = risk_score.get('level', 'minimal')

    if risk_level == 'critical':
        score -= 50
        factors.append("CRITICAL: High-risk associations detected")
    elif risk_level == 'high':
        score -= 30
        factors.append("WARNING: Risky interactions detected")
    elif risk_level == 'medium':
        score -= 10
        factors.append("Caution: Some risk indicators")

    breakdown['risk_penalty'] = -min(50, max(0, 100 - score))

    # 8. Contract interaction ratio (max 10 points)
    outgoing = stats.get('outgoing_txs', 0)
    if outgoing > 0:
        contract_calls = sum(1 for tx in transactions if tx.get('input', '0x') != '0x')
        contract_ratio = contract_calls / outgoing
        contract_score = min(contract_ratio * 10, 10)
        score += contract_score
        breakdown['contract_usage'] = round(contract_score, 1)

        if contract_ratio > 0.7:
            factors.append("Power user (high contract interaction)")

    # Normalize score
    final_score = max(0, min(100, round(score)))

    # Determine tier
    if final_score >= 80:
        tier = 'Excellent'
        tier_color = 'success'
    elif final_score >= 60:
        tier = 'Good'
        tier_color = 'primary'
    elif final_score >= 40:
        tier = 'Average'
        tier_color = 'warning'
    elif final_score >= 20:
        tier = 'Low'
        tier_color = 'danger'
    else:
        tier = 'Very Low'
        tier_color = 'danger'

    return {
        'score': final_score,
        'tier': tier,
        'tier_color': tier_color,
        'factors': factors,
        'breakdown': breakdown
    }


def get_wallet_badges(address_info, transactions, token_transfers):
    """
    Award badges based on wallet characteristics.
    """
    badges = []

    stats = address_info.get('stats', {})
    tx_count = len(transactions)
    token_count = len(address_info.get('token_balances', []))
    nft_count = len(address_info.get('nft_holdings', []))

    # Activity badges
    if tx_count > 1000:
        badges.append({'name': 'Power User', 'icon': 'lightning', 'color': 'warning'})
    elif tx_count > 100:
        badges.append({'name': 'Active', 'icon': 'activity', 'color': 'info'})

    # Holder badges
    if token_count > 50:
        badges.append({'name': 'Token Collector', 'icon': 'collection', 'color': 'primary'})

    if nft_count > 10:
        badges.append({'name': 'NFT Collector', 'icon': 'image', 'color': 'purple'})

    # DeFi badges
    defi = address_info.get('defi_summary', {})
    if defi.get('protocol_count', 0) > 5:
        badges.append({'name': 'DeFi Degen', 'icon': 'bank', 'color': 'success'})

    if defi.get('has_staking'):
        badges.append({'name': 'Staker', 'icon': 'lock', 'color': 'info'})

    if defi.get('has_liquidity'):
        badges.append({'name': 'Liquidity Provider', 'icon': 'droplet', 'color': 'primary'})

    # Value badges
    total_value = address_info.get('total_portfolio_usd', 0)
    if total_value > 1000000:
        badges.append({'name': 'Whale', 'icon': 'water', 'color': 'primary'})
    elif total_value > 100000:
        badges.append({'name': 'Dolphin', 'icon': 'water', 'color': 'info'})

    # Veteran badge
    first_tx = stats.get('first_tx_timestamp')
    if first_tx and not isinstance(first_tx, str):
        age_days = (datetime.now() - datetime.fromtimestamp(first_tx)).days
        if age_days > 1095:  # 3 years
            badges.append({'name': 'OG', 'icon': 'award', 'color': 'warning'})

    return badges
