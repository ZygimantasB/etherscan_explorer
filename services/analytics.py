# Analytics Service
# Activity heatmaps, historical data, and statistical analysis

from collections import defaultdict
from datetime import datetime, timedelta
import calendar


def generate_activity_heatmap(transactions, token_transfers=None):
    """
    Generate GitHub-style activity heatmap data.
    Returns activity count by day for the past year.
    """
    # Initialize heatmap with zeros for past 365 days
    today = datetime.now()
    heatmap = {}

    for i in range(365):
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        heatmap[date_str] = 0

    # Count transactions per day
    for tx in transactions:
        timestamp = tx.get('timestamp', 0)
        if timestamp:
            date = datetime.fromtimestamp(timestamp)
            date_str = date.strftime('%Y-%m-%d')
            if date_str in heatmap:
                heatmap[date_str] += 1

    # Add token transfers
    if token_transfers:
        for tx in token_transfers:
            timestamp = tx.get('timestamp', 0)
            if timestamp:
                date = datetime.fromtimestamp(timestamp)
                date_str = date.strftime('%Y-%m-%d')
                if date_str in heatmap:
                    heatmap[date_str] += 1

    # Convert to list format for frontend
    heatmap_list = [
        {'date': date, 'count': count}
        for date, count in sorted(heatmap.items())
    ]

    return heatmap_list


def generate_hourly_activity(transactions):
    """
    Analyze transaction activity by hour of day.
    Useful for detecting bot patterns or optimal trading times.
    """
    hourly = defaultdict(int)

    for tx in transactions:
        timestamp = tx.get('timestamp', 0)
        if timestamp:
            hour = datetime.fromtimestamp(timestamp).hour
            hourly[hour] += 1

    # Fill in missing hours
    result = []
    for hour in range(24):
        result.append({
            'hour': hour,
            'count': hourly.get(hour, 0),
            'label': f"{hour:02d}:00"
        })

    return result


def generate_daily_activity(transactions):
    """
    Analyze transaction activity by day of week.
    """
    daily = defaultdict(int)
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    for tx in transactions:
        timestamp = tx.get('timestamp', 0)
        if timestamp:
            day = datetime.fromtimestamp(timestamp).weekday()
            daily[day] += 1

    result = []
    for day in range(7):
        result.append({
            'day': day,
            'name': day_names[day],
            'count': daily.get(day, 0)
        })

    return result


def calculate_balance_history(transactions, address, decimals=18):
    """
    Calculate historical balance over time from transactions.
    Returns balance snapshots for charting.
    """
    address_lower = address.lower()
    balance_history = []
    running_balance = 0

    # Sort transactions chronologically
    sorted_txs = sorted(transactions, key=lambda x: x.get('timestamp', 0))

    for tx in sorted_txs:
        timestamp = tx.get('timestamp', 0)
        value = tx.get('value', 0)
        from_addr = tx.get('from', '').lower()
        to_addr = tx.get('to', '').lower()
        gas_fee = tx.get('gas_fee', 0)

        if from_addr == address_lower:
            running_balance -= value
            running_balance -= gas_fee  # Deduct gas fee for outgoing
        elif to_addr == address_lower:
            running_balance += value

        if timestamp:
            balance_history.append({
                'timestamp': timestamp,
                'date': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d'),
                'balance': running_balance,
                'tx_hash': tx.get('hash', '')
            })

    return balance_history


def calculate_token_balance_history(token_transfers, address, token_symbol=None):
    """
    Calculate historical token balance over time.
    """
    address_lower = address.lower()
    balances = defaultdict(lambda: {'history': [], 'balance': 0})

    # Sort transfers chronologically
    sorted_transfers = sorted(token_transfers, key=lambda x: x.get('timestamp', 0))

    for transfer in sorted_transfers:
        symbol = transfer.get('token_symbol', 'Unknown')
        if token_symbol and symbol.upper() != token_symbol.upper():
            continue

        timestamp = transfer.get('timestamp', 0)
        value = transfer.get('value', 0)
        direction = transfer.get('direction', '')

        if direction == 'in':
            balances[symbol]['balance'] += value
        else:
            balances[symbol]['balance'] -= value

        if timestamp:
            balances[symbol]['history'].append({
                'timestamp': timestamp,
                'date': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d'),
                'balance': balances[symbol]['balance']
            })

    return dict(balances)


