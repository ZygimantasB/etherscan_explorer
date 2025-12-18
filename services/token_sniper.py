# Token Sniper Detection Service
# Identify early buyers and potential sniping activity

from datetime import datetime
from collections import defaultdict

# Known DEX router contracts
DEX_ROUTERS = {
    '0x7a250d5630b4cf539739df2c5dacb4c659f2488d': 'Uniswap V2 Router',
    '0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45': 'Uniswap V3 Router',
    '0xe592427a0aece92de3edee1f18e0157c05861564': 'Uniswap V3 Router 2',
    '0xef1c6e67703c7bd7107eed8303fbe6ec2554bf6b': 'Uniswap Universal Router',
    '0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad': 'Uniswap Universal Router 2',
    '0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f': 'SushiSwap Router',
    '0x1111111254fb6c44bac0bed2854e76f90643097d': '1inch Router',
    '0x1111111254eeb25477b68fb85ed929f73a960582': '1inch Router V5',
    '0xdef1c0ded9bec7f1a1670819833240f027b25eff': '0x Exchange Proxy',
    '0x10ed43c718714eb63d5aa57b78b54704e256024e': 'PancakeSwap Router',
    '0x13f4ea83d0bd40e75c8222255bc855a974568dd4': 'PancakeSwap V3 Router',
}

# Sniper bot indicators
SNIPER_INDICATORS = {
    'early_buy': 'Bought within first few blocks of liquidity',
    'high_gas': 'Used very high gas price',
    'private_tx': 'Used private transaction (Flashbots)',
    'repeated_pattern': 'Repeated buying pattern across tokens',
    'quick_sell': 'Sold shortly after buying',
    'mev_protection': 'Used MEV protection service'
}


def detect_early_buyers(token_transfers, transactions, target_token=None):
    """
    Detect early buyers of tokens - potential snipers.
    """
    # Group transfers by token
    token_first_transfers = defaultdict(list)

    for transfer in token_transfers:
        symbol = transfer.get('token_symbol', '')
        contract = transfer.get('contract_address', '').lower()

        if target_token and symbol.upper() != target_token.upper():
            continue

        token_first_transfers[contract].append(transfer)

    early_buys = []

    for contract, transfers in token_first_transfers.items():
        if len(transfers) < 2:
            continue

        # Sort by timestamp
        sorted_transfers = sorted(transfers, key=lambda x: x.get('timestamp', 0))

        # Find first buy (incoming transfer)
        first_buys = [t for t in sorted_transfers[:20] if t.get('direction') == 'in']

        for i, buy in enumerate(first_buys):
            buy_info = {
                'token_symbol': buy.get('token_symbol'),
                'token_name': buy.get('token_name'),
                'contract_address': contract,
                'hash': buy.get('hash'),
                'timestamp': buy.get('timestamp'),
                'value': buy.get('value', 0),
                'position': i + 1,  # Position in early buyers
                'indicators': [],
                'sniper_score': 0
            }

            # Check if in first 5 buyers
            if i < 5:
                buy_info['indicators'].append(f"Top {i + 1} earliest buyer")
                buy_info['sniper_score'] += 30

            # Find matching transaction for gas analysis
            tx_hash = buy.get('hash', '').lower()
            matching_tx = next(
                (tx for tx in transactions if tx.get('hash', '').lower() == tx_hash),
                None
            )

            if matching_tx:
                gas_price = matching_tx.get('gas_price_gwei', 0)

                # Check for high gas (snipers often use high gas)
                if gas_price > 100:
                    buy_info['indicators'].append(SNIPER_INDICATORS['high_gas'])
                    buy_info['sniper_score'] += 25
                elif gas_price > 50:
                    buy_info['sniper_score'] += 10

                # Check if using DEX router
                to_addr = matching_tx.get('to', '').lower()
                if to_addr in DEX_ROUTERS:
                    buy_info['dex_used'] = DEX_ROUTERS[to_addr]

            early_buys.append(buy_info)

    # Sort by sniper score
    early_buys.sort(key=lambda x: x['sniper_score'], reverse=True)

    return early_buys


