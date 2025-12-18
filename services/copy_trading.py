# Copy Trading Signals Service
# Track profitable wallets and generate trading signals

from collections import defaultdict
from datetime import datetime, timedelta

# Categories of wallets worth following
WALLET_CATEGORIES = {
    'whale': 'Large holder with significant market impact',
    'smart_money': 'Consistently profitable trader',
    'degen': 'High-risk, high-reward trader',
    'accumulator': 'Long-term holder, buys dips',
    'influencer': 'Known crypto influencer wallet'
}


def analyze_wallet_performance(transactions, token_transfers, address):
    """
    Analyze wallet trading performance.
    """
    performance = {
        'total_trades': 0,
        'profitable_trades': 0,
        'loss_trades': 0,
        'total_profit_usd': 0,
        'total_loss_usd': 0,
        'win_rate': 0,
        'average_hold_time': 0,
        'best_trade': None,
        'worst_trade': None,
        'tokens_traded': set(),
        'active_days': 0
    }

    # Group transfers by token
    token_positions = defaultdict(lambda: {
        'buys': [],
        'sells': [],
        'total_bought': 0,
        'total_sold': 0,
        'avg_buy_price': 0,
        'avg_sell_price': 0,
        'realized_pnl': 0
    })

    for transfer in token_transfers:
        symbol = transfer.get('token_symbol', 'UNKNOWN')
        value = transfer.get('value', 0)
        value_usd = transfer.get('value_usd', 0)
        timestamp = transfer.get('timestamp', 0)
        direction = transfer.get('direction')

        performance['tokens_traded'].add(symbol)

        if direction == 'in':
            token_positions[symbol]['buys'].append({
                'value': value,
                'value_usd': value_usd,
                'timestamp': timestamp
            })
            token_positions[symbol]['total_bought'] += value
        else:
            token_positions[symbol]['sells'].append({
                'value': value,
                'value_usd': value_usd,
                'timestamp': timestamp
            })
            token_positions[symbol]['total_sold'] += value

    # Calculate PnL for each token
    for symbol, data in token_positions.items():
        buys = data['buys']
        sells = data['sells']

        if not buys or not sells:
            continue

        performance['total_trades'] += 1

        # Simple PnL calculation (total sold value - total bought value)
        total_bought_usd = sum(b.get('value_usd', 0) for b in buys)
        total_sold_usd = sum(s.get('value_usd', 0) for s in sells)

        pnl = total_sold_usd - total_bought_usd
        data['realized_pnl'] = pnl

        if pnl > 0:
            performance['profitable_trades'] += 1
            performance['total_profit_usd'] += pnl

            if not performance['best_trade'] or pnl > performance['best_trade']['pnl']:
                performance['best_trade'] = {'token': symbol, 'pnl': pnl}
        else:
            performance['loss_trades'] += 1
            performance['total_loss_usd'] += abs(pnl)

            if not performance['worst_trade'] or pnl < performance['worst_trade']['pnl']:
                performance['worst_trade'] = {'token': symbol, 'pnl': pnl}

        # Calculate hold time
        if buys and sells:
            first_buy = min(b['timestamp'] for b in buys)
            last_sell = max(s['timestamp'] for s in sells)
            hold_time = last_sell - first_buy
            performance['average_hold_time'] += hold_time

    # Calculate averages
    if performance['total_trades'] > 0:
        performance['win_rate'] = (performance['profitable_trades'] / performance['total_trades']) * 100
        performance['average_hold_time'] //= performance['total_trades']

    # Count active days
    tx_dates = set()
    for tx in transactions:
        ts = tx.get('timestamp', 0)
        if ts:
            tx_dates.add(datetime.fromtimestamp(ts).date())
    performance['active_days'] = len(tx_dates)

    # Convert set to count
    performance['tokens_traded'] = len(performance['tokens_traded'])

    return performance


