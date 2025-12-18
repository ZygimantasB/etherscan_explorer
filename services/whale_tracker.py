# Whale Alert Tracker Service
# Monitor and analyze large transactions

from datetime import datetime

# Whale thresholds by token type (in USD)
WHALE_THRESHOLDS = {
    'ETH': 100000,      # $100k+ ETH transfer
    'WETH': 100000,
    'USDT': 500000,     # $500k+ stablecoins
    'USDC': 500000,
    'DAI': 500000,
    'WBTC': 100000,
    'default': 50000    # $50k+ for other tokens
}

# Known whale wallets
KNOWN_WHALES = {
    '0x28c6c06298d514db089934071355e5743bf21d60': {'name': 'Binance Hot Wallet', 'type': 'exchange'},
    '0x21a31ee1afc51d94c2efccaa2092ad1028285549': {'name': 'Binance Cold Wallet', 'type': 'exchange'},
    '0xdfd5293d8e347dfe59e90efd55b2956a1343963d': {'name': 'Binance Cold Wallet 2', 'type': 'exchange'},
    '0x56eddb7aa87536c09ccc2793473599fd21a8b17f': {'name': 'Bitfinex', 'type': 'exchange'},
    '0x742d35cc6634c0532925a3b844bc9e7595f5b2b0': {'name': 'Bitfinex 2', 'type': 'exchange'},
    '0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0': {'name': 'Kraken', 'type': 'exchange'},
    '0xae2d4617c862309a3d75a0ffb358c7a5009c673f': {'name': 'Kraken 2', 'type': 'exchange'},
    '0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13': {'name': 'Kraken 3', 'type': 'exchange'},
    '0xdc76cd25977e0a5ae17155770273ad58648900d3': {'name': 'Kraken 4', 'type': 'exchange'},
    '0x2faf487a4414fe77e2327f0bf4ae2a264a776ad2': {'name': 'FTX (Defunct)', 'type': 'exchange'},
    '0xc098b2a3aa256d2140208c3de6543aaef5cd3a94': {'name': 'FTX 2 (Defunct)', 'type': 'exchange'},
    '0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503': {'name': 'Binance Staking', 'type': 'staking'},
    '0xf977814e90da44bfa03b6295a0616a897441acec': {'name': 'Binance 8', 'type': 'exchange'},
    '0x8103683202aa8da10536036edef04cdd865c225e': {'name': 'Wintermute', 'type': 'market_maker'},
    '0x0000000000000000000000000000000000000000': {'name': 'Null Address (Burn)', 'type': 'burn'},
    '0x000000000000000000000000000000000000dead': {'name': 'Dead Address (Burn)', 'type': 'burn'},
}


def detect_whale_transactions(transactions, token_transfers, native_price=0):
    """
    Identify whale-sized transactions.
    """
    whale_txs = []

    # Check native token transfers
    for tx in transactions:
        value = tx.get('value', 0)
        value_usd = value * native_price if native_price else 0

        threshold = WHALE_THRESHOLDS.get('ETH', WHALE_THRESHOLDS['default'])

        if value_usd >= threshold:
            whale_info = {
                'type': 'native',
                'hash': tx.get('hash'),
                'from': tx.get('from'),
                'to': tx.get('to'),
                'value': value,
                'value_usd': value_usd,
                'timestamp': tx.get('timestamp'),
                'direction': tx.get('direction'),
                'from_whale': get_whale_info(tx.get('from', '')),
                'to_whale': get_whale_info(tx.get('to', ''))
            }
            whale_txs.append(whale_info)

    # Check token transfers
    for transfer in token_transfers:
        value = transfer.get('value', 0)
        value_usd = transfer.get('value_usd', 0)
        symbol = transfer.get('token_symbol', '').upper()

        threshold = WHALE_THRESHOLDS.get(symbol, WHALE_THRESHOLDS['default'])

        if value_usd >= threshold:
            whale_info = {
                'type': 'token',
                'hash': transfer.get('hash'),
                'token_symbol': symbol,
                'token_name': transfer.get('token_name'),
                'from': transfer.get('from'),
                'to': transfer.get('to'),
                'value': value,
                'value_usd': value_usd,
                'timestamp': transfer.get('timestamp'),
                'direction': transfer.get('direction'),
                'from_whale': get_whale_info(transfer.get('from', '')),
                'to_whale': get_whale_info(transfer.get('to', ''))
            }
            whale_txs.append(whale_info)

    # Sort by value
    whale_txs.sort(key=lambda x: x.get('value_usd', 0), reverse=True)

    return whale_txs


def get_whale_info(address):
    """
    Get known whale information for an address.
    """
    if not address:
        return None
    return KNOWN_WHALES.get(address.lower())


