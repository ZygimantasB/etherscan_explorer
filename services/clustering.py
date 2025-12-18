# Address Clustering Service
# Identifies potentially related addresses using heuristics

from collections import defaultdict
from services.labels import get_address_label


def find_related_addresses(transactions, token_transfers, address):
    """
    Find addresses that are likely related (same owner) using heuristics:
    1. Funded by same address
    2. Funds the same destination
    3. Similar transaction patterns
    4. Interacts with same set of contracts
    """
    address_lower = address.lower()

    # Track relationships
    funded_by = set()
    funds_to = set()
    interacted_contracts = set()
    interaction_times = defaultdict(list)

    for tx in transactions:
        from_addr = tx.get('from', '').lower()
        to_addr = tx.get('to', '').lower()
        timestamp = tx.get('timestamp', 0)
        value = tx.get('value', 0)

        if from_addr == address_lower:
            if to_addr and value > 0:
                funds_to.add(to_addr)
            if to_addr:
                interacted_contracts.add(to_addr)
                interaction_times[to_addr].append(timestamp)
        elif to_addr == address_lower:
            if value > 0:
                funded_by.add(from_addr)

    # Analyze token transfers
    token_counterparties = defaultdict(int)
    for transfer in token_transfers:
        from_addr = transfer.get('from', '').lower()
        to_addr = transfer.get('to', '').lower()

        if from_addr == address_lower:
            token_counterparties[to_addr] += 1
        elif to_addr == address_lower:
            token_counterparties[from_addr] += 1

    # Build cluster candidates
    cluster_candidates = {}

    # Addresses that funded this address (high confidence for funding source)
    for addr in funded_by:
        if addr not in cluster_candidates:
            cluster_candidates[addr] = {
                'address': addr,
                'confidence': 0,
                'reasons': [],
                'label': get_address_label(addr)
            }
        cluster_candidates[addr]['confidence'] += 30
        cluster_candidates[addr]['reasons'].append('Funded this address')

    # Addresses this address funds
    for addr in funds_to:
        if addr not in cluster_candidates:
            cluster_candidates[addr] = {
                'address': addr,
                'confidence': 0,
                'reasons': [],
                'label': get_address_label(addr)
            }
        cluster_candidates[addr]['confidence'] += 20
        cluster_candidates[addr]['reasons'].append('Receives funds from this address')

    # Frequent token transfer counterparties
    for addr, count in token_counterparties.items():
        if count >= 3:  # At least 3 interactions
            if addr not in cluster_candidates:
                cluster_candidates[addr] = {
                    'address': addr,
                    'confidence': 0,
                    'reasons': [],
                    'label': get_address_label(addr)
                }
            cluster_candidates[addr]['confidence'] += min(count * 5, 25)
            cluster_candidates[addr]['reasons'].append(f'Frequent token transfers ({count}x)')

    # Filter out known contracts/exchanges (less likely to be same owner)
    filtered_candidates = []
    for addr, data in cluster_candidates.items():
        label = data['label']
        if label:
            category = label.get('category', '')
            # Lower confidence for known entities
            if category in ['exchange', 'defi', 'bridge', 'nft']:
                data['confidence'] = max(0, data['confidence'] - 40)
                data['reasons'].append(f'Known {category}: {label["name"]}')
            elif category in ['mixer', 'scam']:
                data['confidence'] = 0
                continue

        if data['confidence'] > 0:
            filtered_candidates.append(data)

    # Sort by confidence
    filtered_candidates.sort(key=lambda x: x['confidence'], reverse=True)

    return filtered_candidates[:20]  # Top 20 candidates


def analyze_funding_chain(transactions, address, depth=3):
    """
    Trace the funding chain - who funded who.
    Returns tree of funding relationships.
    """
    address_lower = address.lower()

    funding_chain = {
        'address': address,
        'label': get_address_label(address),
        'funders': [],
        'funded': []
    }

    # Find direct funders and fundees
    for tx in transactions:
        from_addr = tx.get('from', '').lower()
        to_addr = tx.get('to', '').lower()
        value = tx.get('value', 0)

        if value > 0:
            if to_addr == address_lower and from_addr:
                funder_exists = any(f['address'] == from_addr for f in funding_chain['funders'])
                if not funder_exists:
                    funding_chain['funders'].append({
                        'address': from_addr,
                        'label': get_address_label(from_addr),
                        'total_funded': value,
                        'tx_count': 1
                    })
                else:
                    for f in funding_chain['funders']:
                        if f['address'] == from_addr:
                            f['total_funded'] += value
                            f['tx_count'] += 1

            elif from_addr == address_lower and to_addr:
                fundee_exists = any(f['address'] == to_addr for f in funding_chain['funded'])
                if not fundee_exists:
                    funding_chain['funded'].append({
                        'address': to_addr,
                        'label': get_address_label(to_addr),
                        'total_received': value,
                        'tx_count': 1
                    })
                else:
                    for f in funding_chain['funded']:
                        if f['address'] == to_addr:
                            f['total_received'] += value
                            f['tx_count'] += 1

    # Sort by amount
    funding_chain['funders'].sort(key=lambda x: x['total_funded'], reverse=True)
    funding_chain['funded'].sort(key=lambda x: x['total_received'], reverse=True)

    return funding_chain


def detect_sybil_patterns(transactions, token_transfers, address):
    """
    Detect potential sybil attack patterns:
    - Multiple addresses funded from same source
    - Coordinated activity timing
    - Similar transaction patterns
    """
    patterns = {
        'suspected_sybil': False,
        'indicators': [],
        'confidence': 0
    }

    address_lower = address.lower()

    # Check for coordinated funding
    funders = defaultdict(list)
    for tx in transactions:
        if tx.get('to', '').lower() == address_lower and tx.get('value', 0) > 0:
            funder = tx.get('from', '').lower()
            funders[funder].append(tx.get('timestamp', 0))

    # If funded by very few addresses (1-2), might be sybil
    if len(funders) <= 2 and len(transactions) > 10:
        patterns['indicators'].append('Limited funding sources despite high activity')
        patterns['confidence'] += 20

    # Check for regular/automated transaction patterns
    timestamps = [tx.get('timestamp', 0) for tx in transactions]
    if len(timestamps) > 5:
        intervals = [timestamps[i] - timestamps[i+1] for i in range(len(timestamps)-1) if timestamps[i+1] > 0]
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            # Check for very regular intervals (bot-like)
            variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
            if variance < 1000 and avg_interval < 3600:  # Low variance, frequent txs
                patterns['indicators'].append('Regular automated transaction pattern detected')
                patterns['confidence'] += 30

    # Check for airdrop farming patterns
    unique_contracts = set()
    for tx in transactions:
        to_addr = tx.get('to', '')
        if to_addr:
            unique_contracts.add(to_addr.lower())

    # Many unique contract interactions might indicate airdrop farming
    if len(unique_contracts) > 50:
        patterns['indicators'].append(f'High contract diversity ({len(unique_contracts)} contracts)')
        patterns['confidence'] += 15

    patterns['suspected_sybil'] = patterns['confidence'] >= 40

    return patterns