def generate_copy_signals(token_transfers, address):
    """
    Generate copy trading signals from recent activity.
    """
    signals = []

    # Get recent buys (last 7 days worth)
    recent_threshold = datetime.now().timestamp() - (7 * 24 * 3600)

    recent_buys = [
        t for t in token_transfers
        if t.get('direction') == 'in' and t.get('timestamp', 0) > recent_threshold
    ]

    for buy in recent_buys:
        signal = {
            'type': 'BUY',
            'token_symbol': buy.get('token_symbol'),
            'token_name': buy.get('token_name'),
            'token_contract': buy.get('contract_address'),
            'amount': buy.get('value', 0),
            'value_usd': buy.get('value_usd', 0),
            'timestamp': buy.get('timestamp'),
            'tx_hash': buy.get('hash'),
            'confidence': 'medium'
        }

        # Higher confidence for larger buys
        if signal['value_usd'] and signal['value_usd'] > 10000:
            signal['confidence'] = 'high'
        elif signal['value_usd'] and signal['value_usd'] < 1000:
            signal['confidence'] = 'low'

        signals.append(signal)

    # Get recent sells
    recent_sells = [
        t for t in token_transfers
        if t.get('direction') == 'out' and t.get('timestamp', 0) > recent_threshold
    ]

    for sell in recent_sells:
        signal = {
            'type': 'SELL',
            'token_symbol': sell.get('token_symbol'),
            'token_name': sell.get('token_name'),
            'token_contract': sell.get('contract_address'),
            'amount': sell.get('value', 0),
            'value_usd': sell.get('value_usd', 0),
            'timestamp': sell.get('timestamp'),
            'tx_hash': sell.get('hash'),
            'confidence': 'medium'
        }
        signals.append(signal)

    # Sort by timestamp (newest first)
    signals.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

    return signals[:50]  # Return latest 50 signals


def calculate_copy_score(performance):
    """
    Calculate how worthy a wallet is to copy.
    """
    score = 0
    reasons = []

    # Win rate contribution (max 40 points)
    win_rate = performance.get('win_rate', 0)
    if win_rate >= 70:
        score += 40
        reasons.append(f"Excellent win rate: {win_rate:.1f}%")
    elif win_rate >= 50:
        score += 25
        reasons.append(f"Good win rate: {win_rate:.1f}%")
    elif win_rate >= 30:
        score += 10
        reasons.append(f"Moderate win rate: {win_rate:.1f}%")

    # Profitability contribution (max 30 points)
    net_profit = performance.get('total_profit_usd', 0) - performance.get('total_loss_usd', 0)
    if net_profit > 100000:
        score += 30
        reasons.append(f"High profitability: ${net_profit:,.0f}")
    elif net_profit > 10000:
        score += 20
        reasons.append(f"Good profitability: ${net_profit:,.0f}")
    elif net_profit > 0:
        score += 10
        reasons.append(f"Profitable: ${net_profit:,.0f}")

    # Activity contribution (max 15 points)
    total_trades = performance.get('total_trades', 0)
    if total_trades >= 50:
        score += 15
        reasons.append(f"Very active: {total_trades} trades")
    elif total_trades >= 20:
        score += 10
        reasons.append(f"Active: {total_trades} trades")
    elif total_trades >= 5:
        score += 5
        reasons.append(f"Some activity: {total_trades} trades")

    # Consistency contribution (max 15 points)
    active_days = performance.get('active_days', 0)
    if active_days >= 30:
        score += 15
        reasons.append(f"Consistent: {active_days} active days")
    elif active_days >= 14:
        score += 10
        reasons.append(f"Regular activity: {active_days} days")

    return {
        'score': min(score, 100),
        'reasons': reasons,
        'recommendation': get_copy_recommendation(score)
    }


def get_copy_recommendation(score):
    """
    Get recommendation based on copy score.
    """
    if score >= 80:
        return {
            'level': 'strong',
            'text': 'Strong copy candidate - consistent profitable trading',
            'color': 'success'
        }
    elif score >= 60:
        return {
            'level': 'moderate',
            'text': 'Moderate copy candidate - shows promise but verify signals',
            'color': 'primary'
        }
    elif score >= 40:
        return {
            'level': 'cautious',
            'text': 'Use caution - mixed performance, selective copying only',
            'color': 'warning'
        }
    else:
        return {
            'level': 'avoid',
            'text': 'Not recommended for copying - poor or insufficient track record',
            'color': 'danger'
        }


def get_similar_wallets(performance, known_wallets):
    """
    Find similar wallets based on trading patterns.
    """
    # This would compare trading patterns to find similar successful wallets
    # Placeholder for now
    return []


def generate_copy_trading_report(address, performance, signals, copy_score):
    """
    Generate comprehensive copy trading report.
    """
    return {
        'address': address,
        'performance': performance,
        'recent_signals': signals[:20],
        'copy_score': copy_score,
        'summary': {
            'total_trades': performance.get('total_trades', 0),
            'win_rate': f"{performance.get('win_rate', 0):.1f}%",
            'net_profit': performance.get('total_profit_usd', 0) - performance.get('total_loss_usd', 0),
            'tokens_traded': performance.get('tokens_traded', 0),
            'is_copy_worthy': copy_score.get('score', 0) >= 60
        }
    }
