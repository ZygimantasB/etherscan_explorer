# Wallet Profiler Service
# Classify wallet behavior and generate comprehensive profile

from collections import defaultdict
from datetime import datetime, timedelta

# Wallet archetypes
WALLET_ARCHETYPES = {
    'whale': {
        'name': 'Whale',
        'description': 'Large holder with significant market impact',
        'icon': 'water',
        'color': 'primary',
        'criteria': ['High balance', 'Large transactions']
    },
    'trader': {
        'name': 'Active Trader',
        'description': 'Frequently buys and sells tokens',
        'icon': 'graph-up-arrow',
        'color': 'success',
        'criteria': ['High tx frequency', 'Many different tokens']
    },
    'hodler': {
        'name': 'Long-term Holder',
        'description': 'Buys and holds with minimal selling',
        'icon': 'safe',
        'color': 'info',
        'criteria': ['Low sell ratio', 'Long hold times']
    },
    'degen': {
        'name': 'DeFi Degen',
        'description': 'Heavy DeFi user, yield farming, high risk tolerance',
        'icon': 'fire',
        'color': 'danger',
        'criteria': ['Many DeFi interactions', 'LP positions', 'New token trades']
    },
    'nft_collector': {
        'name': 'NFT Collector',
        'description': 'Primarily collects and trades NFTs',
        'icon': 'image',
        'color': 'purple',
        'criteria': ['Many NFT holdings', 'NFT marketplace activity']
    },
    'bot': {
        'name': 'Bot/Automated',
        'description': 'Likely automated trading or MEV bot',
        'icon': 'robot',
        'color': 'warning',
        'criteria': ['Very high tx frequency', 'Repetitive patterns']
    },
    'airdrop_farmer': {
        'name': 'Airdrop Farmer',
        'description': 'Interacts with many protocols for potential airdrops',
        'icon': 'gift',
        'color': 'success',
        'criteria': ['Many protocol interactions', 'Small consistent transactions']
    },
    'new_user': {
        'name': 'New User',
        'description': 'Recently created wallet with limited history',
        'icon': 'person-plus',
        'color': 'secondary',
        'criteria': ['Recent first transaction', 'Low tx count']
    },
    'dormant': {
        'name': 'Dormant',
        'description': 'Inactive wallet with no recent activity',
        'icon': 'moon',
        'color': 'secondary',
        'criteria': ['No recent transactions']
    },
    'smart_money': {
        'name': 'Smart Money',
        'description': 'Consistently profitable with good timing',
        'icon': 'lightning',
        'color': 'warning',
        'criteria': ['High win rate', 'Early token entries']
    }
}


def analyze_transaction_patterns(transactions, token_transfers, address):
    """
    Analyze transaction patterns for profiling.
    """
    patterns = {
        'total_txs': len(transactions),
        'total_token_transfers': len(token_transfers),
        'avg_daily_txs': 0,
        'tx_frequency': 'low',
        'unique_tokens_traded': set(),
        'unique_contracts_interacted': set(),
        'buy_count': 0,
        'sell_count': 0,
        'swap_count': 0,
        'contract_calls': 0,
        'simple_transfers': 0,
        'active_hours': defaultdict(int),
        'active_days': defaultdict(int),
        'first_tx_time': None,
        'last_tx_time': None,
        'avg_tx_value': 0,
        'max_tx_value': 0
    }

    if not transactions:
        return patterns

    timestamps = []
    values = []

    for tx in transactions:
        timestamp = tx.get('timestamp', 0)
        if timestamp:
            timestamps.append(timestamp)
            dt = datetime.fromtimestamp(timestamp)
            patterns['active_hours'][dt.hour] += 1
            patterns['active_days'][dt.strftime('%A')] += 1

        value = tx.get('value', 0)
        values.append(value)

        # Count contract calls vs simple transfers
        if tx.get('input', '0x') != '0x':
            patterns['contract_calls'] += 1
        else:
            patterns['simple_transfers'] += 1

        to_addr = tx.get('to', '').lower()
        if to_addr:
            patterns['unique_contracts_interacted'].add(to_addr)

    # Token analysis
    for transfer in token_transfers:
        patterns['unique_tokens_traded'].add(transfer.get('token_symbol', ''))
        if transfer.get('direction') == 'in':
            patterns['buy_count'] += 1
        else:
            patterns['sell_count'] += 1

    if timestamps:
        patterns['first_tx_time'] = min(timestamps)
        patterns['last_tx_time'] = max(timestamps)

        # Calculate daily average
        days_active = (max(timestamps) - min(timestamps)) / 86400
        if days_active > 0:
            patterns['avg_daily_txs'] = len(transactions) / days_active

    if values:
        patterns['avg_tx_value'] = sum(values) / len(values)
        patterns['max_tx_value'] = max(values)

    # Determine tx frequency
    if patterns['avg_daily_txs'] > 50:
        patterns['tx_frequency'] = 'very_high'
    elif patterns['avg_daily_txs'] > 10:
        patterns['tx_frequency'] = 'high'
    elif patterns['avg_daily_txs'] > 1:
        patterns['tx_frequency'] = 'medium'
    else:
        patterns['tx_frequency'] = 'low'

    # Convert sets to counts
    patterns['unique_tokens_traded'] = len(patterns['unique_tokens_traded'])
    patterns['unique_contracts_interacted'] = len(patterns['unique_contracts_interacted'])
    patterns['active_hours'] = dict(patterns['active_hours'])
    patterns['active_days'] = dict(patterns['active_days'])

    return patterns


