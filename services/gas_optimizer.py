# Gas Optimizer Service
# Analyze historical gas patterns and suggest optimal times

from collections import defaultdict
from datetime import datetime


def analyze_gas_history(transactions):
    """
    Analyze historical gas usage patterns from user's transactions.
    """
    hourly_gas = defaultdict(list)
    daily_gas = defaultdict(list)

    for tx in transactions:
        timestamp = tx.get('timestamp', 0)
        gas_price = tx.get('gas_price_gwei', 0)

        if timestamp and gas_price > 0:
            dt = datetime.fromtimestamp(timestamp)
            hourly_gas[dt.hour].append(gas_price)
            daily_gas[dt.strftime('%A')].append(gas_price)  # Day name

    # Calculate averages
    hourly_avg = {}
    for hour, prices in hourly_gas.items():
        hourly_avg[hour] = {
            'avg': sum(prices) / len(prices),
            'min': min(prices),
            'max': max(prices),
            'count': len(prices)
        }

    daily_avg = {}
    for day, prices in daily_gas.items():
        daily_avg[day] = {
            'avg': sum(prices) / len(prices),
            'min': min(prices),
            'max': max(prices),
            'count': len(prices)
        }

    return {
        'hourly': hourly_avg,
        'daily': daily_avg
    }


def get_optimal_times(gas_history):
    """
    Determine optimal times for transactions based on historical data.
    """
    hourly = gas_history.get('hourly', {})
    daily = gas_history.get('daily', {})

    # Find lowest gas hours
    if hourly:
        sorted_hours = sorted(hourly.items(), key=lambda x: x[1]['avg'])
        best_hours = sorted_hours[:3]
        worst_hours = sorted_hours[-3:]
    else:
        best_hours = []
        worst_hours = []

    # Find lowest gas days
    if daily:
        sorted_days = sorted(daily.items(), key=lambda x: x[1]['avg'])
        best_days = sorted_days[:2]
        worst_days = sorted_days[-2:]
    else:
        best_days = []
        worst_days = []

    return {
        'best_hours': [{'hour': h, **data} for h, data in best_hours],
        'worst_hours': [{'hour': h, **data} for h, data in worst_hours],
        'best_days': [{'day': d, **data} for d, data in best_days],
        'worst_days': [{'day': d, **data} for d, data in worst_days]
    }


def get_gas_recommendations():
    """
    Get general gas optimization recommendations.
    """
    return [
        {
            'tip': 'Transaction timing',
            'description': 'Gas prices are typically lowest during weekends and late night/early morning UTC',
            'savings': 'Up to 50%'
        },
        {
            'tip': 'Use gas tokens',
            'description': 'Mint CHI or GST2 tokens when gas is low, burn when high',
            'savings': 'Up to 42%'
        },
        {
            'tip': 'Batch transactions',
            'description': 'Use multicall contracts to batch multiple operations',
            'savings': '20-40%'
        },
        {
            'tip': 'Set custom gas',
            'description': 'Use "slow" gas settings for non-urgent transactions',
            'savings': '10-30%'
        },
        {
            'tip': 'L2 solutions',
            'description': 'Use Arbitrum, Optimism, or Base for much lower fees',
            'savings': '90-99%'
        },
        {
            'tip': 'Token approvals',
            'description': 'Approve exact amounts instead of unlimited to save gas on future revokes',
            'savings': 'Future savings'
        }
    ]


def calculate_gas_savings(transactions):
    """
    Calculate potential gas savings if user had transacted at optimal times.
    """
    if not transactions:
        return None

    total_gas_spent = 0
    optimal_gas_estimate = 0

    for tx in transactions:
        gas_used = tx.get('gas_used', 0)
        gas_price = tx.get('gas_price_gwei', 0)

        if gas_used and gas_price:
            total_gas_spent += gas_used * gas_price
            # Estimate optimal would be 70% of actual (conservative)
            optimal_gas_estimate += gas_used * gas_price * 0.7

    if total_gas_spent > 0:
        potential_savings = total_gas_spent - optimal_gas_estimate
        savings_percentage = (potential_savings / total_gas_spent) * 100

        return {
            'total_spent_gwei': total_gas_spent,
            'total_spent_eth': total_gas_spent / 1e9,
            'potential_savings_gwei': potential_savings,
            'potential_savings_eth': potential_savings / 1e9,
            'savings_percentage': round(savings_percentage, 1)
        }

    return None


def get_gas_summary(gas_history, transactions):
    """
    Generate comprehensive gas analysis summary.
    """
    optimal_times = get_optimal_times(gas_history)
    savings = calculate_gas_savings(transactions)
    recommendations = get_gas_recommendations()

    # Calculate average gas price
    gas_prices = [tx.get('gas_price_gwei', 0) for tx in transactions if tx.get('gas_price_gwei', 0) > 0]
    avg_gas = sum(gas_prices) / len(gas_prices) if gas_prices else 0

    return {
        'average_gas_price': round(avg_gas, 2),
        'total_transactions': len(transactions),
        'optimal_times': optimal_times,
        'potential_savings': savings,
        'recommendations': recommendations[:3],  # Top 3 recommendations
        'tip_of_day': recommendations[0] if recommendations else None
    }
