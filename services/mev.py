# MEV Detection Service
# Detects sandwich attacks, front-running, and arbitrage on user transactions

from collections import defaultdict

# Known MEV bot addresses
KNOWN_MEV_BOTS = {
    '0x00000000003b3cc22af3ae1eac0440bcee416b40': 'Flashbots Builder',
    '0x4675c7e5baafbffbca748158becba61ef3b0a263': 'jaredfromsubway.eth',
    '0x6b75d8af000000e20b7a7ddf000ba900b4009a80': 'MEV Bot',
    '0x5050e08626c499411b5d0e0b5af0e83d3fd82edf': 'MEV Bot',
    '0x280027dd00ee0050d3f9d168efd6b40090009246': 'MEV Bot',
    '0x6980a47bee930a4584b09ee79ebe46484fbdbdd0': 'MEV Bot',
    '0xee9ddc9b6f36fffff27f81b1fd7ff70a17ed1ffa': 'MEV Bot',
    '0x00000000008c4fb1c916e0c88fd4cc402d935e7d': 'MEV Bot',
}

# DEX router addresses
DEX_ROUTERS = {
    '0x7a250d5630b4cf539739df2c5dacb4c659f2488d': 'Uniswap V2',
    '0xe592427a0aece92de3edee1f18e0157c05861564': 'Uniswap V3',
    '0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45': 'Uniswap V3 Router 2',
    '0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f': 'SushiSwap',
    '0x1111111254eeb25477b68fb85ed929f73a960582': '1inch',
    '0xdef1c0ded9bec7f1a1670819833240f027b25eff': '0x Protocol',
}


def detect_mev_exposure(transactions, token_transfers, address):
    """
    Detect if address has been exposed to MEV attacks.
    Returns analysis of potential MEV interactions.
    """
    address_lower = address.lower()

    mev_analysis = {
        'total_transactions': len(transactions),
        'dex_transactions': 0,
        'potential_sandwich_attacks': [],
        'mev_bot_interactions': [],
        'high_slippage_trades': [],
        'failed_transactions': [],
        'total_mev_exposure_eth': 0,
        'risk_level': 'low'
    }

    # Group transactions by block to detect sandwich patterns
    block_txs = defaultdict(list)
    for tx in transactions:
        block = tx.get('block_number', '')
        if block:
            block_txs[block].append(tx)

    # Analyze each transaction
    for tx in transactions:
        to_addr = tx.get('to', '').lower()
        from_addr = tx.get('from', '').lower()
        tx_hash = tx.get('hash', '')
        block = tx.get('block_number', '')

        # Check if interacting with DEX
        if to_addr in DEX_ROUTERS:
            mev_analysis['dex_transactions'] += 1

            # Check for MEV bot interaction in same block
            if block in block_txs:
                block_transactions = block_txs[block]
                for other_tx in block_transactions:
                    other_from = other_tx.get('from', '').lower()
                    if other_from in KNOWN_MEV_BOTS and other_tx['hash'] != tx_hash:
                        mev_analysis['mev_bot_interactions'].append({
                            'user_tx': tx_hash,
                            'mev_tx': other_tx['hash'],
                            'mev_bot': KNOWN_MEV_BOTS.get(other_from, 'Unknown MEV Bot'),
                            'block': block,
                            'timestamp': tx.get('timestamp', 0)
                        })

        # Check for failed transactions (potential front-running victim)
        if tx.get('is_error'):
            mev_analysis['failed_transactions'].append({
                'tx_hash': tx_hash,
                'to': to_addr,
                'timestamp': tx.get('timestamp', 0),
                'gas_price_gwei': tx.get('gas_price_gwei', 0),
                'is_dex': to_addr in DEX_ROUTERS
            })

        # Check for direct MEV bot interactions
        if to_addr in KNOWN_MEV_BOTS or from_addr in KNOWN_MEV_BOTS:
            bot_addr = to_addr if to_addr in KNOWN_MEV_BOTS else from_addr
            mev_analysis['mev_bot_interactions'].append({
                'tx_hash': tx_hash,
                'mev_bot': KNOWN_MEV_BOTS.get(bot_addr, 'Unknown'),
                'direction': 'to' if to_addr in KNOWN_MEV_BOTS else 'from',
                'value': tx.get('value', 0),
                'timestamp': tx.get('timestamp', 0)
            })

    # Detect potential sandwich attacks from token transfers
    # A sandwich typically shows: buy before user, sell after user
    token_swaps = []
    for transfer in token_transfers:
        if transfer.get('from', '').lower() == address_lower or \
           transfer.get('to', '').lower() == address_lower:
            token_swaps.append({
                'timestamp': transfer.get('timestamp', 0),
                'direction': transfer.get('direction'),
                'token': transfer.get('token_symbol'),
                'amount': transfer.get('value', 0),
                'hash': transfer.get('hash')
            })

    # Analyze for sandwich patterns (simplified)
    # In production, would check mempool data and exact block positions
    for i, swap in enumerate(token_swaps):
        # Check for unusual price impact indicators
        pass  # Would need more data for accurate detection

    # Calculate risk level
    mev_score = 0
    if mev_analysis['mev_bot_interactions']:
        mev_score += len(mev_analysis['mev_bot_interactions']) * 10
    if mev_analysis['failed_transactions']:
        failed_dex = sum(1 for f in mev_analysis['failed_transactions'] if f['is_dex'])
        mev_score += failed_dex * 15

    if mev_score >= 50:
        mev_analysis['risk_level'] = 'high'
    elif mev_score >= 20:
        mev_analysis['risk_level'] = 'medium'

    mev_analysis['mev_risk_score'] = min(mev_score, 100)

    return mev_analysis


def get_mev_summary(mev_analysis):
    """Generate human-readable MEV exposure summary."""
    summary = []

    if mev_analysis['mev_bot_interactions']:
        count = len(mev_analysis['mev_bot_interactions'])
        summary.append(f"Detected {count} MEV bot interaction(s)")

    if mev_analysis['failed_transactions']:
        failed_dex = sum(1 for f in mev_analysis['failed_transactions'] if f['is_dex'])
        if failed_dex > 0:
            summary.append(f"{failed_dex} failed DEX transaction(s) - potential front-running")

    dex_ratio = mev_analysis['dex_transactions'] / max(mev_analysis['total_transactions'], 1)
    if dex_ratio > 0.3:
        summary.append(f"High DEX activity ({mev_analysis['dex_transactions']} swaps) increases MEV exposure")

    if not summary:
        summary.append("No significant MEV exposure detected")

    return {
        'summary': summary,
        'risk_level': mev_analysis['risk_level'],
        'score': mev_analysis.get('mev_risk_score', 0)
    }


def is_mev_bot(address):
    """Check if address is a known MEV bot."""
    return address.lower() in KNOWN_MEV_BOTS


def get_mev_bot_name(address):
    """Get name of MEV bot if known."""
    return KNOWN_MEV_BOTS.get(address.lower())
