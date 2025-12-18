# Smart Money Tracker Service
# Track what successful/notable wallets are doing

from collections import defaultdict
from services.labels import get_address_label, KNOWN_ADDRESSES

# Known smart money wallets (successful traders, VCs, influencers)
SMART_MONEY_WALLETS = {
    # Notable traders and whales
    '0x28c6c06298d514db089934071355e5743bf21d60': {'name': 'Binance Hot Wallet', 'type': 'exchange'},
    '0x21a31ee1afc51d94c2efccaa2092ad1028285549': {'name': 'Binance', 'type': 'exchange'},
    '0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503': {'name': 'Binance Reserve', 'type': 'exchange'},

    # VC Wallets
    '0x0716a17fbaee714f1e6ab0f9d59edbc5f09815c0': {'name': 'Jump Trading', 'type': 'vc'},
    '0x9b64203878f24eb0cdf55c8c6fa7d08ba0cf77e5': {'name': 'Paradigm', 'type': 'vc'},
    '0x8103683202aa8da10536036edef04cdd865c225e': {'name': 'a]6z Crypto', 'type': 'vc'},

    # Notable DeFi wallets
    '0x0548f59fee79f8832c299e01dca5c76f034f558e': {'name': 'Tetranode', 'type': 'trader'},
    '0x7a16ff8270133f063aab6c9977183d9e72835428': {'name': 'Hsaka', 'type': 'trader'},

    # Protocol treasuries
    '0x0bc3807ec262cb779b38d65b38f0d402b3f35c6f': {'name': 'Lido Treasury', 'type': 'protocol'},
    '0xbe8e3e3618f7474f8cb1d074a26affef007e98fb': {'name': 'Uniswap Treasury', 'type': 'protocol'},
}


def identify_smart_money_interactions(transactions, token_transfers, address):
    """
    Identify interactions with known smart money addresses.
    """
    address_lower = address.lower()
    interactions = []

    # Check transactions
    for tx in transactions:
        from_addr = tx.get('from', '').lower()
        to_addr = tx.get('to', '').lower()

        counterparty = to_addr if from_addr == address_lower else from_addr

        if counterparty in SMART_MONEY_WALLETS:
            info = SMART_MONEY_WALLETS[counterparty]
            interactions.append({
                'address': counterparty,
                'name': info['name'],
                'type': info['type'],
                'direction': 'to' if to_addr == counterparty else 'from',
                'value': tx.get('value', 0),
                'timestamp': tx.get('timestamp', 0),
                'tx_hash': tx.get('hash', '')
            })

    # Check token transfers
    for transfer in token_transfers:
        from_addr = transfer.get('from', '').lower()
        to_addr = transfer.get('to', '').lower()

        counterparty = to_addr if from_addr == address_lower else from_addr

        if counterparty in SMART_MONEY_WALLETS:
            info = SMART_MONEY_WALLETS[counterparty]
            interactions.append({
                'address': counterparty,
                'name': info['name'],
                'type': info['type'],
                'direction': 'to' if to_addr == counterparty else 'from',
                'token': transfer.get('token_symbol', ''),
                'amount': transfer.get('value', 0),
                'timestamp': transfer.get('timestamp', 0),
                'tx_hash': transfer.get('hash', '')
            })

    # Sort by timestamp
    interactions.sort(key=lambda x: x['timestamp'], reverse=True)

    return interactions


def analyze_copy_trading_potential(token_transfers, address):
    """
    Analyze which tokens smart money bought that this address also bought.
    Useful for identifying copy-trading patterns or shared alpha.
    """
    address_lower = address.lower()

    # Get tokens this address bought
    user_tokens = set()
    for transfer in token_transfers:
        if transfer.get('direction') == 'in':
            user_tokens.add(transfer.get('token_symbol', '').upper())

    # In production, you would:
    # 1. Query recent smart money transactions
    # 2. Compare token holdings
    # 3. Identify overlap

    return {
        'user_token_count': len(user_tokens),
        'tokens': list(user_tokens)
    }


def get_smart_money_summary(interactions):
    """
    Summarize smart money interactions.
    """
    if not interactions:
        return {
            'total_interactions': 0,
            'unique_wallets': 0,
            'by_type': {},
            'most_frequent': None
        }

    by_type = defaultdict(int)
    by_wallet = defaultdict(int)

    for interaction in interactions:
        by_type[interaction['type']] += 1
        by_wallet[interaction['name']] += 1

    most_frequent = max(by_wallet.items(), key=lambda x: x[1]) if by_wallet else None

    return {
        'total_interactions': len(interactions),
        'unique_wallets': len(set(i['address'] for i in interactions)),
        'by_type': dict(by_type),
        'most_frequent': {
            'name': most_frequent[0],
            'count': most_frequent[1]
        } if most_frequent else None
    }


def is_smart_money(address):
    """Check if address is known smart money."""
    return address.lower() in SMART_MONEY_WALLETS


def get_smart_money_type(address):
    """Get the type of smart money wallet."""
    info = SMART_MONEY_WALLETS.get(address.lower())
    return info['type'] if info else None
