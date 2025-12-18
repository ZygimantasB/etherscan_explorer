# Liquidity Pool Tracker Service
# Track LP positions across DEXs

from collections import defaultdict

# Known LP token patterns
LP_TOKEN_PATTERNS = [
    'UNI-V2',  # Uniswap V2
    'SLP',      # SushiSwap
    'PCS-LP',   # PancakeSwap
    'CAKE-LP',
    'BPT',      # Balancer
    'G-UNI',    # Gelato Uniswap
    'SUSHI-LP',
    'LP Token',
    'Uniswap V2',
    'Curve.fi',
    'crv',
]

# Known DEX factory contracts
DEX_FACTORIES = {
    '0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f': 'Uniswap V2',
    '0x1f98431c8ad98523631ae4a59f267346ea31f984': 'Uniswap V3',
    '0xc0aee478e3658e2610c5f7a4a2e1777ce9e4f2ac': 'SushiSwap',
    '0xb7926c0430afb07aa7defde6da862ae0bde767bc': 'Balancer V2',
    '0xca143ce32fe78f1f7019d7d551a6402fc5350c73': 'PancakeSwap',
}

# DEX router addresses for detecting LP operations
LP_ROUTERS = {
    '0x7a250d5630b4cf539739df2c5dacb4c659f2488d': 'Uniswap V2 Router',
    '0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f': 'SushiSwap Router',
    '0xba12222222228d8ba445958a75a0704d566bf2c8': 'Balancer Vault',
    '0x10ed43c718714eb63d5aa57b78b54704e256024e': 'PancakeSwap Router',
}

# Function signatures for LP operations
LP_FUNCTION_SIGNATURES = {
    '0xe8e33700': 'addLiquidity',
    '0xf305d719': 'addLiquidityETH',
    '0xbaa2abde': 'removeLiquidity',
    '0x02751cec': 'removeLiquidityETH',
    '0xded9382a': 'removeLiquidityETHWithPermit',
    '0x2195995c': 'removeLiquidityWithPermit',
    '0xaf2979eb': 'removeLiquidityETHSupportingFeeOnTransferTokens',
    '0x5c11d795': 'swapExactTokensForTokensSupportingFeeOnTransferTokens',
}


def detect_lp_tokens(token_balances):
    """
    Detect LP tokens in token balances.
    """
    lp_positions = []

    for token in token_balances:
        symbol = token.get('token_symbol', '').upper()
        name = token.get('token_name', '').upper()

        is_lp = False
        dex = 'Unknown DEX'

        # Check if token name/symbol matches LP patterns
        for pattern in LP_TOKEN_PATTERNS:
            if pattern.upper() in symbol or pattern.upper() in name:
                is_lp = True
                break

        # Identify the DEX
        if 'UNI-V2' in symbol or 'UNISWAP' in name:
            dex = 'Uniswap V2'
            is_lp = True
        elif 'SLP' in symbol or 'SUSHI' in name:
            dex = 'SushiSwap'
            is_lp = True
        elif 'CAKE' in symbol or 'PANCAKE' in name:
            dex = 'PancakeSwap'
            is_lp = True
        elif 'BPT' in symbol or 'BALANCER' in name:
            dex = 'Balancer'
            is_lp = True
        elif 'CRV' in symbol.lower() or 'CURVE' in name:
            dex = 'Curve'
            is_lp = True

        if is_lp:
            # Try to extract pair tokens from name
            pair_tokens = extract_pair_tokens(name, symbol)

            lp_positions.append({
                'token_symbol': symbol,
                'token_name': name,
                'contract_address': token.get('contract_address'),
                'balance': token.get('balance', 0),
                'value_usd': token.get('value_usd', 0),
                'dex': dex,
                'pair_tokens': pair_tokens,
                'type': 'lp_token'
            })

    return lp_positions


def extract_pair_tokens(name, symbol):
    """
    Try to extract the pair tokens from LP token name.
    """
    # Common patterns: "WETH/USDC", "ETH-USDT", "Token0-Token1 LP"
    import re

    # Try various separators
    for sep in ['/', '-', '_']:
        if sep in symbol:
            parts = symbol.split(sep)
            if len(parts) >= 2:
                return [p.strip() for p in parts[:2]]

    # Try to extract from name
    match = re.search(r'(\w+)[/-](\w+)', name)
    if match:
        return [match.group(1), match.group(2)]

    return []


