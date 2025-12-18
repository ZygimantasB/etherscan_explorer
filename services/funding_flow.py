# Funding Flow Visualization Service
# Trace and visualize money movement

from collections import defaultdict
from datetime import datetime

# Flow types
FLOW_TYPES = {
    'direct': 'Direct transfer',
    'exchange': 'Via exchange',
    'mixer': 'Via mixer/tumbler',
    'bridge': 'Cross-chain bridge',
    'defi': 'Via DeFi protocol',
    'unknown': 'Unknown path'
}

# Suspicious patterns
SUSPICIOUS_PATTERNS = {
    'rapid_movement': 'Funds moved quickly through multiple addresses',
    'round_amounts': 'Transfers of round amounts',
    'new_wallet': 'Sent to newly created wallet',
    'known_mixer': 'Interacted with known mixer',
    'layering': 'Multiple hops to obscure origin',
    'structuring': 'Multiple small transactions avoiding thresholds'
}


def trace_funding_sources(transactions, token_transfers, address, depth=3):
    """
    Trace where funds came from.
    """
    address_lower = address.lower()
    sources = []

    # Track direct funding sources
    for tx in transactions:
        if tx.get('direction') == 'in' and tx.get('value', 0) > 0:
            source = {
                'address': tx.get('from'),
                'amount': tx.get('value'),
                'amount_usd': tx.get('value_usd', 0),
                'timestamp': tx.get('timestamp'),
                'tx_hash': tx.get('hash'),
                'type': 'native',
                'depth': 1
            }
            sources.append(source)

    # Track token funding sources
    for transfer in token_transfers:
        if transfer.get('direction') == 'in':
            source = {
                'address': transfer.get('from'),
                'amount': transfer.get('value'),
                'amount_usd': transfer.get('value_usd', 0),
                'token': transfer.get('token_symbol'),
                'timestamp': transfer.get('timestamp'),
                'tx_hash': transfer.get('hash'),
                'type': 'token',
                'depth': 1
            }
            sources.append(source)

    # Sort by amount
    sources.sort(key=lambda x: x.get('amount_usd', 0) or 0, reverse=True)

    return sources


def trace_funding_destinations(transactions, token_transfers, address, depth=3):
    """
    Trace where funds went.
    """
    address_lower = address.lower()
    destinations = []

    # Track direct outflows
    for tx in transactions:
        if tx.get('direction') == 'out' and tx.get('value', 0) > 0:
            dest = {
                'address': tx.get('to'),
                'amount': tx.get('value'),
                'amount_usd': tx.get('value_usd', 0),
                'timestamp': tx.get('timestamp'),
                'tx_hash': tx.get('hash'),
                'type': 'native',
                'depth': 1
            }
            destinations.append(dest)

    # Track token outflows
    for transfer in token_transfers:
        if transfer.get('direction') == 'out':
            dest = {
                'address': transfer.get('to'),
                'amount': transfer.get('value'),
                'amount_usd': transfer.get('value_usd', 0),
                'token': transfer.get('token_symbol'),
                'timestamp': transfer.get('timestamp'),
                'tx_hash': transfer.get('hash'),
                'type': 'token',
                'depth': 1
            }
            destinations.append(dest)

    # Sort by amount
    destinations.sort(key=lambda x: x.get('amount_usd', 0) or 0, reverse=True)

    return destinations


def build_flow_graph(sources, destinations, address):
    """
    Build graph data for visualization.
    """
    nodes = [{
        'id': address.lower(),
        'label': f"{address[:6]}...{address[-4:]}",
        'type': 'target',
        'size': 30
    }]
    edges = []

    seen_addresses = {address.lower()}

    # Add source nodes and edges
    for source in sources[:20]:  # Limit to top 20
        source_addr = source.get('address', '').lower()
        if source_addr and source_addr not in seen_addresses:
            nodes.append({
                'id': source_addr,
                'label': f"{source_addr[:6]}...{source_addr[-4:]}",
                'type': 'source',
                'size': 15
            })
            seen_addresses.add(source_addr)

        if source_addr:
            edges.append({
                'source': source_addr,
                'target': address.lower(),
                'value': source.get('amount_usd', 0) or source.get('amount', 0),
                'label': source.get('token', 'ETH'),
                'type': 'inflow'
            })

    # Add destination nodes and edges
    for dest in destinations[:20]:  # Limit to top 20
        dest_addr = dest.get('address', '').lower()
        if dest_addr and dest_addr not in seen_addresses:
            nodes.append({
                'id': dest_addr,
                'label': f"{dest_addr[:6]}...{dest_addr[-4:]}",
                'type': 'destination',
                'size': 15
            })
            seen_addresses.add(dest_addr)

        if dest_addr:
            edges.append({
                'source': address.lower(),
                'target': dest_addr,
                'value': dest.get('amount_usd', 0) or dest.get('amount', 0),
                'label': dest.get('token', 'ETH'),
                'type': 'outflow'
            })

    return {'nodes': nodes, 'edges': edges}