def get_transaction_stats(transactions, address):
    """
    Calculate comprehensive transaction statistics.
    """
    address_lower = address.lower()

    stats = {
        'total_transactions': len(transactions),
        'incoming': 0,
        'outgoing': 0,
        'contract_creations': 0,
        'contract_calls': 0,
        'simple_transfers': 0,
        'failed': 0,
        'total_gas_used': 0,
        'avg_gas_price': 0,
        'total_value_in': 0,
        'total_value_out': 0,
        'unique_addresses': set(),
        'first_tx_date': None,
        'last_tx_date': None,
        'active_days': set(),
        'avg_tx_per_day': 0,
        'max_single_tx_value': 0
    }

    gas_prices = []

    for tx in transactions:
        timestamp = tx.get('timestamp', 0)
        from_addr = tx.get('from', '').lower()
        to_addr = tx.get('to', '').lower()
        value = tx.get('value', 0)

        # Direction
        if from_addr == address_lower:
            stats['outgoing'] += 1
            stats['total_value_out'] += value
            if to_addr:
                stats['unique_addresses'].add(to_addr)
        else:
            stats['incoming'] += 1
            stats['total_value_in'] += value
            stats['unique_addresses'].add(from_addr)

        # Transaction type
        if not to_addr:
            stats['contract_creations'] += 1
        elif tx.get('input', '0x') != '0x':
            stats['contract_calls'] += 1
        else:
            stats['simple_transfers'] += 1

        # Failed
        if tx.get('is_error'):
            stats['failed'] += 1

        # Gas
        stats['total_gas_used'] += tx.get('gas_used', 0)
        gas_price = tx.get('gas_price_gwei', 0)
        if gas_price > 0:
            gas_prices.append(gas_price)

        # Value
        if value > stats['max_single_tx_value']:
            stats['max_single_tx_value'] = value

        # Dates
        if timestamp:
            date = datetime.fromtimestamp(timestamp)
            date_str = date.strftime('%Y-%m-%d')
            stats['active_days'].add(date_str)

            if stats['first_tx_date'] is None or timestamp < stats['first_tx_date']:
                stats['first_tx_date'] = timestamp
            if stats['last_tx_date'] is None or timestamp > stats['last_tx_date']:
                stats['last_tx_date'] = timestamp

    # Calculate averages
    if gas_prices:
        stats['avg_gas_price'] = sum(gas_prices) / len(gas_prices)

    stats['unique_address_count'] = len(stats['unique_addresses'])
    stats['active_day_count'] = len(stats['active_days'])

    if stats['active_day_count'] > 0:
        stats['avg_tx_per_day'] = stats['total_transactions'] / stats['active_day_count']

    # Convert dates to readable format
    if stats['first_tx_date']:
        stats['first_tx_date'] = datetime.fromtimestamp(stats['first_tx_date']).strftime('%Y-%m-%d %H:%M')
    if stats['last_tx_date']:
        stats['last_tx_date'] = datetime.fromtimestamp(stats['last_tx_date']).strftime('%Y-%m-%d %H:%M')

    # Remove sets from output
    del stats['unique_addresses']
    del stats['active_days']

    return stats


def get_token_distribution(token_balances):
    """
    Generate token distribution data for pie chart.
    """
    distribution = []
    total_value = sum(t.get('value_usd', 0) for t in token_balances)

    for token in token_balances:
        value = token.get('value_usd', 0)
        if value > 0:
            distribution.append({
                'symbol': token.get('token_symbol', 'Unknown'),
                'name': token.get('token_name', 'Unknown'),
                'balance': token.get('balance', 0),
                'value_usd': value,
                'percentage': (value / total_value * 100) if total_value > 0 else 0
            })

    # Sort by value
    distribution.sort(key=lambda x: x['value_usd'], reverse=True)

    # Group small holdings into "Other"
    if len(distribution) > 10:
        main = distribution[:9]
        other_value = sum(d['value_usd'] for d in distribution[9:])
        other_pct = sum(d['percentage'] for d in distribution[9:])
        main.append({
            'symbol': 'Other',
            'name': f'{len(distribution) - 9} tokens',
            'balance': 0,
            'value_usd': other_value,
            'percentage': other_pct
        })
        distribution = main

    return distribution


def calculate_monthly_summary(transactions, address):
    """
    Calculate monthly transaction summary.
    """
    address_lower = address.lower()
    monthly = defaultdict(lambda: {
        'in_count': 0,
        'out_count': 0,
        'in_value': 0,
        'out_value': 0,
        'gas_spent': 0
    })

    for tx in transactions:
        timestamp = tx.get('timestamp', 0)
        if not timestamp:
            continue

        month_key = datetime.fromtimestamp(timestamp).strftime('%Y-%m')
        value = tx.get('value', 0)

        if tx.get('from', '').lower() == address_lower:
            monthly[month_key]['out_count'] += 1
            monthly[month_key]['out_value'] += value
            monthly[month_key]['gas_spent'] += tx.get('gas_fee', 0)
        else:
            monthly[month_key]['in_count'] += 1
            monthly[month_key]['in_value'] += value

    # Convert to sorted list
    result = []
    for month, data in sorted(monthly.items()):
        result.append({
            'month': month,
            **data,
            'net_value': data['in_value'] - data['out_value'] - data['gas_spent']
        })

    return result