def classify_wallet(patterns, address_info, defi_summary=None, nft_holdings=None):
    """
    Classify wallet into one or more archetypes.
    """
    archetypes = []
    scores = {}

    total_txs = patterns.get('total_txs', 0)
    tx_frequency = patterns.get('tx_frequency', 'low')
    unique_tokens = patterns.get('unique_tokens_traded', 0)
    contract_calls = patterns.get('contract_calls', 0)
    buy_count = patterns.get('buy_count', 0)
    sell_count = patterns.get('sell_count', 0)
    first_tx = patterns.get('first_tx_time')
    last_tx = patterns.get('last_tx_time')
    portfolio_value = address_info.get('total_portfolio_usd', 0)

    # Calculate days since last activity
    now = datetime.now().timestamp()
    days_inactive = (now - last_tx) / 86400 if last_tx else 999

    # Calculate wallet age in days
    wallet_age = (now - first_tx) / 86400 if first_tx else 0

    # Whale check
    whale_score = 0
    if portfolio_value > 1000000:
        whale_score = 100
    elif portfolio_value > 100000:
        whale_score = 70
    elif portfolio_value > 10000:
        whale_score = 40
    scores['whale'] = whale_score

    # Trader check
    trader_score = 0
    if tx_frequency in ['high', 'very_high']:
        trader_score += 40
    if unique_tokens > 20:
        trader_score += 30
    if buy_count > 50 and sell_count > 50:
        trader_score += 30
    scores['trader'] = min(trader_score, 100)

    # Hodler check
    hodler_score = 0
    if buy_count > 0:
        sell_ratio = sell_count / buy_count if buy_count > 0 else 1
        if sell_ratio < 0.2:
            hodler_score += 50
        elif sell_ratio < 0.5:
            hodler_score += 30
    if wallet_age > 365:
        hodler_score += 30
    if days_inactive > 30 and portfolio_value > 0:
        hodler_score += 20
    scores['hodler'] = min(hodler_score, 100)

    # DeFi Degen check
    degen_score = 0
    if defi_summary:
        protocol_count = defi_summary.get('protocol_count', 0)
        if protocol_count >= 5:
            degen_score += 50
        elif protocol_count >= 2:
            degen_score += 30
        if defi_summary.get('has_liquidity'):
            degen_score += 25
        if defi_summary.get('has_yield'):
            degen_score += 25
    scores['degen'] = min(degen_score, 100)

    # NFT Collector check
    nft_score = 0
    nft_count = len(nft_holdings) if nft_holdings else 0
    if nft_count > 50:
        nft_score = 100
    elif nft_count > 20:
        nft_score = 70
    elif nft_count > 5:
        nft_score = 40
    scores['nft_collector'] = nft_score

    # Bot check
    bot_score = 0
    if tx_frequency == 'very_high':
        bot_score += 40
    if patterns.get('avg_daily_txs', 0) > 100:
        bot_score += 30
    # Check for repetitive timing
    active_hours = patterns.get('active_hours', {})
    if active_hours:
        max_hour_txs = max(active_hours.values())
        total_hour_txs = sum(active_hours.values())
        if max_hour_txs > total_hour_txs * 0.5:  # More than 50% in one hour
            bot_score += 30
    scores['bot'] = min(bot_score, 100)

    # Airdrop Farmer check
    farmer_score = 0
    if patterns.get('unique_contracts_interacted', 0) > 50:
        farmer_score += 40
    if unique_tokens > 30:
        farmer_score += 30
    if patterns.get('avg_tx_value', 0) < 0.1 and total_txs > 100:
        farmer_score += 30
    scores['airdrop_farmer'] = min(farmer_score, 100)

    # New User check
    new_user_score = 0
    if wallet_age < 30:
        new_user_score = 80
    elif wallet_age < 90:
        new_user_score = 50
    if total_txs < 10:
        new_user_score += 20
    scores['new_user'] = min(new_user_score, 100)

    # Dormant check
    dormant_score = 0
    if days_inactive > 180:
        dormant_score = 100
    elif days_inactive > 90:
        dormant_score = 70
    elif days_inactive > 30:
        dormant_score = 40
    scores['dormant'] = dormant_score

    # Smart Money check (simplified - would need P&L data)
    smart_money_score = 0
    if portfolio_value > 10000 and scores['trader'] > 50:
        smart_money_score = 50  # Potential smart money
    scores['smart_money'] = smart_money_score

    # Determine primary and secondary archetypes
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    for archetype, score in sorted_scores:
        if score >= 50:
            archetypes.append({
                'type': archetype,
                'score': score,
                **WALLET_ARCHETYPES[archetype]
            })

    # If no strong classification, default to based on balance
    if not archetypes:
        if portfolio_value > 1000:
            archetypes.append({
                'type': 'hodler',
                'score': 30,
                **WALLET_ARCHETYPES['hodler']
            })
        else:
            archetypes.append({
                'type': 'new_user',
                'score': 30,
                **WALLET_ARCHETYPES['new_user']
            })

    return {
        'primary': archetypes[0] if archetypes else None,
        'secondary': archetypes[1:3] if len(archetypes) > 1 else [],
        'all_scores': scores
    }


