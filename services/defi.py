# DeFi position detection service
from services.labels import get_address_label

# Known DeFi protocol contracts
DEFI_PROTOCOLS = {
    # Aave V2
    '0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9': {
        'name': 'Aave V2',
        'type': 'lending',
        'actions': ['deposit', 'withdraw', 'borrow', 'repay']
    },
    # Aave V3
    '0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2': {
        'name': 'Aave V3',
        'type': 'lending',
        'actions': ['supply', 'withdraw', 'borrow', 'repay']
    },
    # Compound V2
    '0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b': {
        'name': 'Compound',
        'type': 'lending',
        'actions': ['mint', 'redeem', 'borrow', 'repay']
    },
    # Uniswap V2
    '0x7a250d5630b4cf539739df2c5dacb4c659f2488d': {
        'name': 'Uniswap V2',
        'type': 'dex',
        'actions': ['swap', 'addLiquidity', 'removeLiquidity']
    },
    # Uniswap V3
    '0xe592427a0aece92de3edee1f18e0157c05861564': {
        'name': 'Uniswap V3',
        'type': 'dex',
        'actions': ['exactInput', 'exactOutput']
    },
    '0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45': {
        'name': 'Uniswap V3 Router 2',
        'type': 'dex',
        'actions': ['exactInput', 'exactOutput', 'multicall']
    },
    # Curve
    '0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7': {
        'name': 'Curve 3pool',
        'type': 'dex',
        'actions': ['exchange', 'add_liquidity', 'remove_liquidity']
    },
    # Lido
    '0xae7ab96520de3a18e5e111b5eaab095312d7fe84': {
        'name': 'Lido stETH',
        'type': 'staking',
        'actions': ['submit']
    },
    # Rocket Pool
    '0xae78736cd615f374d3085123a210448e74fc6393': {
        'name': 'Rocket Pool rETH',
        'type': 'staking',
        'actions': ['deposit', 'burn']
    },
    # MakerDAO
    '0x5ef30b9986345249bc32d8928b7ee64de9435e39': {
        'name': 'MakerDAO CDP Manager',
        'type': 'lending',
        'actions': ['open', 'give', 'frob']
    },
    # Yearn
    '0xa354f35829ae975e850e23e9615b11da1b3dc4de': {
        'name': 'Yearn yvUSDC',
        'type': 'yield',
        'actions': ['deposit', 'withdraw']
    },
    # Convex
    '0xf403c135812408bfbe8713b5a23a04b3d48aae31': {
        'name': 'Convex Booster',
        'type': 'yield',
        'actions': ['deposit', 'withdraw', 'getReward']
    },
    # SushiSwap
    '0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f': {
        'name': 'SushiSwap',
        'type': 'dex',
        'actions': ['swap', 'addLiquidity', 'removeLiquidity']
    },
    # 1inch
    '0x1111111254eeb25477b68fb85ed929f73a960582': {
        'name': '1inch',
        'type': 'aggregator',
        'actions': ['swap', 'uniswapV3Swap']
    },
    # Balancer
    '0xba12222222228d8ba445958a75a0704d566bf2c8': {
        'name': 'Balancer Vault',
        'type': 'dex',
        'actions': ['swap', 'joinPool', 'exitPool']
    },
    # GMX
    '0xabc0e2b5e0a07eb1e3f4b9c51e4c1c9b0c51c9b0': {
        'name': 'GMX',
        'type': 'perps',
        'actions': ['createIncreasePosition', 'createDecreasePosition']
    }
}

# aToken / cToken addresses for detecting lending positions
LENDING_TOKENS = {
    # Aave V2 aTokens
    '0x028171bca77440897b824ca71d1c56cac55b68a3': {'name': 'aDAI', 'protocol': 'Aave V2', 'underlying': 'DAI'},
    '0xbcca60bb61934080951369a648fb03df4f96263c': {'name': 'aUSDC', 'protocol': 'Aave V2', 'underlying': 'USDC'},
    '0x3ed3b47dd13ec9a98b44e6204a523e766b225811': {'name': 'aUSDT', 'protocol': 'Aave V2', 'underlying': 'USDT'},
    '0x030ba81f1c18d280636f32af80b9aad02cf0854e': {'name': 'aWETH', 'protocol': 'Aave V2', 'underlying': 'WETH'},
    '0x9ff58f4ffb29fa2266ab25e75e2a8b3503311656': {'name': 'aWBTC', 'protocol': 'Aave V2', 'underlying': 'WBTC'},

    # Aave V3 aTokens (Ethereum)
    '0x018008bfb33d285247a21d44e50697654f754e63': {'name': 'aEthDAI', 'protocol': 'Aave V3', 'underlying': 'DAI'},
    '0x98c23e9d8f34fefb1b7bd6a91b7ff122f4e16f5c': {'name': 'aEthUSDC', 'protocol': 'Aave V3', 'underlying': 'USDC'},
    '0x23878914efe38d27c4d67ab83ed1b93a74d4086a': {'name': 'aEthUSDT', 'protocol': 'Aave V3', 'underlying': 'USDT'},
    '0x4d5f47fa6a74757f35c14fd3a6ef8e3c9bc514e8': {'name': 'aEthWETH', 'protocol': 'Aave V3', 'underlying': 'WETH'},

    # Compound cTokens
    '0x5d3a536e4d6dbd6114cc1ead35777bab948e3643': {'name': 'cDAI', 'protocol': 'Compound', 'underlying': 'DAI'},
    '0x39aa39c021dfbae8fac545936693ac917d5e7563': {'name': 'cUSDC', 'protocol': 'Compound', 'underlying': 'USDC'},
    '0xf650c3d88d12db855b8bf7d11be6c55a4e07dcc9': {'name': 'cUSDT', 'protocol': 'Compound', 'underlying': 'USDT'},
    '0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5': {'name': 'cETH', 'protocol': 'Compound', 'underlying': 'ETH'},
    '0xccf4429db6322d5c611ee964527d42e5d685dd6a': {'name': 'cWBTC', 'protocol': 'Compound', 'underlying': 'WBTC'},
}

