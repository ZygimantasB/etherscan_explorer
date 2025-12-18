# Tax Report Generator Service
# Generate tax-ready reports for crypto transactions

from datetime import datetime
from collections import defaultdict
import csv
import io

# Tax event types
TAX_EVENTS = {
    'buy': 'Acquisition',
    'sell': 'Disposal',
    'transfer_in': 'Transfer In',
    'transfer_out': 'Transfer Out',
    'swap': 'Exchange/Swap',
    'airdrop': 'Income - Airdrop',
    'staking_reward': 'Income - Staking',
    'mining_reward': 'Income - Mining',
    'gift_received': 'Gift Received',
    'gift_sent': 'Gift Sent',
    'lost': 'Lost/Stolen',
    'fee': 'Transaction Fee'
}

# Cost basis methods
COST_BASIS_METHODS = {
    'fifo': 'First In, First Out',
    'lifo': 'Last In, First Out',
    'hifo': 'Highest In, First Out',
    'average': 'Average Cost'
}


def generate_tax_events(transactions, token_transfers, address, native_symbol='ETH'):
    """
    Generate tax events from transaction history.
    """
    tax_events = []
    address_lower = address.lower()

    # Process native token transactions
    for tx in transactions:
        value = tx.get('value', 0)
        if value == 0:
            continue

        event = {
            'timestamp': tx.get('timestamp'),
            'date': datetime.fromtimestamp(tx.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M:%S'),
            'tx_hash': tx.get('hash'),
            'asset': native_symbol,
            'amount': value,
            'type': 'sell' if tx.get('direction') == 'out' else 'buy',
            'counterparty': tx.get('to') if tx.get('direction') == 'out' else tx.get('from'),
            'fee_amount': tx.get('gas_fee', 0),
            'fee_asset': native_symbol,
            'value_usd': tx.get('value_usd', 0),
            'fee_usd': tx.get('gas_fee_usd', 0)
        }

        tax_events.append(event)

    # Process token transfers
    for transfer in token_transfers:
        event = {
            'timestamp': transfer.get('timestamp'),
            'date': datetime.fromtimestamp(transfer.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M:%S'),
            'tx_hash': transfer.get('hash'),
            'asset': transfer.get('token_symbol', 'UNKNOWN'),
            'amount': transfer.get('value', 0),
            'type': 'sell' if transfer.get('direction') == 'out' else 'buy',
            'counterparty': transfer.get('to') if transfer.get('direction') == 'out' else transfer.get('from'),
            'contract_address': transfer.get('contract_address'),
            'value_usd': transfer.get('value_usd', 0),
            'fee_amount': 0,
            'fee_asset': native_symbol,
            'fee_usd': 0
        }

        # Detect airdrops (received from unknown source with no corresponding payment)
        if transfer.get('direction') == 'in':
            from_addr = transfer.get('from', '').lower()
            # Could check if this looks like an airdrop based on patterns
            # For now, keep as regular buy

        tax_events.append(event)

    # Sort by timestamp
    tax_events.sort(key=lambda x: x.get('timestamp', 0))

    return tax_events


def calculate_gains_fifo(tax_events, address):
    """
    Calculate capital gains using FIFO method.
    """
    # Track cost basis for each asset
    holdings = defaultdict(list)  # asset -> list of {amount, cost_per_unit, timestamp}
    gains = []

    for event in tax_events:
        asset = event.get('asset', 'UNKNOWN')
        amount = event.get('amount', 0)
        value_usd = event.get('value_usd', 0)
        event_type = event.get('type')

        if amount <= 0:
            continue

        cost_per_unit = value_usd / amount if amount > 0 else 0

        if event_type == 'buy':
            # Add to holdings
            holdings[asset].append({
                'amount': amount,
                'cost_per_unit': cost_per_unit,
                'timestamp': event.get('timestamp'),
                'tx_hash': event.get('tx_hash')
            })

        elif event_type == 'sell':
            # Calculate gain using FIFO
            remaining_to_sell = amount
            total_cost_basis = 0
            lots_used = []

            while remaining_to_sell > 0 and holdings[asset]:
                lot = holdings[asset][0]

                if lot['amount'] <= remaining_to_sell:
                    # Use entire lot
                    total_cost_basis += lot['amount'] * lot['cost_per_unit']
                    remaining_to_sell -= lot['amount']
                    lots_used.append(lot)
                    holdings[asset].pop(0)
                else:
                    # Use partial lot
                    total_cost_basis += remaining_to_sell * lot['cost_per_unit']
                    lot['amount'] -= remaining_to_sell
                    lots_used.append({**lot, 'amount': remaining_to_sell})
                    remaining_to_sell = 0

            proceeds = value_usd
            gain = proceeds - total_cost_basis

            # Determine if short-term or long-term
            hold_period = 'unknown'
            if lots_used:
                earliest_buy = min(l.get('timestamp', 0) for l in lots_used)
                sell_time = event.get('timestamp', 0)
                hold_days = (sell_time - earliest_buy) / 86400 if earliest_buy else 0

                if hold_days > 365:
                    hold_period = 'long_term'
                else:
                    hold_period = 'short_term'

            gains.append({
                'date': event.get('date'),
                'asset': asset,
                'amount_sold': amount,
                'proceeds': proceeds,
                'cost_basis': total_cost_basis,
                'gain_loss': gain,
                'hold_period': hold_period,
                'tx_hash': event.get('tx_hash')
            })

    return gains


def calculate_income_events(tax_events):
    """
    Calculate taxable income events (airdrops, staking rewards, etc.).
    """
    income_events = []

    for event in tax_events:
        event_type = event.get('type')

        # Airdrops, staking rewards, etc. are taxable income
        if event_type in ['airdrop', 'staking_reward', 'mining_reward']:
            income_events.append({
                'date': event.get('date'),
                'type': TAX_EVENTS.get(event_type, event_type),
                'asset': event.get('asset'),
                'amount': event.get('amount'),
                'fair_market_value': event.get('value_usd', 0),
                'tx_hash': event.get('tx_hash')
            })

    return income_events


def generate_tax_summary(gains, income_events, tax_events):
    """
    Generate tax summary for the year.
    """
    summary = {
        'total_transactions': len(tax_events),
        'total_disposals': len(gains),
        'short_term_gains': 0,
        'short_term_losses': 0,
        'long_term_gains': 0,
        'long_term_losses': 0,
        'net_short_term': 0,
        'net_long_term': 0,
        'total_income': 0,
        'total_fees': 0,
        'assets_traded': set()
    }

    for gain in gains:
        gain_loss = gain.get('gain_loss', 0)
        hold_period = gain.get('hold_period', 'short_term')
        summary['assets_traded'].add(gain.get('asset'))

        if hold_period == 'long_term':
            if gain_loss >= 0:
                summary['long_term_gains'] += gain_loss
            else:
                summary['long_term_losses'] += abs(gain_loss)
        else:
            if gain_loss >= 0:
                summary['short_term_gains'] += gain_loss
            else:
                summary['short_term_losses'] += abs(gain_loss)

    summary['net_short_term'] = summary['short_term_gains'] - summary['short_term_losses']
    summary['net_long_term'] = summary['long_term_gains'] - summary['long_term_losses']

    # Calculate income
    for income in income_events:
        summary['total_income'] += income.get('fair_market_value', 0)

    # Calculate fees
    for event in tax_events:
        summary['total_fees'] += event.get('fee_usd', 0)

    summary['assets_traded'] = list(summary['assets_traded'])

    return summary


def export_to_csv(gains, format_type='generic'):
    """
    Export gains to CSV format compatible with tax software.
    """
    output = io.StringIO()

    if format_type == 'generic':
        fieldnames = [
            'Date Sold', 'Asset', 'Amount', 'Proceeds (USD)',
            'Cost Basis (USD)', 'Gain/Loss (USD)', 'Hold Period', 'TX Hash'
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for gain in gains:
            writer.writerow({
                'Date Sold': gain.get('date'),
                'Asset': gain.get('asset'),
                'Amount': gain.get('amount_sold'),
                'Proceeds (USD)': f"{gain.get('proceeds', 0):.2f}",
                'Cost Basis (USD)': f"{gain.get('cost_basis', 0):.2f}",
                'Gain/Loss (USD)': f"{gain.get('gain_loss', 0):.2f}",
                'Hold Period': gain.get('hold_period', 'Unknown'),
                'TX Hash': gain.get('tx_hash')
            })

    elif format_type == 'turbotax':
        # TurboTax compatible format
        fieldnames = [
            'Description', 'Date Acquired', 'Date Sold',
            'Proceeds', 'Cost Basis', 'Adjustment Code', 'Adjustment Amount',
            'Gain or Loss'
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for gain in gains:
            writer.writerow({
                'Description': f"{gain.get('amount_sold')} {gain.get('asset')}",
                'Date Acquired': 'Various',
                'Date Sold': gain.get('date'),
                'Proceeds': f"{gain.get('proceeds', 0):.2f}",
                'Cost Basis': f"{gain.get('cost_basis', 0):.2f}",
                'Adjustment Code': '',
                'Adjustment Amount': '',
                'Gain or Loss': f"{gain.get('gain_loss', 0):.2f}"
            })

    elif format_type == 'koinly':
        # Koinly compatible format
        fieldnames = [
            'Date', 'Sent Amount', 'Sent Currency', 'Received Amount',
            'Received Currency', 'Fee Amount', 'Fee Currency',
            'Net Worth Amount', 'Net Worth Currency', 'Label', 'TxHash'
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        # Would need different logic for Koinly format

    return output.getvalue()


def generate_tax_report(address, transactions, token_transfers, year=None, native_symbol='ETH'):
    """
    Generate comprehensive tax report.
    """
    # Generate tax events
    tax_events = generate_tax_events(transactions, token_transfers, address, native_symbol)

    # Filter by year if specified
    if year:
        year_start = datetime(year, 1, 1).timestamp()
        year_end = datetime(year, 12, 31, 23, 59, 59).timestamp()
        tax_events = [e for e in tax_events if year_start <= e.get('timestamp', 0) <= year_end]

    # Calculate gains
    gains = calculate_gains_fifo(tax_events, address)

    # Calculate income
    income_events = calculate_income_events(tax_events)

    # Generate summary
    summary = generate_tax_summary(gains, income_events, tax_events)

    return {
        'address': address,
        'year': year or 'All Time',
        'tax_events': tax_events,
        'capital_gains': gains,
        'income_events': income_events,
        'summary': summary,
        'method': 'FIFO'
    }