def generate_behavior_insights(patterns, classification):
    """
    Generate behavioral insights based on patterns.
    """
    insights = []

    primary = classification.get('primary', {})
    primary_type = primary.get('type', '')

    # Activity pattern insights
    active_hours = patterns.get('active_hours', {})
    if active_hours:
        peak_hour = max(active_hours.items(), key=lambda x: x[1])[0]
        insights.append({
            'category': 'Activity',
            'insight': f"Most active at {peak_hour}:00 UTC",
            'type': 'info'
        })

    active_days = patterns.get('active_days', {})
    if active_days:
        peak_day = max(active_days.items(), key=lambda x: x[1])[0]
        insights.append({
            'category': 'Activity',
            'insight': f"Most active on {peak_day}s",
            'type': 'info'
        })

    # Trading behavior insights
    buy_count = patterns.get('buy_count', 0)
    sell_count = patterns.get('sell_count', 0)

    if buy_count > sell_count * 2:
        insights.append({
            'category': 'Trading',
            'insight': "Accumulation pattern - buys significantly more than sells",
            'type': 'bullish'
        })
    elif sell_count > buy_count * 2:
        insights.append({
            'category': 'Trading',
            'insight': "Distribution pattern - sells significantly more than buys",
            'type': 'bearish'
        })

    # Contract interaction insights
    contract_ratio = patterns.get('contract_calls', 0) / max(patterns.get('total_txs', 1), 1)
    if contract_ratio > 0.8:
        insights.append({
            'category': 'Behavior',
            'insight': "Heavy DeFi/smart contract user (80%+ contract calls)",
            'type': 'info'
        })
    elif contract_ratio < 0.2:
        insights.append({
            'category': 'Behavior',
            'insight': "Primarily simple transfers (minimal DeFi usage)",
            'type': 'info'
        })

    return insights


def generate_wallet_profile(address, address_info, transactions, token_transfers,
                           defi_summary=None, nft_holdings=None):
    """
    Generate comprehensive wallet profile.
    """
    patterns = analyze_transaction_patterns(transactions, token_transfers, address)
    classification = classify_wallet(patterns, address_info, defi_summary, nft_holdings)
    insights = generate_behavior_insights(patterns, classification)

    return {
        'address': address,
        'classification': classification,
        'patterns': patterns,
        'insights': insights,
        'summary': {
            'primary_type': classification.get('primary', {}).get('name', 'Unknown'),
            'total_transactions': patterns.get('total_txs', 0),
            'unique_tokens': patterns.get('unique_tokens_traded', 0),
            'activity_level': patterns.get('tx_frequency', 'low'),
            'portfolio_value': address_info.get('total_portfolio_usd', 0)
        }
    }