# Liquidity pool token patterns
LP_TOKENS = {
    'Uniswap V2': 'UNI-V2',
    'SushiSwap': 'SLP',
    'Curve': 'Curve',
    'Balancer': 'BPT'
}


def detect_defi_positions(token_balances, transactions=None):
    """
    Detect DeFi positions from token balances and transaction history.
    Returns categorized positions.
    """
    positions = {
        'lending': [],
        'staking': [],
        'liquidity': [],
        'yield': [],
        'total_protocols': set()
    }

    # Check token balances for lending/staking tokens
    for token in token_balances:
        contract = token.get('contract_address', '').lower()
        symbol = token.get('token_symbol', '')

        # Check lending tokens
        if contract in LENDING_TOKENS:
            info = LENDING_TOKENS[contract]
            positions['lending'].append({
                'protocol': info['protocol'],
                'token': info['name'],
                'underlying': info['underlying'],
                'balance': token.get('balance', 0),
                'type': 'supply'
            })
            positions['total_protocols'].add(info['protocol'])

        # Check for staked ETH derivatives
        if symbol.lower() in ['steth', 'reth', 'cbeth', 'wsteth']:
            positions['staking'].append({
                'protocol': 'Liquid Staking',
                'token': symbol,
                'balance': token.get('balance', 0),
                'type': 'staked_eth'
            })
            if symbol.lower() == 'steth':
                positions['total_protocols'].add('Lido')
            elif symbol.lower() == 'reth':
                positions['total_protocols'].add('Rocket Pool')
            elif symbol.lower() == 'cbeth':
                positions['total_protocols'].add('Coinbase')

        # Check for LP tokens
        for protocol, prefix in LP_TOKENS.items():
            if prefix in symbol:
                positions['liquidity'].append({
                    'protocol': protocol,
                    'token': symbol,
                    'balance': token.get('balance', 0),
                    'type': 'lp'
                })
                positions['total_protocols'].add(protocol)

        # Check for yield tokens (yearn, convex, etc.)
        if symbol.startswith('yv') or symbol.startswith('cvx'):
            protocol = 'Yearn' if symbol.startswith('yv') else 'Convex'
            positions['yield'].append({
                'protocol': protocol,
                'token': symbol,
                'balance': token.get('balance', 0),
                'type': 'vault'
            })
            positions['total_protocols'].add(protocol)

    # Analyze transactions for protocol interactions
    if transactions:
        protocol_interactions = {}
        for tx in transactions:
            to_addr = tx.get('to', '').lower()
            if to_addr in DEFI_PROTOCOLS:
                protocol = DEFI_PROTOCOLS[to_addr]['name']
                protocol_interactions[protocol] = protocol_interactions.get(protocol, 0) + 1
                positions['total_protocols'].add(protocol)

        positions['interactions'] = protocol_interactions

    positions['total_protocols'] = list(positions['total_protocols'])
    return positions


def get_protocol_info(address):
    """Get protocol information for a contract address."""
    addr = address.lower()
    if addr in DEFI_PROTOCOLS:
        return DEFI_PROTOCOLS[addr]
    return None


def is_defi_contract(address):
    """Check if an address is a known DeFi contract."""
    addr = address.lower()
    return addr in DEFI_PROTOCOLS or addr in LENDING_TOKENS


def get_defi_summary(positions):
    """Generate a summary of DeFi positions."""
    summary = {
        'has_lending': len(positions.get('lending', [])) > 0,
        'has_staking': len(positions.get('staking', [])) > 0,
        'has_liquidity': len(positions.get('liquidity', [])) > 0,
        'has_yield': len(positions.get('yield', [])) > 0,
        'protocol_count': len(positions.get('total_protocols', [])),
        'protocols': positions.get('total_protocols', [])
    }

    # Calculate estimated values (would need price data for accuracy)
    summary['lending_positions'] = len(positions.get('lending', []))
    summary['staking_positions'] = len(positions.get('staking', []))
    summary['lp_positions'] = len(positions.get('liquidity', []))
    summary['yield_positions'] = len(positions.get('yield', []))

    return summary
