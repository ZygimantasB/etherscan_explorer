# Profit/Loss Calculator Service
# Tracks token trades and calculates realized/unrealized P&L

from collections import defaultdict
from services.prices import get_token_price_by_symbol, get_eth_price


def calculate_token_pnl(token_transfers, address):
    """
    Calculate profit/loss for each token based on transfer history.
    Uses FIFO (First In, First Out) cost basis method.
    """
    address_lower = address.lower()
    token_trades = defaultdict(lambda: {
        'symbol': '',
        'name': '',
        'buys': [],
        'sells': [],
        'holdings': [],  # FIFO queue
        'total_bought': 0,
        'total_sold': 0,
        'total_cost': 0,
        'total_proceeds': 0,
        'realized_pnl': 0,
        'current_balance': 0
    })

    # Get current ETH price for estimating values
    eth_price = get_eth_price() or 0

    # Process transfers chronologically
    sorted_transfers = sorted(token_transfers, key=lambda x: x.get('timestamp', 0))

    for transfer in sorted_transfers:
        symbol = transfer.get('token_symbol', 'Unknown')
        token_key = transfer.get('contract_address', '').lower()

        if not token_key:
            continue

        token_data = token_trades[token_key]
        token_data['symbol'] = symbol
        token_data['name'] = transfer.get('token_name', 'Unknown')

        amount = transfer.get('value', 0)
        timestamp = transfer.get('timestamp', 0)
        tx_hash = transfer.get('hash', '')

        # Estimate value at time of transfer (simplified - uses current prices)
        # In production, would use historical price data
        current_price = get_token_price_by_symbol(symbol) or 0

        if transfer.get('direction') == 'in':
            # This is a buy/receive
            cost_basis = amount * current_price if current_price else 0

            token_data['buys'].append({
                'amount': amount,
                'price': current_price,
                'cost': cost_basis,
                'timestamp': timestamp,
                'tx_hash': tx_hash
            })

            # Add to FIFO holdings queue
            token_data['holdings'].append({
                'amount': amount,
                'cost_per_unit': current_price,
                'timestamp': timestamp
            })

            token_data['total_bought'] += amount
            token_data['total_cost'] += cost_basis
            token_data['current_balance'] += amount

        else:
            # This is a sell/send
            proceeds = amount * current_price if current_price else 0
            cost_basis = 0

            # Calculate cost basis using FIFO
            remaining_to_sell = amount
            while remaining_to_sell > 0 and token_data['holdings']:
                holding = token_data['holdings'][0]

                if holding['amount'] <= remaining_to_sell:
                    # Use entire holding
                    cost_basis += holding['amount'] * holding['cost_per_unit']
                    remaining_to_sell -= holding['amount']
                    token_data['holdings'].pop(0)
                else:
                    # Use partial holding
                    cost_basis += remaining_to_sell * holding['cost_per_unit']
                    holding['amount'] -= remaining_to_sell
                    remaining_to_sell = 0

            realized_pnl = proceeds - cost_basis

            token_data['sells'].append({
                'amount': amount,
                'price': current_price,
                'proceeds': proceeds,
                'cost_basis': cost_basis,
                'realized_pnl': realized_pnl,
                'timestamp': timestamp,
                'tx_hash': tx_hash
            })

            token_data['total_sold'] += amount
            token_data['total_proceeds'] += proceeds
            token_data['realized_pnl'] += realized_pnl
            token_data['current_balance'] -= amount

    # Calculate unrealized P&L for remaining holdings
    results = []
    for token_address, data in token_trades.items():
        current_price = get_token_price_by_symbol(data['symbol']) or 0
        current_value = data['current_balance'] * current_price

        # Calculate remaining cost basis
        remaining_cost = sum(h['amount'] * h['cost_per_unit'] for h in data['holdings'])
        unrealized_pnl = current_value - remaining_cost

        results.append({
            'token_address': token_address,
            'symbol': data['symbol'],
            'name': data['name'],
            'total_bought': data['total_bought'],
            'total_sold': data['total_sold'],
            'current_balance': data['current_balance'],
            'total_cost': data['total_cost'],
            'total_proceeds': data['total_proceeds'],
            'realized_pnl': data['realized_pnl'],
            'unrealized_pnl': unrealized_pnl,
            'total_pnl': data['realized_pnl'] + unrealized_pnl,
            'current_price': current_price,
            'current_value': current_value,
            'num_buys': len(data['buys']),
            'num_sells': len(data['sells']),
            'avg_buy_price': data['total_cost'] / data['total_bought'] if data['total_bought'] > 0 else 0,
            'avg_sell_price': data['total_proceeds'] / data['total_sold'] if data['total_sold'] > 0 else 0
        })

    # Sort by total P&L
    results.sort(key=lambda x: x['total_pnl'], reverse=True)

    return results


def get_pnl_summary(pnl_data):
    """Generate summary of all P&L data."""
    summary = {
        'total_realized_pnl': 0,
        'total_unrealized_pnl': 0,
        'total_pnl': 0,
        'winning_tokens': 0,
        'losing_tokens': 0,
        'total_tokens_traded': len(pnl_data),
        'best_trade': None,
        'worst_trade': None,
        'total_volume': 0
    }

    best_pnl = float('-inf')
    worst_pnl = float('inf')

    for token in pnl_data:
        summary['total_realized_pnl'] += token['realized_pnl']
        summary['total_unrealized_pnl'] += token['unrealized_pnl']
        summary['total_pnl'] += token['total_pnl']
        summary['total_volume'] += token['total_cost'] + token['total_proceeds']

        if token['total_pnl'] > 0:
            summary['winning_tokens'] += 1
        elif token['total_pnl'] < 0:
            summary['losing_tokens'] += 1

        if token['total_pnl'] > best_pnl:
            best_pnl = token['total_pnl']
            summary['best_trade'] = {
                'symbol': token['symbol'],
                'pnl': token['total_pnl']
            }

        if token['total_pnl'] < worst_pnl:
            worst_pnl = token['total_pnl']
            summary['worst_trade'] = {
                'symbol': token['symbol'],
                'pnl': token['total_pnl']
            }

    # Calculate win rate
    if summary['total_tokens_traded'] > 0:
        summary['win_rate'] = (summary['winning_tokens'] / summary['total_tokens_traded']) * 100
    else:
        summary['win_rate'] = 0

    return summary


def get_trade_history(token_transfers, address, token_symbol=None):
    """Get detailed trade history for a specific token or all tokens."""
    address_lower = address.lower()
    trades = []

    for transfer in token_transfers:
        if token_symbol and transfer.get('token_symbol', '').upper() != token_symbol.upper():
            continue

        direction = transfer.get('direction', '')
        trade_type = 'Buy' if direction == 'in' else 'Sell'

        trades.append({
            'timestamp': transfer.get('timestamp', 0),
            'type': trade_type,
            'token_symbol': transfer.get('token_symbol', 'Unknown'),
            'token_name': transfer.get('token_name', 'Unknown'),
            'amount': transfer.get('value', 0),
            'counterparty': transfer.get('from') if direction == 'in' else transfer.get('to'),
            'tx_hash': transfer.get('hash', '')
        })

    # Sort by timestamp descending
    trades.sort(key=lambda x: x['timestamp'], reverse=True)

    return trades