def analyze_whale_patterns(whale_txs, address):
    """
    Analyze patterns in whale transactions.
    """
    address_lower = address.lower()

    analysis = {
        'total_whale_txs': len(whale_txs),
        'total_volume_usd': sum(tx.get('value_usd', 0) for tx in whale_txs),
        'inbound_whale_txs': 0,
        'outbound_whale_txs': 0,
        'inbound_volume_usd': 0,
        'outbound_volume_usd': 0,
        'exchange_interactions': 0,
        'burn_transactions': 0,
        'market_maker_interactions': 0,
        'top_whale_senders': {},
        'top_whale_receivers': {}
    }

    for tx in whale_txs:
        value_usd = tx.get('value_usd', 0)

        if tx.get('direction') == 'in':
            analysis['inbound_whale_txs'] += 1
            analysis['inbound_volume_usd'] += value_usd

            from_addr = tx.get('from', '').lower()
            if from_addr:
                if from_addr not in analysis['top_whale_senders']:
                    analysis['top_whale_senders'][from_addr] = {'count': 0, 'volume': 0}
                analysis['top_whale_senders'][from_addr]['count'] += 1
                analysis['top_whale_senders'][from_addr]['volume'] += value_usd
        else:
            analysis['outbound_whale_txs'] += 1
            analysis['outbound_volume_usd'] += value_usd

            to_addr = tx.get('to', '').lower()
            if to_addr:
                if to_addr not in analysis['top_whale_receivers']:
                    analysis['top_whale_receivers'][to_addr] = {'count': 0, 'volume': 0}
                analysis['top_whale_receivers'][to_addr]['count'] += 1
                analysis['top_whale_receivers'][to_addr]['volume'] += value_usd

        # Check counterparty type
        from_whale = tx.get('from_whale')
        to_whale = tx.get('to_whale')

        for whale in [from_whale, to_whale]:
            if whale:
                if whale['type'] == 'exchange':
                    analysis['exchange_interactions'] += 1
                elif whale['type'] == 'burn':
                    analysis['burn_transactions'] += 1
                elif whale['type'] == 'market_maker':
                    analysis['market_maker_interactions'] += 1

    # Convert top senders/receivers to sorted lists
    analysis['top_whale_senders'] = sorted(
        [{'address': k, **v} for k, v in analysis['top_whale_senders'].items()],
        key=lambda x: x['volume'],
        reverse=True
    )[:10]

    analysis['top_whale_receivers'] = sorted(
        [{'address': k, **v} for k, v in analysis['top_whale_receivers'].items()],
        key=lambda x: x['volume'],
        reverse=True
    )[:10]

    return analysis


def get_whale_alerts(whale_txs):
    """
    Generate alerts for significant whale activity.
    """
    alerts = []

    for tx in whale_txs[:10]:  # Top 10 whale transactions
        value_usd = tx.get('value_usd', 0)

        alert_level = 'info'
        if value_usd >= 10000000:  # $10M+
            alert_level = 'critical'
        elif value_usd >= 1000000:  # $1M+
            alert_level = 'high'
        elif value_usd >= 500000:  # $500k+
            alert_level = 'medium'

        symbol = tx.get('token_symbol', 'ETH')
        direction = 'received' if tx.get('direction') == 'in' else 'sent'

        # Check if counterparty is known
        counterparty = tx.get('to_whale') if tx.get('direction') == 'out' else tx.get('from_whale')
        counterparty_str = f" ({counterparty['name']})" if counterparty else ""

        alerts.append({
            'level': alert_level,
            'message': f"${value_usd:,.0f} {symbol} {direction}{counterparty_str}",
            'timestamp': tx.get('timestamp'),
            'hash': tx.get('hash'),
            'value_usd': value_usd
        })

    return alerts


def classify_whale_activity(analysis):
    """
    Classify the type of whale activity for this address.
    """
    classifications = []

    total_volume = analysis.get('total_volume_usd', 0)
    inbound = analysis.get('inbound_volume_usd', 0)
    outbound = analysis.get('outbound_volume_usd', 0)

    if total_volume == 0:
        return ['No whale activity detected']

    # Net flow analysis
    if inbound > outbound * 2:
        classifications.append('Accumulator (Net Buyer)')
    elif outbound > inbound * 2:
        classifications.append('Distributor (Net Seller)')
    else:
        classifications.append('Active Trader')

    # Exchange interaction
    if analysis.get('exchange_interactions', 0) > 5:
        classifications.append('Heavy Exchange User')

    # Burn activity
    if analysis.get('burn_transactions', 0) > 0:
        classifications.append('Token Burner')

    # Market maker interaction
    if analysis.get('market_maker_interactions', 0) > 3:
        classifications.append('Market Maker Connected')

    return classifications