def detect_sniper_patterns(transactions, token_transfers, address):
    """
    Detect patterns consistent with sniper bot activity.
    """
    address_lower = address.lower()
    patterns = {
        'is_potential_sniper': False,
        'confidence': 0,
        'indicators': [],
        'tokens_sniped': [],
        'quick_flips': [],
        'high_gas_buys': 0,
        'dex_usage': defaultdict(int)
    }

    # Analyze buying patterns
    buys_by_token = defaultdict(list)
    sells_by_token = defaultdict(list)

    for transfer in token_transfers:
        symbol = transfer.get('token_symbol', '')
        if transfer.get('direction') == 'in':
            buys_by_token[symbol].append(transfer)
        else:
            sells_by_token[symbol].append(transfer)

    # Check for quick flips (buy and sell within short time)
    for symbol, buys in buys_by_token.items():
        sells = sells_by_token.get(symbol, [])

        for buy in buys:
            buy_time = buy.get('timestamp', 0)

            for sell in sells:
                sell_time = sell.get('timestamp', 0)
                time_diff = sell_time - buy_time

                # Quick flip: sold within 1 hour
                if 0 < time_diff < 3600:
                    patterns['quick_flips'].append({
                        'token': symbol,
                        'buy_time': buy_time,
                        'sell_time': sell_time,
                        'hold_time_minutes': time_diff // 60
                    })
                    break

    # Check transaction gas prices
    for tx in transactions:
        gas_price = tx.get('gas_price_gwei', 0)
        if gas_price > 100:
            patterns['high_gas_buys'] += 1

        # Track DEX usage
        to_addr = tx.get('to', '').lower()
        if to_addr in DEX_ROUTERS:
            patterns['dex_usage'][DEX_ROUTERS[to_addr]] += 1

    # Calculate sniper confidence
    if len(patterns['quick_flips']) >= 3:
        patterns['indicators'].append(f"{len(patterns['quick_flips'])} quick flips detected")
        patterns['confidence'] += 30

    if patterns['high_gas_buys'] >= 5:
        patterns['indicators'].append(f"{patterns['high_gas_buys']} high gas transactions")
        patterns['confidence'] += 20

    if len(buys_by_token) > 20:
        patterns['indicators'].append(f"Traded {len(buys_by_token)} different tokens")
        patterns['confidence'] += 15

    # Convert dex_usage to regular dict for JSON
    patterns['dex_usage'] = dict(patterns['dex_usage'])

    if patterns['confidence'] >= 40:
        patterns['is_potential_sniper'] = True

    return patterns


def analyze_token_launch_buys(token_transfers, address):
    """
    Analyze if address tends to buy tokens at launch.
    """
    # Group by token contract
    tokens_bought = defaultdict(lambda: {'first_buy': None, 'total_bought': 0, 'total_sold': 0})

    for transfer in token_transfers:
        contract = transfer.get('contract_address', '').lower()
        symbol = transfer.get('token_symbol', '')
        timestamp = transfer.get('timestamp', 0)
        value = transfer.get('value', 0)

        if transfer.get('direction') == 'in':
            tokens_bought[contract]['total_bought'] += value
            if not tokens_bought[contract]['first_buy'] or timestamp < tokens_bought[contract]['first_buy']:
                tokens_bought[contract]['first_buy'] = timestamp
                tokens_bought[contract]['symbol'] = symbol
        else:
            tokens_bought[contract]['total_sold'] += value

    # Analyze patterns
    launch_buyer_score = 0
    total_tokens = len(tokens_bought)
    profitable_flips = 0
    loss_flips = 0

    for contract, data in tokens_bought.items():
        if data['total_sold'] > 0:
            if data['total_sold'] > data['total_bought'] * 0.9:
                # Sold most of position
                profitable_flips += 1

    if total_tokens > 0:
        flip_ratio = profitable_flips / total_tokens
        if flip_ratio > 0.5:
            launch_buyer_score += 30

    return {
        'total_tokens_bought': total_tokens,
        'tokens_fully_sold': profitable_flips,
        'launch_buyer_score': launch_buyer_score,
        'is_launch_buyer': launch_buyer_score >= 30
    }


def get_sniper_summary(early_buys, patterns, launch_analysis):
    """
    Generate summary of sniper detection analysis.
    """
    summary = {
        'is_sniper': patterns.get('is_potential_sniper', False) or launch_analysis.get('is_launch_buyer', False),
        'confidence': patterns.get('confidence', 0),
        'early_buys_detected': len(early_buys),
        'quick_flips': len(patterns.get('quick_flips', [])),
        'high_gas_transactions': patterns.get('high_gas_buys', 0),
        'total_tokens_traded': launch_analysis.get('total_tokens_bought', 0),
        'indicators': patterns.get('indicators', []),
        'risk_assessment': 'low'
    }

    if summary['is_sniper']:
        if summary['confidence'] >= 70:
            summary['risk_assessment'] = 'high'
        elif summary['confidence'] >= 40:
            summary['risk_assessment'] = 'medium'

    return summary