def detect_suspicious_patterns(sources, destinations, transactions):
    """
    Detect suspicious fund flow patterns.
    """
    patterns = []

    # Check for rapid movement (funds out within 1 hour of funds in)
    inflow_times = {s['timestamp']: s for s in sources if s.get('timestamp')}
    outflow_times = {d['timestamp']: d for d in destinations if d.get('timestamp')}

    for in_time, inflow in inflow_times.items():
        for out_time, outflow in outflow_times.items():
            if 0 < out_time - in_time < 3600:  # Within 1 hour
                patterns.append({
                    'type': 'rapid_movement',
                    'description': SUSPICIOUS_PATTERNS['rapid_movement'],
                    'details': f"Funds moved {(out_time - in_time) // 60} minutes after receipt",
                    'risk': 'medium'
                })
                break
        else:
            continue
        break

    # Check for round amounts
    round_count = 0
    for tx in transactions:
        value = tx.get('value', 0)
        if value > 0 and value == int(value) and value % 1 == 0:
            round_count += 1

    if round_count > len(transactions) * 0.3:  # More than 30% round numbers
        patterns.append({
            'type': 'round_amounts',
            'description': SUSPICIOUS_PATTERNS['round_amounts'],
            'details': f"{round_count} transactions with round amounts",
            'risk': 'low'
        })

    # Check for potential structuring (many transactions just under common thresholds)
    threshold_amounts = [9999, 999, 4999]  # Common reporting thresholds
    threshold_count = 0
    for tx in transactions:
        value_usd = tx.get('value_usd', 0)
        for threshold in threshold_amounts:
            if threshold * 0.9 < value_usd <= threshold:
                threshold_count += 1
                break

    if threshold_count > 3:
        patterns.append({
            'type': 'structuring',
            'description': SUSPICIOUS_PATTERNS['structuring'],
            'details': f"{threshold_count} transactions near common thresholds",
            'risk': 'high'
        })

    return patterns


def analyze_flow_concentration(sources, destinations):
    """
    Analyze concentration of fund flows.
    """
    analysis = {
        'inflow_concentration': {},
        'outflow_concentration': {},
        'top_source': None,
        'top_destination': None
    }

    # Inflow concentration
    source_totals = defaultdict(float)
    for source in sources:
        addr = source.get('address', '').lower()
        amount = source.get('amount_usd', 0) or 0
        source_totals[addr] += amount

    total_inflow = sum(source_totals.values())
    if total_inflow > 0:
        for addr, amount in source_totals.items():
            pct = (amount / total_inflow) * 100
            if pct > 5:  # Only track significant sources
                analysis['inflow_concentration'][addr] = {
                    'amount': amount,
                    'percentage': pct
                }

        top_source = max(source_totals.items(), key=lambda x: x[1], default=(None, 0))
        if top_source[0]:
            analysis['top_source'] = {
                'address': top_source[0],
                'amount': top_source[1],
                'percentage': (top_source[1] / total_inflow) * 100
            }

    # Outflow concentration
    dest_totals = defaultdict(float)
    for dest in destinations:
        addr = dest.get('address', '').lower()
        amount = dest.get('amount_usd', 0) or 0
        dest_totals[addr] += amount

    total_outflow = sum(dest_totals.values())
    if total_outflow > 0:
        for addr, amount in dest_totals.items():
            pct = (amount / total_outflow) * 100
            if pct > 5:
                analysis['outflow_concentration'][addr] = {
                    'amount': amount,
                    'percentage': pct
                }

        top_dest = max(dest_totals.items(), key=lambda x: x[1], default=(None, 0))
        if top_dest[0]:
            analysis['top_destination'] = {
                'address': top_dest[0],
                'amount': top_dest[1],
                'percentage': (top_dest[1] / total_outflow) * 100
            }

    return analysis


def generate_flow_report(address, transactions, token_transfers):
    """
    Generate comprehensive funding flow report.
    """
    sources = trace_funding_sources(transactions, token_transfers, address)
    destinations = trace_funding_destinations(transactions, token_transfers, address)
    graph = build_flow_graph(sources, destinations, address)
    patterns = detect_suspicious_patterns(sources, destinations, transactions)
    concentration = analyze_flow_concentration(sources, destinations)

    total_inflow = sum(s.get('amount_usd', 0) or 0 for s in sources)
    total_outflow = sum(d.get('amount_usd', 0) or 0 for d in destinations)

    return {
        'address': address,
        'sources': sources[:50],
        'destinations': destinations[:50],
        'graph': graph,
        'suspicious_patterns': patterns,
        'concentration': concentration,
        'summary': {
            'total_inflow_usd': total_inflow,
            'total_outflow_usd': total_outflow,
            'net_flow': total_inflow - total_outflow,
            'unique_sources': len(set(s.get('address') for s in sources if s.get('address'))),
            'unique_destinations': len(set(d.get('address') for d in destinations if d.get('address'))),
            'suspicious_pattern_count': len(patterns)
        }
    }