def detect_lp_operations(transactions, token_transfers, address):
    """
    Detect liquidity add/remove operations.
    """
    operations = []

    for tx in transactions:
        to_addr = (tx.get('to') or '').lower()
        input_data = tx.get('input', '0x')

        # Check if interacting with LP router
        if to_addr in LP_ROUTERS:
            func_sig = input_data[:10] if len(input_data) >= 10 else ''

            operation = {
                'tx_hash': tx.get('hash'),
                'timestamp': tx.get('timestamp'),
                'dex': LP_ROUTERS[to_addr],
                'gas_used': tx.get('gas_used'),
                'gas_price': tx.get('gas_price_gwei'),
                'type': 'unknown'
            }

            if func_sig in LP_FUNCTION_SIGNATURES:
                func_name = LP_FUNCTION_SIGNATURES[func_sig]
                if 'add' in func_name.lower():
                    operation['type'] = 'add_liquidity'
                elif 'remove' in func_name.lower():
                    operation['type'] = 'remove_liquidity'
                operation['function'] = func_name

            # Try to find associated token transfers
            tx_hash = tx.get('hash', '').lower()
            related_transfers = [
                t for t in token_transfers
                if t.get('hash', '').lower() == tx_hash
            ]

            operation['tokens_involved'] = [
                {
                    'symbol': t.get('token_symbol'),
                    'amount': t.get('value'),
                    'direction': t.get('direction')
                }
                for t in related_transfers
            ]

            operations.append(operation)

    return operations


def calculate_lp_stats(lp_positions, lp_operations):
    """
    Calculate LP statistics.
    """
    stats = {
        'total_lp_positions': len(lp_positions),
        'total_lp_value_usd': sum(p.get('value_usd', 0) or 0 for p in lp_positions),
        'dexes_used': list(set(p.get('dex') for p in lp_positions)),
        'add_liquidity_count': sum(1 for o in lp_operations if o.get('type') == 'add_liquidity'),
        'remove_liquidity_count': sum(1 for o in lp_operations if o.get('type') == 'remove_liquidity'),
        'unique_pairs': len(lp_positions)
    }

    return stats


def estimate_impermanent_loss(lp_position, current_prices=None):
    """
    Estimate impermanent loss for a position.
    Note: This is a simplified calculation and requires price data.
    """
    # Would need historical price data to calculate properly
    # Placeholder for now
    return {
        'position': lp_position.get('token_symbol'),
        'estimated_il': 0,
        'note': 'Requires historical price data for accurate calculation'
    }


def get_lp_recommendations(lp_positions, lp_operations):
    """
    Generate LP position recommendations.
    """
    recommendations = []

    # Check for concentrated positions
    if len(lp_positions) == 1:
        recommendations.append({
            'type': 'diversification',
            'priority': 'medium',
            'message': 'Consider diversifying LP positions across multiple pairs/DEXs'
        })

    # Check for unused LP tokens (holding but not actively managing)
    if len(lp_positions) > 0 and len(lp_operations) == 0:
        recommendations.append({
            'type': 'management',
            'priority': 'low',
            'message': 'LP tokens detected but no recent operations - consider reviewing positions'
        })

    # General recommendations
    recommendations.append({
        'type': 'general',
        'priority': 'info',
        'message': 'Monitor impermanent loss and rebalance positions as needed'
    })

    return recommendations


def generate_lp_report(address, token_balances, transactions, token_transfers):
    """
    Generate comprehensive LP tracking report.
    """
    lp_positions = detect_lp_tokens(token_balances)
    lp_operations = detect_lp_operations(transactions, token_transfers, address)
    stats = calculate_lp_stats(lp_positions, lp_operations)
    recommendations = get_lp_recommendations(lp_positions, lp_operations)

    return {
        'address': address,
        'positions': lp_positions,
        'operations': lp_operations[:50],  # Limit to recent 50
        'stats': stats,
        'recommendations': recommendations,
        'is_lp_provider': len(lp_positions) > 0 or len(lp_operations) > 0
    }
